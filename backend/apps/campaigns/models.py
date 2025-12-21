from django.db import models
from django.contrib.auth.models import User


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=100)
    template = models.ForeignKey('templates.EmailTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class CampaignContact(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_contacts')
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE)
    sent = models.BooleanField(default=False)
    opened = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    bounced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['campaign', 'contact']
    
    def __str__(self):
        return f"{self.campaign.name} - {self.contact.email}"
