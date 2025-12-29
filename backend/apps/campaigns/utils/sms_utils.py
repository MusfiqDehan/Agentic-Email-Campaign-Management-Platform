from twilio.rest import Client
from ..models import AutomationRule
from .crypto import decrypt_data
from .email_utils import process_template_variables


def send_sms(rule_id, sms_variables=None, recipient_numbers=None):
    """
    Utility function to send SMS messages based on an automation rule.
    
    Args:
        rule_id: ID of the AutomationRule
        sms_variables: Dictionary of template variables
        recipient_numbers: Optional list of phone numbers to override template recipients
    """
    if sms_variables is None:
        sms_variables = {}
        
    try:
        rule = AutomationRule.objects.get(id=rule_id)
        
        # Check if rule supports SMS
        if rule.communication_type != AutomationRule.CommunicationType.SMS:
            print(f"Rule {rule_id} is not configured for SMS")
            return False
            
        if not rule.sms_template_id:
            print(f"Rule {rule_id} has no SMS template configured")
            return False
            
        if not rule.sms_config_id:
            print(f"Rule {rule_id} has no SMS configuration")
            return False

        # Get SMS configuration
        sms_config = rule.sms_config_id
        
        # Get template
        template = rule.sms_template_id
        
        # Process template with sms_variables data
        body = process_template_variables(template.sms_body, sms_variables)
        
        # Get recipient numbers
        if not recipient_numbers:
            recipient_numbers = [num.strip() for num in template.recipient_numbers_list.split(',') if num.strip()]
        
        # Initialize Twilio client
        client = Client(sms_config.account_ssid, decrypt_data(sms_config.auth_token))
        
        # Send SMS to all recipients
        message_sids = []
        for number in recipient_numbers:
            try:
                # Clean and format number for SMS
                clean_number = number.strip()
                
                # Remove any WhatsApp prefix if present
                if clean_number.startswith('whatsapp:'):
                    clean_number = clean_number.replace('whatsapp:', '')
                
                # Format for SMS (international format with +)
                if not clean_number.startswith('+'):
                    # For Bangladesh numbers, add +880 country code
                    if clean_number.startswith('880'):
                        clean_number = f"+{clean_number}"
                    elif clean_number.startswith('01'):
                        clean_number = f"+880{clean_number[1:]}"  # Remove leading 0 and add +880
                    else:
                        clean_number = f"+880{clean_number}"  # Assume it's a local number
                
                # Use SMS from number (regular phone number, NOT WhatsApp)
                from_number = getattr(sms_config, 'default_from_number', None) or "+19062928470"
                
                print(f"Sending SMS from {from_number} to {clean_number}")
                
                # Create SMS message (no whatsapp: prefix)
                message = client.messages.create(
                    from_=from_number,
                    body=body,
                    to=clean_number  # Regular phone number format for SMS
                )
                
                message_sids.append(message.sid)
                print(f"SMS sent to {clean_number}, SID: {message.sid}")
                
            except Exception as e:
                print(f"Failed to send SMS to {number}: {str(e)}")

        return message_sids if message_sids else False
        
    except AutomationRule.DoesNotExist:
        print(f"Automation rule with ID {rule_id} not found")
        return False
    except Exception as e:
        print(f"Error sending SMS for rule {rule_id}: {str(e)}")
        return False


