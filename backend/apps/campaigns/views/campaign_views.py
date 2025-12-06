"""
Views for Campaign, Contact, and ContactList management.

All views use APIView for explicit control over request handling.
"""
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.db.models.functions import TruncHour, TruncDay

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
from apps.utils.throttles import OrganizationRateThrottle, EmailSendingRateThrottle


# =============================================================================
# CONTACT LIST VIEWS
# =============================================================================

class ContactListListCreateView(APIView):
    """
    List all contact lists or create a new one.
    
    GET /contact-lists/
    POST /contact-lists/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get(self, request):
        """List all contact lists for the organization."""
        contact_lists = ContactList.objects.filter(
            organization=request.user.organization,
            is_deleted=False
        ).order_by('-created_at')
        
        serializer = ContactListSummarySerializer(contact_lists, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new contact list."""
        # Ensure user has an organization
        if not request.user.organization:
            return Response(
                {"error": "User must be associated with an organization."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ContactListSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(organization=request.user.organization)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContactListDetailView(APIView):
    """
    Retrieve, update or delete a contact list.
    
    GET /contact-lists/{id}/
    PUT /contact-lists/{id}/
    PATCH /contact-lists/{id}/
    DELETE /contact-lists/{id}/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_object(self, pk, user):
        return get_object_or_404(
            ContactList,
            pk=pk,
            organization=user.organization,
            is_deleted=False
        )
    
    def get(self, request, pk):
        """Retrieve a contact list."""
        contact_list = self.get_object(pk, request.user)
        serializer = ContactListSerializer(contact_list, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Update a contact list."""
        contact_list = self.get_object(pk, request.user)
        serializer = ContactListSerializer(contact_list, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """Partially update a contact list."""
        contact_list = self.get_object(pk, request.user)
        serializer = ContactListSerializer(contact_list, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Soft delete a contact list."""
        contact_list = self.get_object(pk, request.user)
        contact_list.is_deleted = True
        contact_list.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContactListRefreshStatsView(APIView):
    """
    Refresh contact list statistics.
    
    POST /contact-lists/{id}/refresh-stats/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Refresh contact list statistics."""
        contact_list = get_object_or_404(
            ContactList,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        contact_list.update_stats()
        return Response({
            'total_contacts': contact_list.total_contacts,
            'active_contacts': contact_list.active_contacts,
            'unsubscribed_contacts': contact_list.unsubscribed_contacts,
            'bounced_contacts': contact_list.bounced_contacts,
        })


# =============================================================================
# CONTACT VIEWS
# =============================================================================

class ContactListView(APIView):
    """
    List all contacts or create a new one.
    
    GET /contacts/
    POST /contacts/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_queryset(self, request):
        queryset = Contact.objects.filter(
            organization=request.user.organization,
            is_deleted=False
        ).select_related('organization').prefetch_related('lists')
        
        # Filter by list
        list_id = request.query_params.get('list')
        if list_id:
            queryset = queryset.filter(lists__id=list_id)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by tag
        tag = request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        
        # Search by email or name
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get(self, request):
        """List all contacts for the organization."""
        contacts = self.get_queryset(request)
        serializer = ContactMinimalSerializer(contacts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new contact."""
        serializer = ContactSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(organization=request.user.organization)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContactDetailView(APIView):
    """
    Retrieve, update or delete a contact.
    
    GET /contacts/{id}/
    PUT /contacts/{id}/
    PATCH /contacts/{id}/
    DELETE /contacts/{id}/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_object(self, pk, user):
        return get_object_or_404(
            Contact,
            pk=pk,
            organization=user.organization,
            is_deleted=False
        )
    
    def get(self, request, pk):
        """Retrieve a contact."""
        contact = self.get_object(pk, request.user)
        serializer = ContactSerializer(contact, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Update a contact."""
        contact = self.get_object(pk, request.user)
        serializer = ContactSerializer(contact, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """Partially update a contact."""
        contact = self.get_object(pk, request.user)
        serializer = ContactSerializer(contact, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Soft delete a contact."""
        contact = self.get_object(pk, request.user)
        contact.is_deleted = True
        contact.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContactBulkImportView(APIView):
    """
    Bulk import contacts from CSV or JSON.
    
    POST /contacts/bulk/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request):
        """Bulk import contacts from CSV or JSON."""
        serializer = BulkContactCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# CAMPAIGN VIEWS
# =============================================================================

class CampaignListCreateView(APIView):
    """
    List all campaigns or create a new one.
    
    GET /campaigns/
    POST /campaigns/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_queryset(self, request):
        queryset = Campaign.objects.filter(
            organization=request.user.organization,
            is_deleted=False
        ).select_related(
            'organization', 'email_template', 'email_provider'
        ).prefetch_related('contact_lists')
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by tag
        tag = request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        
        return queryset.order_by('-created_at')
    
    def get(self, request):
        """List all campaigns for the organization."""
        campaigns = self.get_queryset(request)
        serializer = CampaignListSerializer(campaigns, many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new campaign."""
        serializer = CampaignSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(organization=request.user.organization)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CampaignDetailView(APIView):
    """
    Retrieve, update or delete a campaign.
    
    GET /campaigns/{id}/
    PUT /campaigns/{id}/
    PATCH /campaigns/{id}/
    DELETE /campaigns/{id}/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get_object(self, pk, user):
        return get_object_or_404(
            Campaign,
            pk=pk,
            organization=user.organization,
            is_deleted=False
        )
    
    def get(self, request, pk):
        """Retrieve a campaign."""
        campaign = self.get_object(pk, request.user)
        serializer = CampaignSerializer(campaign, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Update a campaign."""
        campaign = self.get_object(pk, request.user)
        serializer = CampaignSerializer(campaign, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """Partially update a campaign."""
        campaign = self.get_object(pk, request.user)
        serializer = CampaignSerializer(campaign, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Soft delete a campaign."""
        campaign = self.get_object(pk, request.user)
        campaign.is_deleted = True
        campaign.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CampaignLaunchView(APIView):
    """
    Launch campaign immediately.
    
    POST /campaigns/{id}/launch/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailSendingRateThrottle]
    
    def post(self, request, pk):
        """Launch campaign immediately."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
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


class CampaignScheduleView(APIView):
    """
    Schedule campaign for future send.
    
    POST /campaigns/{id}/schedule/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Schedule campaign for future send."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        if campaign.status not in ['DRAFT']:
            return Response(
                {'error': f'Cannot schedule campaign with status {campaign.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CampaignScheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        campaign.scheduled_at = serializer.validated_data['scheduled_at']
        campaign.status = 'SCHEDULED'
        campaign.calculate_total_recipients()
        campaign.save()
        
        return Response({
            'message': 'Campaign scheduled successfully',
            'scheduled_at': campaign.scheduled_at,
            'total_recipients': campaign.stats_total_recipients
        })


class CampaignPauseView(APIView):
    """
    Pause sending campaign.
    
    POST /campaigns/{id}/pause/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Pause sending campaign."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        try:
            campaign.pause()
            return Response({'message': 'Campaign paused', 'status': campaign.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CampaignResumeView(APIView):
    """
    Resume paused campaign.
    
    POST /campaigns/{id}/resume/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Resume paused campaign."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        try:
            campaign.resume()
            return Response({'message': 'Campaign resumed', 'status': campaign.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CampaignCancelView(APIView):
    """
    Cancel campaign.
    
    POST /campaigns/{id}/cancel/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Cancel campaign."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        try:
            campaign.cancel()
            return Response({'message': 'Campaign cancelled', 'status': campaign.status})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CampaignPreviewView(APIView):
    """
    Preview campaign email.
    
    GET /campaigns/{id}/preview/
    POST /campaigns/{id}/preview/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get(self, request, pk):
        """Preview campaign email with default settings."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        preview = campaign.preview(None)
        return Response(preview)
    
    def post(self, request, pk):
        """Preview campaign email with specific contact."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        contact = None
        serializer = CampaignPreviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            contact_id = serializer.validated_data.get('contact_id')
            if contact_id:
                contact = Contact.objects.filter(id=contact_id).first()
        
        preview = campaign.preview(contact)
        return Response(preview)


class CampaignTestSendView(APIView):
    """
    Send test email.
    
    POST /campaigns/{id}/test-send/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailSendingRateThrottle]
    
    def post(self, request, pk):
        """Send test email."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        serializer = CampaignTestSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
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


class CampaignDuplicateView(APIView):
    """
    Duplicate campaign.
    
    POST /campaigns/{id}/duplicate/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Duplicate campaign."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        serializer = CampaignDuplicateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_campaign = campaign.duplicate(
            new_name=serializer.validated_data.get('new_name')
        )
        
        return Response(
            CampaignSerializer(new_campaign, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class CampaignAnalyticsView(APIView):
    """
    Get campaign analytics with time series data.
    
    GET /campaigns/{id}/analytics/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def get(self, request, pk):
        """Get campaign analytics with time series data."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
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


class CampaignRefreshStatsView(APIView):
    """
    Refresh campaign statistics from delivery logs.
    
    POST /campaigns/{id}/refresh-stats/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Refresh campaign statistics from delivery logs."""
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
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


# =============================================================================
# PUBLIC VIEWS
# =============================================================================

class UnsubscribeView(APIView):
    """
    Public endpoint for unsubscribing contacts.
    
    GET /unsubscribe/?token=xxx - Get unsubscribe confirmation page data
    POST /unsubscribe/ - Process unsubscription
    """
    permission_classes = []  # Public endpoint
    
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
    
    def post(self, request):
        """Process unsubscription."""
        serializer = UnsubscribeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['token']
        reason = serializer.validated_data.get('reason', '')
        
        contact = Contact.objects.filter(unsubscribe_token=token).first()
        if not contact:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        contact.unsubscribe(reason)
        
        return Response({
            'message': 'Successfully unsubscribed',
            'email': contact.email
        })


class GDPRForgetView(APIView):
    """
    GDPR forget endpoint for anonymizing contact data.
    
    POST /gdpr/forget/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request):
        """Anonymize contact data for GDPR compliance."""
        serializer = GDPRForgetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
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
