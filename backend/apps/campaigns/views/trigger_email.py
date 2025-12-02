import uuid
import logging
from datetime import timedelta

from rest_framework.response import Response
from rest_framework import status, permissions, generics

from ..models import AutomationRule
from ..serializers import TriggerEmailSerializer
from ..tasks import dispatch_email_task
from ..utils.hierarchy_resolver import HierarchicalResolver, is_email_service_active
from core.mixins import CustomResponseMixin


class TriggerEmailView(CustomResponseMixin, generics.GenericAPIView):
    """
    A generic endpoint for other microservices to trigger one-off emails
    based on tenant, product, and reason.
    
    Uses hierarchical resolution:
    1. Tenant-specific rule (if tenant_id provided and rule exists)
    2. Global rule (fallback when tenant rule not found)
    
    This enables pre-signup emails using global TMD configurations.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = TriggerEmailSerializer
    queryset = AutomationRule.objects.all()

    def post(self, request, *args, **kwargs):
        # Parse optional debug flag and correlation id for better traceability across services
        debug = str(request.query_params.get("debug", "")).lower() in ("1", "true", "yes")
        correlation_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        rule_id = data.get("rule_id")
        automation_name = data.get("automation_name")
        reason_name = data.get("reason_name")
        email_variables = data.get("email_variables")
        recipient_emails = data.get("recipient_emails")
        product_id = data.get("product_id")
        tenant_id = data.get("tenant_id")
        email_template_id = data.get("email_template_id")

        # Check if email service is active (supports pre-signup with tenant_id=None)
        if not is_email_service_active(tenant_id=tenant_id, product_id=product_id):
            body = {
                "error_code": "EMAIL_SERVICE_INACTIVE",
                "message": "Email service is not active or not enabled for this product/tenant.",
                "details": {
                    "product_id": product_id,
                    "tenant_id": tenant_id,
                    "service_active": False
                },
                "correlation_id": correlation_id,
            }
            return Response(body, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 1. Direct lookup by rule_id or automation_name (highest precedence)
        rule = None
        try:
            if rule_id:
                rule = self.get_queryset().get(id=rule_id)
            elif automation_name:
                rule = self.get_queryset().get(automation_name=automation_name)
        except AutomationRule.DoesNotExist:
            body = {
                "error_code": "RULE_NOT_FOUND_BY_IDENTIFIER",
                "message": "Specified automation rule not found.",
                "details": {"rule_id": rule_id, "automation_name": automation_name},
                "correlation_id": correlation_id,
            }
            return Response(body, status=status.HTTP_404_NOT_FOUND)
        except AutomationRule.MultipleObjectsReturned:
            count = self.get_queryset().filter(automation_name=automation_name).count() if automation_name else None
            body = {
                "error_code": "MULTIPLE_RULES_FOR_NAME",
                "message": "Multiple rules matched automation_name. Use rule_id.",
                "details": {"automation_name": automation_name, "matches": count},
                "correlation_id": correlation_id,
            }
            return Response(body, status=status.HTTP_409_CONFLICT)

        # 2. If not directly specified, use hierarchical resolver (tenant → global)
        if not rule and reason_name:
            rule = HierarchicalResolver.get_automation_rule(
                reason_name=reason_name,
                tenant_id=tenant_id,
                communication_type='EMAIL'
            )
            
            if not rule:
                body = {
                    "error_code": "RULE_NOT_FOUND",
                    "message": f"No AutomationRule found for reason '{reason_name}'.",
                    "details": {
                        "reason_name": reason_name,
                        "tenant_id": tenant_id,
                        "hierarchy_checked": ["tenant-specific", "global"]
                    },
                    "correlation_id": correlation_id,
                }
                return Response(body, status=status.HTTP_404_NOT_FOUND)

        # 3. Validate trigger type
        if rule.trigger_type not in [AutomationRule.TriggerType.IMMEDIATE, AutomationRule.TriggerType.DELAY]:
            body = {
                "error_code": "INVALID_TRIGGER_TYPE",
                "message": "This rule is a recurring schedule and cannot be triggered manually.",
                "details": {"rule_id": rule.id, "trigger_type": str(rule.trigger_type)},
                "correlation_id": correlation_id,
            }
            return Response(body, status=status.HTTP_400_BAD_REQUEST)

        # Prepare task arguments (email_template_id can override rule's template)
        # Pass tenant_id and product_id from request to override rule's values if provided
        task_args = [
            rule.id, 
            recipient_emails, 
            email_variables, 
            email_template_id, 
            None,  # planned_delivery_at
            tenant_id,  # override_tenant_id
            product_id   # override_product_id
        ]

        if rule.trigger_type == AutomationRule.TriggerType.IMMEDIATE:
            try:
                result = dispatch_email_task.delay(*task_args)
                body = {
                    "message": "Email dispatch initiated immediately.",
                    "task_id": getattr(result, 'id', None),
                    "rule_id": rule.id,
                    "correlation_id": correlation_id,
                }
                if debug:
                    body["debug"] = {
                        "automation_name": getattr(rule, 'automation_name', None),
                        "reason_name": getattr(rule, 'reason_name', None),
                    }
                return Response(body, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                logging.exception("Failed to dispatch email task")
                body = {
                    "error_code": "TASK_DISPATCH_FAILED",
                    "message": "Failed to enqueue email dispatch task.",
                    "details": {"exception": type(e).__name__, "error": str(e)},
                    "correlation_id": correlation_id,
                }
                return Response(body, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            try:
                delay_kwargs = {rule.delay_unit.lower(): rule.delay_amount}
                delay_seconds = timedelta(**delay_kwargs).total_seconds()
            except Exception as e:
                body = {
                    "error_code": "INVALID_DELAY_CONFIG",
                    "message": "Invalid delay configuration on rule.",
                    "details": {"delay_unit": getattr(rule, 'delay_unit', None), "delay_amount": getattr(rule, 'delay_amount', None), "exception": type(e).__name__, "error": str(e)},
                    "correlation_id": correlation_id,
                }
                return Response(body, status=status.HTTP_400_BAD_REQUEST)

            try:
                result = dispatch_email_task.apply_async(args=task_args, countdown=delay_seconds)
                body = {
                    "message": f"Email scheduled for dispatch in {rule.delay_amount} {rule.delay_unit.lower()}.",
                    "task_id": getattr(result, 'id', None),
                    "rule_id": rule.id,
                    "eta_seconds": delay_seconds,
                    "correlation_id": correlation_id,
                }
                if debug:
                    body["debug"] = {
                        "automation_name": getattr(rule, 'automation_name', None),
                        "reason_name": getattr(rule, 'reason_name', None),
                    }
                return Response(body, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                logging.exception("Failed to schedule email task")
                print("Error occurred while scheduling email task:", e)
                body = {
                    "error_code": "TASK_SCHEDULE_FAILED",
                    "message": "Failed to schedule email dispatch task.",
                    "details": {"exception": type(e).__name__, "error": str(e)},
                    "correlation_id": correlation_id,
                }
                return Response(body, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({"message": "Email triggered successfully."},
                        status=status.HTTP_200_OK)
