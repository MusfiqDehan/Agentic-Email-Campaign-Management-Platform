from django.db import models
from apps.utils.base_models import BaseModel


class Email_setupBaseModel(BaseModel):
    """
    Base model for email_setup app with common fields.
    """
    
    class Meta:
        abstract = True
