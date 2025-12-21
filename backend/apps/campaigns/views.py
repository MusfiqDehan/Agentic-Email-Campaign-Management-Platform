from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Campaign, CampaignContact
from .serializers import CampaignSerializer, CampaignContactSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    
    @action(detail=True, methods=['post'])
    def add_contacts(self, request, pk=None):
        campaign = self.get_object()
        contact_ids = request.data.get('contact_ids', [])
        
        created_count = 0
        for contact_id in contact_ids:
            _, created = CampaignContact.objects.get_or_create(
                campaign=campaign,
                contact_id=contact_id
            )
            if created:
                created_count += 1
        
        return Response({
            'message': f'{created_count} contacts added to campaign',
            'total_contacts': campaign.campaign_contacts.count()
        })
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        campaign = self.get_object()
        
        if campaign.status == 'sent':
            return Response(
                {'error': 'Campaign already sent'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would implement actual email sending logic
        # For now, we'll just mark it as sent
        campaign.status = 'sent'
        from django.utils import timezone
        campaign.sent_at = timezone.now()
        campaign.save()
        
        # Mark all contacts as sent
        campaign.campaign_contacts.update(sent=True)
        
        return Response({
            'message': 'Campaign sent successfully',
            'sent_count': campaign.campaign_contacts.count()
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        campaign = self.get_object()
        total = campaign.campaign_contacts.count()
        
        return Response({
            'total_contacts': total,
            'sent': campaign.campaign_contacts.filter(sent=True).count(),
            'opened': campaign.campaign_contacts.filter(opened=True).count(),
            'clicked': campaign.campaign_contacts.filter(clicked=True).count(),
            'bounced': campaign.campaign_contacts.filter(bounced=True).count(),
        })


class CampaignContactViewSet(viewsets.ModelViewSet):
    queryset = CampaignContact.objects.all()
    serializer_class = CampaignContactSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        campaign_id = self.request.query_params.get('campaign_id', None)
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        return queryset
