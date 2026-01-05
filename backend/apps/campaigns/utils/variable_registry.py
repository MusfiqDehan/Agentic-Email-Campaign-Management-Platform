"""
Centralized Variable Registry for Email Template Personalization.

This module provides a single source of truth for all available variables
that can be used in email templates. It supports:
- System variables (always available)
- Contact variables (from Contact model fields)
- Custom field variables (from Organization's custom_field_schema)
- Campaign variables (from Campaign context)

Variables use the {{variable_name}} format (Mustache-like, no spaces).
"""
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class VariableCategory(str, Enum):
    """Categories for organizing variables."""
    CONTACT = "contact"
    CAMPAIGN = "campaign"
    ORGANIZATION = "organization"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class Variable:
    """Represents a template variable with metadata."""
    name: str
    category: VariableCategory
    description: str
    example: str = ""
    required: bool = False
    data_type: str = "string"  # string, number, date, boolean, url
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "example": self.example,
            "required": self.required,
            "data_type": self.data_type,
            "placeholder": "{{" + self.name + "}}"
        }


class VariableRegistry:
    """
    Central registry for all available template variables.
    
    Usage:
        registry = VariableRegistry()
        
        # Get all available variables
        all_vars = registry.get_all_variables()
        
        # Get variables by category
        contact_vars = registry.get_variables_by_category(VariableCategory.CONTACT)
        
        # Add custom fields from organization
        registry.add_custom_fields(org.custom_field_schema)
        
        # Validate template
        errors = registry.validate_template(template_html)
        
        # Extract variables from template
        used_vars = registry.extract_variables(template_html)
    """
    
    # Variable pattern: {{variable_name}} with no spaces
    VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    
    def __init__(self):
        """Initialize the registry with system and built-in variables."""
        self._variables: Dict[str, Variable] = {}
        self._register_builtin_variables()
    
    def _register_builtin_variables(self):
        """Register all built-in system and model variables."""
        
        # Contact variables (from Contact model)
        contact_vars = [
            Variable(
                name="email",
                category=VariableCategory.CONTACT,
                description="Contact's email address",
                example="john.doe@example.com",
                required=True,
                data_type="string"
            ),
            Variable(
                name="first_name",
                category=VariableCategory.CONTACT,
                description="Contact's first name",
                example="John",
                data_type="string"
            ),
            Variable(
                name="last_name",
                category=VariableCategory.CONTACT,
                description="Contact's last name",
                example="Doe",
                data_type="string"
            ),
            Variable(
                name="full_name",
                category=VariableCategory.CONTACT,
                description="Contact's full name (first + last)",
                example="John Doe",
                data_type="string"
            ),
            Variable(
                name="phone",
                category=VariableCategory.CONTACT,
                description="Contact's phone number",
                example="+1234567890",
                data_type="string"
            ),
        ]
        
        # Campaign variables
        campaign_vars = [
            Variable(
                name="campaign_name",
                category=VariableCategory.CAMPAIGN,
                description="Name of the current campaign",
                example="Summer Sale 2025",
                data_type="string"
            ),
            Variable(
                name="campaign_subject",
                category=VariableCategory.CAMPAIGN,
                description="Email subject line",
                example="Don't miss our summer deals!",
                data_type="string"
            ),
            Variable(
                name="from_name",
                category=VariableCategory.CAMPAIGN,
                description="Sender's display name",
                example="ACME Corp",
                data_type="string"
            ),
            Variable(
                name="from_email",
                category=VariableCategory.CAMPAIGN,
                description="Sender's email address",
                example="hello@acme.com",
                data_type="string"
            ),
        ]
        
        # Organization variables
        org_vars = [
            Variable(
                name="organization_name",
                category=VariableCategory.ORGANIZATION,
                description="Organization's name",
                example="ACME Corporation",
                data_type="string"
            ),
        ]
        
        # System variables (generated at send-time)
        system_vars = [
            Variable(
                name="unsubscribe_url",
                category=VariableCategory.SYSTEM,
                description="One-click unsubscribe link (required for CAN-SPAM compliance)",
                example="https://app.example.com/unsubscribe?token=abc123",
                required=True,
                data_type="url"
            ),
            Variable(
                name="view_in_browser_url",
                category=VariableCategory.SYSTEM,
                description="Link to view email in browser",
                example="https://app.example.com/view?id=campaign123",
                data_type="url"
            ),
            Variable(
                name="current_date",
                category=VariableCategory.SYSTEM,
                description="Current date when email is sent",
                example="December 17, 2025",
                data_type="date"
            ),
            Variable(
                name="current_year",
                category=VariableCategory.SYSTEM,
                description="Current year (useful for copyright)",
                example="2025",
                data_type="string"
            ),
        ]
        
        # Register all built-in variables
        for var in contact_vars + campaign_vars + org_vars + system_vars:
            self._variables[var.name] = var
    
    def register_variable(self, variable: Variable) -> None:
        """
        Register a new variable in the registry.
        
        Args:
            variable: Variable instance to register
        """
        self._variables[variable.name] = variable
    
    def add_custom_fields(self, custom_field_schema: List[Dict[str, Any]]) -> None:
        """
        Add custom field variables from organization's schema.
        
        Args:
            custom_field_schema: List of custom field definitions
                Example: [
                    {"name": "company", "type": "string", "description": "Company name"},
                    {"name": "department", "type": "string", "description": "Department"}
                ]
        """
        for field_def in custom_field_schema:
            name = field_def.get("name", "")
            if not name:
                continue
            
            variable = Variable(
                name=name,
                category=VariableCategory.CUSTOM,
                description=field_def.get("description", f"Custom field: {name}"),
                example=field_def.get("example", ""),
                data_type=field_def.get("type", "string")
            )
            self._variables[name] = variable
    
    def get_variable(self, name: str) -> Optional[Variable]:
        """Get a variable by name."""
        return self._variables.get(name)
    
    def get_all_variables(self) -> List[Variable]:
        """Get all registered variables."""
        return list(self._variables.values())
    
    def get_variables_by_category(self, category: VariableCategory) -> List[Variable]:
        """Get all variables in a specific category."""
        return [v for v in self._variables.values() if v.category == category]
    
    def get_variable_names(self) -> Set[str]:
        """Get set of all variable names."""
        return set(self._variables.keys())
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert all variables to list of dictionaries for API response."""
        return [v.to_dict() for v in self._variables.values()]
    
    def to_categorized_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get variables organized by category."""
        result: Dict[str, List[Dict[str, Any]]] = {}
        for var in self._variables.values():
            category_name = var.category.value
            if category_name not in result:
                result[category_name] = []
            result[category_name].append(var.to_dict())
        return result
    
    def extract_variables(self, template: str) -> Set[str]:
        """
        Extract all variable placeholders from a template.
        
        Args:
            template: Template string containing {{variable}} placeholders
            
        Returns:
            Set of variable names found in the template
        """
        matches = self.VARIABLE_PATTERN.findall(template)
        return set(matches)
    
    def validate_template(self, template: str) -> Dict[str, Any]:
        """
        Validate a template and check for unknown variables.
        
        Args:
            template: Template string to validate
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "used_variables": [...],
                "unknown_variables": [...],
                "missing_required": [...],
                "warnings": [...]
            }
        """
        used_vars = self.extract_variables(template)
        known_vars = self.get_variable_names()
        
        unknown_vars = used_vars - known_vars
        known_used = used_vars & known_vars
        
        # Check for required variables that are missing
        required_vars = {v.name for v in self._variables.values() if v.required}
        missing_required = required_vars - used_vars
        
        warnings = []
        if "unsubscribe_url" not in used_vars:
            warnings.append(
                "Template does not include {{unsubscribe_url}}. "
                "This is required for CAN-SPAM compliance."
            )
        
        return {
            "valid": len(unknown_vars) == 0,
            "used_variables": [
                self._variables[v].to_dict() 
                for v in known_used 
                if v in self._variables
            ],
            "unknown_variables": list(unknown_vars),
            "missing_required": list(missing_required),
            "warnings": warnings
        }
    
    def render_template(
        self, 
        template: str, 
        context: Dict[str, Any],
        fallback: str = ""
    ) -> str:
        """
        Render a template by replacing variables with values from context.
        
        Args:
            template: Template string with {{variable}} placeholders
            context: Dictionary of variable name -> value mappings
            fallback: Value to use for missing variables (default: empty string)
            
        Returns:
            Rendered template with variables replaced
        """
        result = template
        
        for var_name in self.extract_variables(template):
            placeholder = "{{" + var_name + "}}"
            value = context.get(var_name, fallback)
            result = result.replace(placeholder, str(value) if value else fallback)
        
        return result
    
    def build_context_from_contact(
        self,
        contact,
        campaign=None,
        organization=None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a complete variable context for rendering.
        
        Args:
            contact: Contact model instance
            campaign: Optional Campaign model instance
            organization: Optional Organization model instance
            extra_context: Additional context values
            
        Returns:
            Dictionary with all variable values
        """
        from django.utils import timezone
        
        context = {
            # Contact variables
            "email": contact.email,
            "first_name": contact.first_name or "",
            "last_name": contact.last_name or "",
            "full_name": contact.full_name or "",
            "phone": getattr(contact, 'phone', '') or "",
            
            # System variables
            "unsubscribe_url": f"/campaigns/unsubscribe/?token={contact.unsubscribe_token}",
            "current_date": timezone.now().strftime("%B %d, %Y"),
            "current_year": str(timezone.now().year),
        }
        
        # Add campaign variables
        if campaign:
            context.update({
                "campaign_name": campaign.name,
                "campaign_subject": campaign.subject,
                "from_name": campaign.from_name or "",
                "from_email": campaign.from_email or "",
            })
        
        # Add organization variables
        if organization:
            context.update({
                "organization_name": organization.name,
            })
        elif hasattr(contact, 'organization') and contact.organization:
            context["organization_name"] = contact.organization.name
        
        # Add custom fields from contact
        if hasattr(contact, 'custom_fields') and contact.custom_fields:
            context.update(contact.custom_fields)
        
        # Add any extra context
        if extra_context:
            context.update(extra_context)
        
        return context


# Singleton instance for convenience
_default_registry: Optional[VariableRegistry] = None


def get_variable_registry() -> VariableRegistry:
    """Get the default variable registry instance."""
    global _default_registry
    if _default_registry is None:
        _default_registry = VariableRegistry()
    return _default_registry


def get_variables_for_organization(organization) -> VariableRegistry:
    """
    Get a variable registry populated with organization's custom fields.
    
    Args:
        organization: Organization model instance
        
    Returns:
        VariableRegistry with built-in + organization custom variables
    """
    registry = VariableRegistry()
    
    # Add organization's custom field schema if available
    if hasattr(organization, 'custom_field_schema') and organization.custom_field_schema:
        registry.add_custom_fields(organization.custom_field_schema)
    
    return registry
