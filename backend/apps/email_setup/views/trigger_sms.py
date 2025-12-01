from rest_framework.response import Response
from rest_framework import status, permissions, generics

from ..models import AutomationRule
from ..serializers import TriggerSMSSerializer
from ..tasks import send_delayed_sms, send_sms, send_delayed_whatsapp
from ..utils import send_whatsapp
from core import CustomResponseMixin


class DelayCalculator:
    """Helper class to calculate delay in seconds based on delay unit and amount"""
    
    @staticmethod
    def calculate_delay_seconds(delay_amount, delay_unit):
        """Calculate delay in seconds from delay amount and unit"""
        unit_multipliers = {
            AutomationRule.DelayUnit.SECONDS: 1,
            AutomationRule.DelayUnit.MINUTES: 60,
            AutomationRule.DelayUnit.HOURS: 3600,
            AutomationRule.DelayUnit.DAYS: 86400,
        }
        return delay_amount * unit_multipliers.get(delay_unit, 0)


class SMSAutomationHandler:
    """Handler class for SMS and WhatsApp automation logic"""
    
    @staticmethod
    def get_automation_rule(automation_name=None, rule_id=None, reason_name=None, product_id=None):
        """Get automation rule by name, ID, or reason (optionally narrowed by product)."""
        if automation_name:
            return AutomationRule.objects.get(automation_name=automation_name)
        if rule_id:
            return AutomationRule.objects.get(id=rule_id)
        if reason_name:
            qs = AutomationRule.objects.filter(reason_name=reason_name)
            if product_id:
                qs = qs.filter(product_id=product_id)
            rule = qs.order_by('-id').first()
            if not rule:
                raise AutomationRule.DoesNotExist()
            return rule
        raise ValueError("Provide one of: automation_name, rule_id, or reason_name (optionally with product_id)")
    
    @staticmethod
    def validate_sms_rule(rule):
        """Validate that the rule is configured for SMS or WhatsApp"""
        valid_types = [
            AutomationRule.CommunicationType.SMS,
            getattr(AutomationRule.CommunicationType, 'WHATSAPP', None)
        ]
        if rule.communication_type not in valid_types:
            raise ValueError("Rule not configured for SMS or WhatsApp")
    
    @staticmethod
    def handle_immediate_sms(rule, sms_variables, recipient_numbers, use_whatsapp=False):
        """Handle immediate SMS/WhatsApp sending"""
        if use_whatsapp:
            result = send_whatsapp(rule.id, sms_variables, recipient_numbers)
        else:
            result = send_sms(rule.id, sms_variables, recipient_numbers)
            
        if not result:
            message_type = "WhatsApp" if use_whatsapp else "SMS"
            raise RuntimeError(f"Failed to send {message_type}")
        return {"message_sids": result}
    
    @staticmethod
    def handle_delayed_sms(rule, sms_variables, recipient_numbers, use_whatsapp=False):
        """Handle delayed SMS/WhatsApp sending"""
        delay_seconds = DelayCalculator.calculate_delay_seconds(
            rule.delay_amount, rule.delay_unit
        )
        
        if use_whatsapp:
            task = send_delayed_whatsapp.apply_async(
                args=[rule.id], 
                kwargs={"sms_variables": sms_variables, "recipient_numbers": recipient_numbers},
                countdown=delay_seconds
            )
        else:
            task = send_delayed_sms.apply_async(
                args=[rule.id], 
                kwargs={"sms_variables": sms_variables, "recipient_numbers": recipient_numbers},
                countdown=delay_seconds
            )
        
        message_type = "WhatsApp" if use_whatsapp else "SMS"
        return {
            "task_id": task.id,
            "scheduled_for": f"{rule.delay_amount} {rule.delay_unit.lower()}",
            "message_type": message_type
        }
    
    @staticmethod
    def handle_scheduled_sms(rule):
        """Handle scheduled SMS/WhatsApp validation"""
        if not (rule.periodic_task and rule.periodic_task.enabled):
            raise ValueError("SMS/WhatsApp schedule is not active")
        
        return {"next_run": rule.periodic_task.last_run_at}


