import uuid
import logging

from rest_framework.response import Response
from rest_framework import status, permissions, generics, filters

from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from ..models import AutomationRule, EmailTemplate, EmailProvider
from ..serializers import (
    GlobalTriggerEmailSerializer, GlobalEmailTemplateSerializer, GlobalAutomationRuleSerializer, EmailProviderSerializer
)
from ..tasks import dispatch_email_task
from ..utils import is_email_service_active
from core.mixins import CustomResponseMixin
from core.utils import UniversalAutoFilterMixin

logger = logging.getLogger(__name__)


class GlobalEmailTriggerView(CustomResponseMixin, generics.GenericAPIView):
    """
    Trigger emails using global automation rules and templates.
    This endpoint specifically handles global email automation without tenant restrictions.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = GlobalTriggerEmailSerializer
    queryset = AutomationRule.objects.filter(rule_scope=AutomationRule.RuleScope.GLOBAL)

    def post(self, request, *args, **kwargs):
        debug = str(request.query_params.get("debug", "")).lower() in ("1", "true", "yes")
        correlation_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Extract data
        rule_id = data.get("rule_id")
        automation_name = data.get("automation_name")
        reason_name = data.get("reason_name")
        email_variables = data.get("email_variables")
        recipient_emails = data.get("recipient_emails")
        product_id = data.get("product_id")
        email_template_id = data.get("email_template_id")

        # For global setup, we don't require tenant-specific email service checks
        # But we still validate if global email service is available
        if not is_email_service_active(product_id=product_id, tenant_id=None):
            return self.error_response(
                message="Global email service is not active or available.",
                data={
                    "product_id": product_id,
                    "service_type": "global",
                    "service_active": False,
                    "correlation_id": correlation_id
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 1. Direct lookup by rule_id or automation_name for global rules
        rule = None
        try:
            if rule_id:
                rule = self.get_queryset().get(id=rule_id)
            elif automation_name:
                rule = self.get_queryset().get(automation_name=automation_name)
        except AutomationRule.DoesNotExist:
            return self.error_response(
                message="Specified global automation rule not found.",
                data={
                    "rule_id": rule_id, 
                    "automation_name": automation_name,
                    "rule_scope": "GLOBAL",
                    "correlation_id": correlation_id
                },
                status_code=status.HTTP_404_NOT_FOUND
            )
        except AutomationRule.MultipleObjectsReturned:
            count = self.get_queryset().filter(automation_name=automation_name).count() if automation_name else None
            return self.error_response(
                message="Multiple global rules matched automation_name. Use rule_id for specific targeting.",
                data={
                    "automation_name": automation_name, 
                    "matches": count,
                    "rule_scope": "GLOBAL",
                    "correlation_id": correlation_id
                },
                status_code=status.HTTP_409_CONFLICT
            )

        # 2. If not directly specified, build filtered search for global rules
        if not rule:
            base_filter = {
                "communication_type": AutomationRule.CommunicationType.EMAIL,
                "rule_scope": AutomationRule.RuleScope.GLOBAL,
                "reason_name": reason_name,
            }
            
            # Add optional filters
            if product_id is not None:
                base_filter["product_id"] = product_id
            if email_template_id:
                base_filter["email_template_id"] = email_template_id

            queryset = self.get_queryset().filter(**base_filter).order_by('id')

            if not queryset.exists():
                return self.error_response(
                    message="No global automation rule found matching the specified criteria.",
                    data={
                        "reason_name": reason_name,
                        "product_id": product_id,
                        "email_template_id": email_template_id,
                        "rule_scope": "GLOBAL",
                        "correlation_id": correlation_id
                    },
                    status_code=status.HTTP_404_NOT_FOUND
                )

            if queryset.count() > 1:
                return self.error_response(
                    message="Multiple global automation rules match criteria. Please be more specific.",
                    data={
                        "matches": queryset.count(),
                        "reason_name": reason_name,
                        "rule_scope": "GLOBAL",
                        "correlation_id": correlation_id
                    },
                    status_code=status.HTTP_409_CONFLICT
                )

            rule = queryset.first()

        # 3. Dispatch the email task for global rule
        try:
            task_result = dispatch_email_task.delay(
                rule_id=str(rule.id),
                recipient_emails=recipient_emails,
                email_variables=email_variables,
                email_template_id=email_template_id
            )

            response_data = {
                "message": "Global email dispatched successfully.",
                "rule_details": {
                    "rule_id": rule.id,
                    "automation_name": rule.automation_name,
                    "rule_scope": rule.rule_scope,
                    "reason_name": rule.reason_name,
                    "product_id": rule.product_id,
                },
                "task_id": task_result.id,
                "recipient_count": len(recipient_emails),
                "correlation_id": correlation_id,
                "timestamp": timezone.now().isoformat(),
            }

            return self.success_response(
                data=response_data,
                message="Global email automation triggered successfully",
                status_code=status.HTTP_202_ACCEPTED
            )

        except Exception as e:
            logger.error(f"Failed to dispatch global email task: {str(e)}", extra={
                "correlation_id": correlation_id,
                "rule_id": rule.id,
                "error": str(e)
            })
            return self.error_response(
                message="Failed to dispatch global email task.",
                data={
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GlobalAutomationRuleListView(CustomResponseMixin, generics.ListCreateAPIView):
    """
    List and create global automation rules.
    GET: List all global automation rules
    POST: Create new global automation rule
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = GlobalAutomationRuleSerializer
    queryset = AutomationRule.objects.filter(rule_scope=AutomationRule.RuleScope.GLOBAL)

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by communication type if specified
        communication_type = self.request.query_params.get('communication_type')
        if communication_type:
            queryset = queryset.filter(communication_type=communication_type)
        
        # Filter by reason name if specified
        reason_name = self.request.query_params.get('reason_name')
        if reason_name:
            queryset = queryset.filter(reason_name=reason_name)
        
        # Filter by product if specified
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return self.success_response(
            data={
                "rules": serializer.data,
                "count": queryset.count(),
                "filters_applied": {
                    "rule_scope": "GLOBAL",
                    "communication_type": request.query_params.get('communication_type'),
                    "reason_name": request.query_params.get('reason_name'),
                    "product_id": request.query_params.get('product_id'),
                }
            },
            message=f"Retrieved {queryset.count()} global automation rules"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        rule = serializer.save()
        
        return self.success_response(
            data=GlobalAutomationRuleSerializer(rule).data,
            message="Global automation rule created successfully",
            status_code=status.HTTP_201_CREATED
        )


class GlobalEmailTemplateListView(UniversalAutoFilterMixin, CustomResponseMixin, generics.ListCreateAPIView):
    """
    List and create global email templates.
    GET: List all global email templates with support for:
        - Filtering: ?field=value, ?field__contains=value, ?field__gte=value, etc.
        - Searching: ?search=keyword (searches across all text fields)
        - Ordering: ?ordering=field or ?ordering=-field (descending)
    POST: Create new global email template
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = GlobalEmailTemplateSerializer
    queryset = EmailTemplate.objects.filter(template_type=EmailTemplate.TemplateType.GLOBAL)

    def list(self, request, *args, **kwargs):
        # Apply filters, search, and ordering through UniversalAutoFilterMixin
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # Get applied filters from query params for response
        applied_filters = {
            "template_type": "GLOBAL",
        }
        
        # Add all query params as applied filters (except 'search' and 'ordering')
        for key, value in request.query_params.items():
            if key not in ['search', 'ordering']:
                applied_filters[key] = value
        
        return self.success_response(
            data={
                "templates": serializer.data,
                "count": queryset.count(),
                "categories": list(EmailTemplate.TemplateCategory.choices),
                "filters_applied": applied_filters,
                "search_query": request.query_params.get('search'),
                "ordering": request.query_params.get('ordering'),
            },
            message=f"Retrieved {queryset.count()} global email templates"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template = serializer.save()
        
        return self.success_response(
            data=GlobalEmailTemplateSerializer(template).data,
            message="Global email template created successfully",
            status_code=status.HTTP_201_CREATED
        )


class GlobalEmailAnalyticsView(CustomResponseMixin, generics.GenericAPIView):
    """
    Get analytics for global email automation usage.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Get analytics for global email automation usage.
        """
        try:
            # Get global rules analytics
            total_global_rules = AutomationRule.objects.filter(
                rule_scope=AutomationRule.RuleScope.GLOBAL
            ).count()
            
            active_global_rules = AutomationRule.objects.filter(
                rule_scope=AutomationRule.RuleScope.GLOBAL,
                activated_by_root=True,
                activated_by_tmd=True
            ).count()
            
            # Email-specific global rules
            email_global_rules = AutomationRule.objects.filter(
                rule_scope=AutomationRule.RuleScope.GLOBAL,
                communication_type=AutomationRule.CommunicationType.EMAIL
            ).count()
            
            # Global templates analytics
            total_global_templates = EmailTemplate.objects.filter(
                template_type=EmailTemplate.TemplateType.GLOBAL
            ).count()
            
            templates_by_category = EmailTemplate.objects.filter(
                template_type=EmailTemplate.TemplateType.GLOBAL
            ).values('category').annotate(count=Count('category'))
            
            # Global providers (all EmailProvider instances are global)
            total_global_providers = EmailProvider.objects.filter(
                activated_by_root=True,
                activated_by_tmd=True
            ).count()
            
            analytics_data = {
                "global_automation_rules": {
                    "total": total_global_rules,
                    "active": active_global_rules,
                    "email_rules": email_global_rules,
                },
                "global_email_templates": {
                    "total": total_global_templates,
                    "by_category": {item['category']: item['count'] for item in templates_by_category}
                },
                "global_email_providers": {
                    "total": total_global_providers,
                },
                "system_info": {
                    "supports_global_automation": True,
                    "supports_tenant_specific": True,
                    "analytics_generated_at": timezone.now().isoformat(),
                }
            }
            
            return Response({
                "success": True,
                "message": "Global email analytics retrieved successfully",
                "data": analytics_data,
                "timestamp": timezone.now().isoformat(),
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to generate global email analytics: {str(e)}")
            return Response({
                "success": False,
                "message": "Failed to generate global email analytics",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GlobalEmailHealthCheckView(CustomResponseMixin, generics.GenericAPIView):
    """
    Health check specifically for global email functionality.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Health check specifically for global email functionality.
        """
        try:
            health_status = {
                "service": "global_email_automation",
                "status": "healthy",
                "checks": {}
            }
            
            # Check if we have any global automation rules
            global_rules_count = AutomationRule.objects.filter(
                rule_scope=AutomationRule.RuleScope.GLOBAL,
                activated_by_root=True,
                activated_by_tmd=True
            ).count()
            
            health_status["checks"]["global_rules"] = {
                "status": "healthy" if global_rules_count > 0 else "warning",
                "count": global_rules_count,
                "message": f"{global_rules_count} active global rules available"
            }
            
            # Check global email templates
            global_templates_count = EmailTemplate.objects.filter(
                template_type=EmailTemplate.TemplateType.GLOBAL
            ).count()
            
            health_status["checks"]["global_templates"] = {
                "status": "healthy" if global_templates_count > 0 else "warning",
                "count": global_templates_count,
                "message": f"{global_templates_count} global templates available"
            }
            
            # Check global email providers
            active_providers_count = EmailProvider.objects.filter(
                activated_by_root=True,
                activated_by_tmd=True
            ).count()
            
            health_status["checks"]["email_providers"] = {
                "status": "healthy" if active_providers_count > 0 else "critical",
                "count": active_providers_count,
                "message": f"{active_providers_count} active email providers available"
            }
            
            # Overall health determination
            if health_status["checks"]["email_providers"]["status"] == "critical":
                health_status["status"] = "unhealthy"
            elif any(check["status"] == "warning" for check in health_status["checks"].values()):
                health_status["status"] = "warning"
            
            health_status["timestamp"] = timezone.now().isoformat()
            
            return Response({
                "success": True,
                "message": "Global email health check completed",
                "data": health_status,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Global email health check failed: {str(e)}")
            return Response({
                "success": False,
                "message": "Global email health check failed",
                "error": str(e),
                "timestamp": timezone.now().isoformat(),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GlobalAutomationRuleDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific global automation rule.
    GET: Retrieve global automation rule details
    PUT/PATCH: Update global automation rule
    DELETE: Delete global automation rule
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = GlobalAutomationRuleSerializer
    queryset = AutomationRule.objects.filter(rule_scope=AutomationRule.RuleScope.GLOBAL)
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return self.success_response(
            data=serializer.data,
            message="Global automation rule retrieved successfully"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        rule = serializer.save()
        
        return self.success_response(
            data=GlobalAutomationRuleSerializer(rule).data,
            message="Global automation rule updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        rule_name = instance.automation_name
        instance.delete()
        
        return self.success_response(
            data={"deleted_rule": rule_name},
            message=f"Global automation rule '{rule_name}' deleted successfully"
        )


class GlobalEmailTemplateDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific global email template.
    GET: Retrieve global email template details
    PUT/PATCH: Update global email template
    DELETE: Delete global email template
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = GlobalEmailTemplateSerializer
    queryset = EmailTemplate.objects.filter(template_type=EmailTemplate.TemplateType.GLOBAL)
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return self.success_response(
            data=serializer.data,
            message="Global email template retrieved successfully"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        template = serializer.save()
        
        return self.success_response(
            data=GlobalEmailTemplateSerializer(template).data,
            message="Global email template updated successfully"
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        template_name = instance.template_name
        instance.delete()
        
        return self.success_response(
            data={"deleted_template": template_name},
            message=f"Global email template '{template_name}' deleted successfully"
        )


class GlobalEmailProviderListView(CustomResponseMixin, generics.ListAPIView):
    """
    List all global email providers (EmailProvider model).
    This is an alias/convenience view for email/providers/ endpoint.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailProviderSerializer
    queryset = EmailProvider.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider_type', 'activated_by_root', 'activated_by_tmd', 'is_default']
    search_fields = ['name', 'provider_type']
    ordering_fields = ['name', 'created_at', 'priority']
    ordering = ['priority', 'name']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return self.success_response(
            data={
                "providers": serializer.data,
                "count": queryset.count(),
            },
            message=f"Retrieved {queryset.count()} global email providers"
        )