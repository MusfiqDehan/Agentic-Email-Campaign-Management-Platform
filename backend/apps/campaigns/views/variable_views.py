"""
Variable API Views for Email Template Personalization.

These views provide API endpoints for the frontend to:
- Get list of available variables for autocomplete
- Validate templates for unknown variables
- Extract variables from template content
- Manage organization custom field schema
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.campaigns.utils.variable_registry import (
    get_variable_registry,
    get_variables_for_organization,
    VariableCategory
)


class VariableListView(APIView):
    """
    GET /campaigns/variables/
    
    Returns all available variables for template personalization.
    Used by frontend for autocomplete when user types {{ in the template editor.
    
    Query Parameters:
        - category (optional): Filter by category (contact, campaign, organization, system, custom)
        - grouped (optional): If true, return variables grouped by category
    
    Response:
        {
            "variables": [
                {
                    "name": "first_name",
                    "category": "contact",
                    "description": "Contact's first name",
                    "example": "John",
                    "placeholder": "{{first_name}}"
                },
                ...
            ]
        }
        
        Or if grouped=true:
        {
            "variables": {
                "contact": [...],
                "campaign": [...],
                "system": [...],
                "custom": [...]
            }
        }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get registry with organization's custom fields if available
        if hasattr(user, 'organization') and user.organization:
            registry = get_variables_for_organization(user.organization)
        else:
            registry = get_variable_registry()
        
        # Filter by category if specified
        category_filter = request.query_params.get('category')
        grouped = request.query_params.get('grouped', '').lower() == 'true'
        
        if grouped:
            # Return variables grouped by category
            variables = registry.to_categorized_dict()
            
            # Filter to specific category if requested
            if category_filter:
                variables = {
                    k: v for k, v in variables.items() 
                    if k == category_filter
                }
        else:
            # Return flat list
            if category_filter:
                try:
                    category = VariableCategory(category_filter)
                    variables = [v.to_dict() for v in registry.get_variables_by_category(category)]
                except ValueError:
                    return Response(
                        {"error": f"Invalid category: {category_filter}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                variables = registry.to_list()
        
        return Response({
            "variables": variables,
            "total": len(variables) if isinstance(variables, list) else sum(len(v) for v in variables.values())
        })


class VariableExtractView(APIView):
    """
    POST /campaigns/variables/extract/
    
    Extract all variables used in a template.
    
    Request Body:
        {
            "template": "<html>Hello {{first_name}}, your email is {{email}}</html>"
        }
    
    Response:
        {
            "variables": ["first_name", "email"],
            "count": 2
        }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        template = request.data.get('template', '')
        
        if not template:
            return Response(
                {"error": "Template content is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registry = get_variable_registry()
        variables = registry.extract_variables(template)
        
        return Response({
            "variables": sorted(list(variables)),
            "count": len(variables)
        })


class VariableValidateView(APIView):
    """
    POST /campaigns/variables/validate/
    
    Validate a template and check for unknown or missing required variables.
    
    Request Body:
        {
            "template": "<html>Hello {{first_name}}, {{unknown_var}}</html>"
        }
    
    Response:
        {
            "valid": false,
            "used_variables": [
                {"name": "first_name", "category": "contact", ...}
            ],
            "unknown_variables": ["unknown_var"],
            "missing_required": ["unsubscribe_url"],
            "warnings": ["Template does not include {{unsubscribe_url}}..."]
        }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        template = request.data.get('template', '')
        
        if not template:
            return Response(
                {"error": "Template content is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Get registry with organization's custom fields
        if hasattr(user, 'organization') and user.organization:
            registry = get_variables_for_organization(user.organization)
        else:
            registry = get_variable_registry()
        
        result = registry.validate_template(template)
        
        return Response(result)


class CustomFieldSchemaView(APIView):
    """
    GET/PUT /campaigns/variables/schema/
    
    Manage the organization's custom field schema.
    This defines what custom variables are available for contacts.
    
    GET Response:
        {
            "schema": [
                {"name": "company", "type": "string", "description": "Company name"},
                {"name": "department", "type": "string", "description": "Department"}
            ]
        }
    
    PUT Request Body:
        {
            "schema": [
                {"name": "company", "type": "string", "description": "Company name"},
                {"name": "job_title", "type": "string", "description": "Job title"}
            ]
        }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        organization = getattr(user, 'organization', None)
        
        if not organization:
            return Response(
                {"error": "User is not associated with an organization"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get current schema
        schema = getattr(organization, 'custom_field_schema', []) or []
        
        return Response({
            "schema": schema,
            "organization": organization.name
        })
    
    def put(self, request):
        user = request.user
        organization = getattr(user, 'organization', None)
        
        if not organization:
            return Response(
                {"error": "User is not associated with an organization"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schema = request.data.get('schema', [])
        
        # Validate schema format
        if not isinstance(schema, list):
            return Response(
                {"error": "Schema must be a list of field definitions"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate each field definition
        errors = []
        valid_types = {'string', 'number', 'date', 'boolean', 'url'}
        seen_names = set()
        
        for i, field_def in enumerate(schema):
            if not isinstance(field_def, dict):
                errors.append(f"Field {i}: Must be an object")
                continue
            
            name = field_def.get('name', '')
            if not name:
                errors.append(f"Field {i}: 'name' is required")
            elif not name.isidentifier():
                errors.append(f"Field {i}: 'name' must be a valid identifier (letters, numbers, underscore)")
            elif name in seen_names:
                errors.append(f"Field {i}: Duplicate field name '{name}'")
            else:
                seen_names.add(name)
            
            field_type = field_def.get('type', 'string')
            if field_type not in valid_types:
                errors.append(f"Field {i}: Invalid type '{field_type}'. Must be one of: {', '.join(valid_types)}")
        
        if errors:
            return Response(
                {"error": "Invalid schema", "details": errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update organization's custom field schema
        organization.custom_field_schema = schema
        organization.save(update_fields=['custom_field_schema'])
        
        return Response({
            "message": "Custom field schema updated successfully",
            "schema": schema
        })


class VariablePreviewView(APIView):
    """
    POST /campaigns/variables/preview/
    
    Preview how a template will look with sample data.
    
    Request Body:
        {
            "template": "Hello {{first_name}}, welcome to {{organization_name}}!",
            "sample_data": {
                "first_name": "John",
                "organization_name": "ACME Corp"
            }
        }
    
    Response:
        {
            "rendered": "Hello John, welcome to ACME Corp!",
            "variables_used": ["first_name", "organization_name"]
        }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        template = request.data.get('template', '')
        sample_data = request.data.get('sample_data', {})
        
        if not template:
            return Response(
                {"error": "Template content is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registry = get_variable_registry()
        
        # Use provided sample data, falling back to variable examples
        context = {}
        for var in registry.get_all_variables():
            context[var.name] = var.example
        context.update(sample_data)
        
        # Render the template
        rendered = registry.render_template(template, context)
        variables_used = list(registry.extract_variables(template))
        
        return Response({
            "rendered": rendered,
            "variables_used": variables_used
        })