def send_whatsapp(rule_id, sms_variables=None, recipient_numbers=None):
    """
    Dedicated function to send WhatsApp messages based on an automation rule.
    """
    if sms_variables is None:
        sms_variables = {}
        
    try:
        rule = AutomationRule.objects.get(id=rule_id)
        
        # Check if rule supports WhatsApp or SMS (since WhatsApp can use SMS rules)
        valid_types = [
            AutomationRule.CommunicationType.SMS,
            getattr(AutomationRule.CommunicationType, 'WHATSAPP', None)
        ]
        if rule.communication_type not in valid_types:
            print(f"Rule {rule_id} is not configured for WhatsApp")
            return False
            
        if not rule.sms_template_id:
            print(f"Rule {rule_id} has no WhatsApp template configured")
            return False
            
        if not rule.sms_config_id:
            print(f"Rule {rule_id} has no WhatsApp configuration")
            return False
        
        # Get SMS configuration (used for WhatsApp too)
        sms_config = rule.sms_config_id
        
        # Check if WhatsApp is enabled in configuration
        if not getattr(sms_config, 'whatsapp_enabled', False):
            print(f"WhatsApp is not enabled in configuration {sms_config.id}")
            return False
        
        # Get template
        template = rule.sms_template_id
        
        # Check if template supports WhatsApp
        if hasattr(template, 'supports_whatsapp') and not template.supports_whatsapp:
            print(f"Template {template.id} does not support WhatsApp")
            return False
        
        # Process template with sms_variables data
        body = process_template_variables(template.sms_body, sms_variables)
        
        # Get recipient numbers - USE DYNAMIC VALUES, NOT HARDCODED
        if not recipient_numbers:
            # Check if template has WhatsApp-specific recipients
            if hasattr(template, 'whatsapp_recipient_numbers_list') and template.whatsapp_recipient_numbers_list:
                recipient_numbers = [num.strip() for num in template.whatsapp_recipient_numbers_list.split(',') if num.strip()]
            else:
                # Fall back to regular SMS recipients but format them for WhatsApp
                recipient_numbers = [num.strip() for num in template.recipient_numbers_list.split(',') if num.strip()]
        
        # Initialize Twilio client
        client = Client(sms_config.account_ssid, decrypt_data(sms_config.auth_token))
        
        # Send WhatsApp to all recipients
        message_sids = []
        for number in recipient_numbers:
            try:
                # Clean and format number for WhatsApp
                clean_number = number.strip()
                
                # Remove any WhatsApp prefix if present
                if clean_number.startswith('whatsapp:'):
                    clean_number = clean_number.replace('whatsapp:', '')
                
                # Format for WhatsApp (international format with +)
                if not clean_number.startswith('+'):
                    # For Bangladesh numbers, add +880 country code
                    if clean_number.startswith('880'):
                        clean_number = f"+{clean_number}"
                    elif clean_number.startswith('01'):
                        clean_number = f"+880{clean_number[1:]}"  # Remove leading 0 and add +880
                    else:
                        clean_number = f"+880{clean_number}"  # Assume it's a local number
                
                # WhatsApp requires whatsapp: prefix for both from and to
                to_number = f"whatsapp:{clean_number}"
                print(f"Sending WhatsApp to {to_number}")
                
                # Get WhatsApp from number from configuration
                whatsapp_from = getattr(sms_config, 'whatsapp_from_number', None)
                if whatsapp_from:
                    # Ensure from_number has proper formatting
                    if whatsapp_from.startswith('whatsapp:'):
                        whatsapp_from = whatsapp_from.replace('whatsapp:', '')
                    if not whatsapp_from.startswith('+'):
                        whatsapp_from = f"+{whatsapp_from}"
                    from_number = f"whatsapp:{whatsapp_from}"
                else:
                    # Use Twilio sandbox number if no WhatsApp number configured
                    from_number = "whatsapp:+14155238886"  # Twilio Sandbox number
                
                print(f"Sending WhatsApp from {from_number} to {to_number}")
                
                # Create WhatsApp message (with whatsapp: prefix)
                message = client.messages.create(
                    from_=from_number,
                    body=body,
                    to=to_number  # WhatsApp format with whatsapp: prefix
                )
                
                message_sids.append(message.sid)
                print(f"WhatsApp sent to {clean_number}, SID: {message.sid}")
                
            except Exception as e:
                print(f"Failed to send WhatsApp to {number}: {str(e)}")

        return message_sids if message_sids else False
        
    except AutomationRule.DoesNotExist:
        print(f"Automation rule with ID {rule_id} not found")
        return False
    except Exception as e:
        print(f"Error sending WhatsApp for rule {rule_id}: {str(e)}")
        return False