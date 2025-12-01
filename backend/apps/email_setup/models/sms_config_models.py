from django.db import models
import uuid

from core import BaseModel

class SMSConfigurationModel(BaseModel):
    """
    Model for storing configuration settings related to SMS and WhatsApp providers.

    Attributes:
        name_or_type (str): A unique name or type identifier for the SMS/WhatsApp configuration.
        endpoint_url (str): The URL of the SMS provider's API endpoint.
        account_ssid (str): The account SID for the SMS provider.
        auth_token (str): The authentication token for the SMS provider.
        verified_service_id (str): The verified service ID for the SMS provider.
        default_from_number (str): Default phone number for SMS.
        whatsapp_from_number (str): WhatsApp Business phone number.
        whatsapp_enabled (bool): Whether WhatsApp is enabled for this configuration.
    Meta:
        verbose_name_plural (str): The plural name for the model in the admin interface.

    Methods:
        __str__(): Returns a string representation of the object.
        save(*args, **kwargs): Overrides the save method to encrypt the API token before saving.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_or_type = models.CharField(max_length=255, unique=True, null=True, blank=True)
    tenant_id = models.UUIDField(blank=True, null=True, help_text="Tenant-specific configuration if set.")
    endpoint_url = models.CharField(max_length=255, null=True, blank=True)
    
    # Twilio-specific fields
    account_ssid = models.CharField(max_length=255, null=True, blank=True)
    auth_token = models.CharField(max_length=255, null=True, blank=True)
    verified_service_id = models.CharField(max_length=255, null=True, blank=True)
    default_from_number = models.CharField(max_length=20, null=True, blank=True, 
                                          help_text="Twilio phone number to use as sender (e.g. +15551234567)")
    
    # WhatsApp-specific fields
    whatsapp_from_number = models.CharField(max_length=20, null=True, blank=True,
                                          help_text="WhatsApp Business number (e.g. whatsapp:+15551234567)")
    whatsapp_enabled = models.BooleanField(default=False, 
                                         help_text="Enable WhatsApp messaging for this configuration")

    class Meta:
        verbose_name_plural = "SMS/WhatsApp Configurations"

    def __str__(self):
        """
        Returns a string representation of the object.

        Returns:
            str: The string representation of the object containing id, name_or_type, endpoint_url, and account_ssid.
        """
        return f"{self.id}-{self.name_or_type}-{self.endpoint_url}-{self.account_ssid}"
    

class SMSTemplate(BaseModel):
    """
    Stores SMS and WhatsApp templates with dynamic variables.

    Attributes:
        template_name (str): Unique name for the SMS template.
        sms_body (str): The body of the SMS message, can include dynamic variables like {{variable_name}}.
        recipient_numbers_list (str): Comma-separated list of recipient phone numbers.
        supports_whatsapp (bool): Whether this template can be used for WhatsApp messages.
    Meta:
        verbose_name_plural (str): The plural name for the model in the admin interface.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_name = models.CharField(max_length=255, unique=True)
    tenant_id = models.UUIDField(blank=True, null=True, help_text="Tenant-specific template if set.")
    sms_body = models.CharField(max_length=160, help_text="Use {{variable_name}} for dynamic content.")
    # Storing recipient_numbers as a comma-separated string for flexibility
    recipient_numbers_list = models.TextField(blank=True, help_text="Comma-separated phone numbers.")
    
    # WhatsApp-specific fields
    supports_whatsapp = models.BooleanField(default=True, 
                                          help_text="Whether this template can be used for WhatsApp")

    def __str__(self):
        return self.template_name