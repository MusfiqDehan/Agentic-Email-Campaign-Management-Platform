"""
Views for Campaign, Contact, and ContactList management.
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.db.models.functions import TruncHour, TruncDay
from django.utils import timezone

from ..models import Campaign, Contact, ContactList, EmailDeliveryLog
from ..serializers import (
    CampaignSerializer,
    CampaignListSerializer,
    CampaignPreviewSerializer,
    CampaignTestSendSerializer,
    CampaignDuplicateSerializer,
    CampaignScheduleSerializer,
    ContactSerializer,
    ContactMinimalSerializer,
    ContactListSerializer,
    ContactListSummarySerializer,
    BulkContactCreateSerializer,
    UnsubscribeSerializer,
    GDPRForgetSerializer,
)
from utils.throttles import OrganizationRateThrottle, EmailSendingRateThrottle


class ContactListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing contact lists.
    
    Endpoints:
    - GET /contacts/lists/ - List all contact lists
    - POST /contacts/lists/ - Create a new contact list
    - GET /contacts/lists/{id}/ - Get contact list details
    - PUT /contacts/lists/{id}/ - Update contact list
    - DELETE /contacts/lists/{id}/ - Delete contact list (soft delete)
    - POST /contacts/lists/{id}/refresh-stats/ - Refresh list statistics
    """
    
    serializer_class = ContactListSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_queryset(self):
        return ContactList.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def refresh_stats(self, request, pk=None):
        """Refresh contact list statistics."""
        contact_list = self.get_object()
        contact_list.update_stats()
        return Response({
            'total_contacts': contact_list.total_contacts,
            'active_contacts': contact_list.active_contacts,
            'unsubscribed_contacts': contact_list.unsubscribed_contacts,
            'bounced_contacts': contact_list.bounced_contacts,
        })


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing contacts.
    
    Endpoints:
    - GET /contacts/ - List all contacts
    - POST /contacts/ - Create a new contact
    - POST /contacts/bulk/ - Bulk import contacts (CSV/JSON)
    - GET /contacts/{id}/ - Get contact details
    - PUT /contacts/{id}/ - Update contact
    - DELETE /contacts/{id}/ - Delete contact (soft delete)
    """
    
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_queryset(self):
        queryset = Contact.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).select_related('organization').prefetch_related('lists')
        
        # Filter by list
        list_id = self.request.query_params.get('list')
        if list_id:
            queryset = queryset.filter(lists__id=list_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by tag
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        
        # Search by email or name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContactMinimalSerializer
        return ContactSerializer
    
    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Bulk import contacts from CSV or JSON."""
        serializer = BulkContactCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response(result, status=status.HTTP_201_CREATED)


class CampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing email campaigns.
    
    Endpoints:
    - GET /campaigns/ - List all campaigns
    - POST /campaigns/ - Create a new campaign
    - GET /campaigns/{id}/ - Get campaign details
    - PUT /campaigns/{id}/ - Update campaign
    - DELETE /campaigns/{id}/ - Delete campaign (soft delete)
    - POST /campaigns/{id}/launch/ - Launch campaign immediately
    - POST /campaigns/{id}/schedule/ - Schedule campaign
    - POST /campaigns/{id}/pause/ - Pause sending campaign
    - POST /campaigns/{id}/resume/ - Resume paused campaign
    - POST /campaigns/{id}/cancel/ - Cancel campaign
    - GET /campaigns/{id}/preview/ - Preview campaign email
    - POST /campaigns/{id}/test-send/ - Send test email
    - POST /campaigns/{id}/duplicate/ - Duplicate campaign
    - GET /campaigns/{id}/analytics/ - Get campaign analytics
    """
    
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_queryset(self):
        queryset = Campaign.objects.filter(
            organization=self.request.user.organization,
            is_deleted=False
        ).select_related(
            'organization', 'email_template', 'email_provider'
        ).prefetch_related('contact_lists')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by tag
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignListSerializer
        return CampaignSerializer
    
    @action(detail=True, methods=['post'], throttle_classes=[EmailSendingRateThrottle])
    def launch(self, request, pk=None):
        """Launch campaign immediately."""
        campaign = self.get_object()
        
        try:
            campaign.launch()
            return Response({
                'message': 'Campaign launched successfully',
                'status': campaign.status,
                'total_recipients': campaign.stats_total_recipients
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule campaign for future send."""
        campaign = self.get_object()
        
        if campaign.status not in ['DRAFT']:
            return Response(
                {'error': f'Cannot schedule campaign with status {campaign.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CampaignScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        campaign.scheduled_at = serializer.validated_data['scheduled_at']
        campaign.status = 'SCHEDULED'
        campaign.calculate_total_recipients()
        campaign.save()
        
        return Response({
            'message': 'Campaign scheduled successfully',
            'scheduled_at': campaign.scheduled_at,
            'total_recipients': campaign.stats_total_recipients
        })
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause sending campaign."""
        campaign = self.get_object()
        
        try:
            campaign.pause()
            return Response({'message': 'Campaign paused', 'status': campaign.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume paused campaign."""
        campaign = self.get_object()
        
        try:
            campaign.resume()
            return Response({'message': 'Campaign resumed', 'status': campaign.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel campaign."""
        campaign = self.get_object()
        
        try:
            campaign.cancel()
            return Response({'message': 'Campaign cancelled', 'status': campaign.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post'])
    def preview(self, request, pk=None):
        """Preview campaign email."""
        campaign = self.get_object()
        
        contact = None
        if request.method == 'POST':
            serializer = CampaignPreviewSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            contact_id = serializer.validated_data.get('contact_id')
            if contact_id:
                contact = Contact.objects.filter(id=contact_id).first()
        
        preview = campaign.preview(contact)
        return Response(preview)
    
    @action(detail=True, methods=['post'], throttle_classes=[EmailSendingRateThrottle])
    def test_send(self, request, pk=None):
        """Send test email."""
        campaign = self.get_object()
        
        serializer = CampaignTestSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact = None
        contact_id = serializer.validated_data.get('contact_id')
        if contact_id:
            contact = Contact.objects.filter(
                id=contact_id,
                organization=request.user.organization
            ).first()
        
        results = campaign.send_test(
            test_emails=serializer.validated_data['test_emails'],
            contact=contact
        )
        
        return Response({
            'message': f"Test emails queued for {len(results)} recipients",
            'results': results
        })
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate campaign."""
        campaign = self.get_object()
        
        serializer = CampaignDuplicateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_campaign = campaign.duplicate(
            new_name=serializer.validated_data.get('new_name')
        )
        
        return Response(
            CampaignSerializer(new_campaign, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get campaign analytics with time series data."""
        campaign = self.get_object()
        
        period = request.query_params.get('period', 'day')
        
        # Choose truncation based on period
        if period == 'hour':
            trunc_func = TruncHour
        else:
            trunc_func = TruncDay
        
        # Get time series data
        timeline = EmailDeliveryLog.objects.filter(
            campaign=campaign
        ).annotate(
            period=trunc_func('sent_at')
        ).values('period').annotate(
            sent=Count('id', filter=Q(delivery_status__in=['SENT', 'DELIVERED', 'OPENED', 'CLICKED'])),
            delivered=Count('id', filter=Q(delivery_status__in=['DELIVERED', 'OPENED', 'CLICKED'])),
            opened=Count('id', filter=Q(opened_at__isnull=False)),
            clicked=Count('id', filter=Q(clicked_at__isnull=False)),
            bounced=Count('id', filter=Q(delivery_status='BOUNCED')),
        ).order_by('period')
        
        return Response({
            'campaign_id': str(campaign.id),
            'campaign_name': campaign.name,
            'period': period,
            'timeline': list(timeline),
            'totals': {
                'total_recipients': campaign.stats_total_recipients,
                'sent': campaign.stats_sent,
                'delivered': campaign.stats_delivered,
                'opened': campaign.stats_opened,
                'clicked': campaign.stats_clicked,
                'bounced': campaign.stats_bounced,
                'complained': campaign.stats_complained,
                'unsubscribed': campaign.stats_unsubscribed,
                'open_rate': campaign.open_rate,
                'click_rate': campaign.click_rate,
                'bounce_rate': campaign.bounce_rate,
                'delivery_rate': campaign.delivery_rate,
            }
        })
    
    @action(detail=True, methods=['post'])
    def refresh_stats(self, request, pk=None):
        """Refresh campaign statistics from delivery logs."""
        campaign = self.get_object()
        campaign.update_stats_from_logs()
        
        return Response({
            'stats_sent': campaign.stats_sent,
            'stats_delivered': campaign.stats_delivered,
            'stats_opened': campaign.stats_opened,
            'stats_clicked': campaign.stats_clicked,
            'stats_bounced': campaign.stats_bounced,
            'stats_unique_opens': campaign.stats_unique_opens,
            'stats_unique_clicks': campaign.stats_unique_clicks,
            'stats_updated_at': campaign.stats_updated_at,
        })


class UnsubscribeView(generics.GenericAPIView):
    """
    Public endpoint for unsubscribing contacts.
    
    POST /unsubscribe/
    """
    
    permission_classes = []  # Public endpoint
    serializer_class = UnsubscribeSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        reason = serializer.validated_data.get('reason', '')
        
        contact = Contact.objects.get(unsubscribe_token=token)
        contact.unsubscribe(reason)
        
        return Response({
            'message': 'Successfully unsubscribed',
            'email': contact.email
        })
    
    def get(self, request):
        """Handle GET requests for unsubscribe links."""
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'error': 'Token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contact = Contact.objects.filter(unsubscribe_token=token).first()
        if not contact:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if contact.status == 'UNSUBSCRIBED':
            return Response({'message': 'Already unsubscribed', 'email': contact.email})
        
        # Return confirmation page data
        return Response({
            'email': contact.email,
            'status': contact.status,
            'confirm_url': f'/api/campaigns/unsubscribe/?token={token}'
        })


class GDPRForgetView(generics.GenericAPIView):
    """
    GDPR forget endpoint for anonymizing contact data.
    
    POST /gdpr/forget/
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = GDPRForgetSerializer
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        contact = Contact.objects.filter(
            organization=request.user.organization,
            email__iexact=email
        ).first()
        
        if not contact:
            return Response(
                {'error': 'Contact not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        contact.forget()
        
        return Response({
            'message': 'Contact data has been anonymized',
            'gdpr_compliant': True
        })
