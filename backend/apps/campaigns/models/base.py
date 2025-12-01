from django.db import models
from apps.utils.base_models import BaseModel


class CampaignsBaseModel(BaseModel):
    """
    Base model for campaigns app with common fields.
    """
    
    class Meta:
        abstract = True