def trigger_sms_automation(automation_name=None, rule_id=None, reason_name=None, product_id=None, sms_variables=None, recipient_numbers=None, use_whatsapp=False):
    """
    Triggers an SMS or WhatsApp automation based on its rule configuration.
    Handles immediate, delayed, and scheduled triggers.
    
    Args:
        automation_name: Name of the automation rule (preferred way to identify a rule)
        rule_id: UUID of the automation rule (alternative to automation_name)
        sms_variables: Dict of variables to replace in the SMS/WhatsApp template
        recipient_numbers: List of phone numbers to send SMS/WhatsApp to (overrides template recipients)
        use_whatsapp: Boolean to determine whether to send via WhatsApp
    
    Returns:
        Dict with response data including success/error status and relevant data
    """
    try:
        handler = SMSAutomationHandler()
        # Get and validate the rule
        rule = handler.get_automation_rule(
            automation_name=automation_name,
            rule_id=rule_id,
            reason_name=reason_name,
            product_id=product_id,
        )
        handler.validate_sms_rule(rule)
        
        message_type = "WhatsApp" if use_whatsapp else "SMS"
        
        # Handle based on trigger type
        if rule.trigger_type == AutomationRule.TriggerType.IMMEDIATE:
            data = handler.handle_immediate_sms(rule, sms_variables, recipient_numbers, use_whatsapp)
            return {
                "success": True,
                "message": f"{message_type} sent successfully",
                "status_code": 200,
                "data": data
            }
            
        elif rule.trigger_type == AutomationRule.TriggerType.DELAY:
            data = handler.handle_delayed_sms(rule, sms_variables, recipient_numbers, use_whatsapp)
            return {
                "success": True,
                "message": f"{message_type} scheduled to be sent in {data['scheduled_for']}",
                "status_code": 202,
                "data": data
            }
            
        elif rule.trigger_type == AutomationRule.TriggerType.SCHEDULE:
            data = handler.handle_scheduled_sms(rule)
            return {
                "success": True,
                "message": f"{message_type} is scheduled according to the rule configuration",
                "status_code": 200,
                "data": data
            }
                
    except AutomationRule.DoesNotExist:
        rule_identifier = automation_name or reason_name or rule_id
        print(f"Automation rule not found: {rule_identifier}")
        return {
            "success": False,
            "message": f"Automation rule not found: {rule_identifier}",
            "status_code": 404,
            "data": {}
        }
    except ValueError as e:
        rule_identifier = automation_name or reason_name or rule_id
        print(f"Validation error for rule {rule_identifier}: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "status_code": 400,
            "data": {}
        }
    except Exception as e:
        rule_identifier = automation_name or reason_name or rule_id
        mt = "WhatsApp" if use_whatsapp else "SMS"
        print(f"Error triggering {mt} automation for rule {rule_identifier}: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "status_code": 500,
            "data": {}
        }


class TriggerSMSView(CustomResponseMixin, generics.GenericAPIView):
    """
    A generic endpoint for other microservices to trigger one-off SMS or WhatsApp messages.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = TriggerSMSSerializer
    queryset = AutomationRule.objects.all()

    def post(self, request, rule_id=None, *args, **kwargs):
        # Merge URL rule_id with request data
        data = request.data.copy()
        if rule_id:
            data['rule_id'] = rule_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        reason_name = validated_data.get("reason_name")
        rule_id = validated_data.get("rule_id")
        sms_variables = validated_data.get("sms_variables", {})
        recipient_numbers = validated_data.get("recipient_numbers")
        use_whatsapp = validated_data.get("use_whatsapp", False)
        product_id = validated_data.get("product_id")

        # Use the trigger_sms_automation function
        result = trigger_sms_automation(
            reason_name=reason_name,
            product_id=product_id,
            rule_id=rule_id,
            sms_variables=sms_variables,
            recipient_numbers=recipient_numbers,
            use_whatsapp=use_whatsapp
        )

        # Check if this is a one-off trigger request (not for scheduled rules)
        if not result["success"] and result["status_code"] == 404:
            return Response(
                {"error": f"AutomationRule with identifier '{reason_name or rule_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        elif not result["success"]:
            return Response(
                {"error": result["message"]},
                status=result["status_code"]
            )

        # For successful results, check if it's a scheduled rule (which shouldn't be triggered manually)
        try:
            rule = SMSAutomationHandler.get_automation_rule(reason_name=reason_name, rule_id=rule_id, product_id=product_id)
            if rule.trigger_type == AutomationRule.TriggerType.SCHEDULE:
                return Response(
                    {"error": "This rule is a recurring schedule and cannot be triggered manually."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            # Rule validation already handled in trigger_sms_automation
            print(f"Error validating rule {rule_id}: {str(e)}")

        inner = result.get("data", {}) or {}
        payload = {"message": result.get("message", "Success"), **inner}
        return Response(payload, status=result["status_code"])


class TriggerWhatsAppView(TriggerSMSView):
    """
    A specific endpoint for triggering WhatsApp messages.
    """
    
    def post(self, request, rule_id=None, *args, **kwargs):
        # Force use_whatsapp to True for this endpoint
        data = request.data.copy()
        data['use_whatsapp'] = True
        if rule_id:
            data['rule_id'] = rule_id
            
        request._full_data = data
        return super().post(request, rule_id, *args, **kwargs)