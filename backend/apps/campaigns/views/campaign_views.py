"""
Views for Campaign, Contact, and ContactList management.

All views use APIView for explicit control over request handling.
"""
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Sum, Avg
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
    PublicSubscribeSerializer,
)
from drf_spectacular.utils import extend_schema
from apps.utils.throttles import OrganizationRateThrottle, EmailSendingRateThrottle, PublicSubscriptionThrottle
from apps.utils.view_mixins import PublicCORSMixin


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


class OrganizationStatsView(APIView):
    """
    Get organization-wide dashboard statistics.
    
    GET /org/stats/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]

    def get(self, request):
        organization = request.user.organization
        if not organization:
            return Response({"error": "No organization found for user"}, status=status.HTTP_400_BAD_REQUEST)

        # Basic Stats
        total_campaigns = Campaign.objects.filter(organization=organization, is_deleted=False).count()
        total_contacts = Contact.objects.filter(organization=organization, is_deleted=False).count()
        
        # Aggregate email stats across all campaigns
        email_stats = Campaign.objects.filter(organization=organization, is_deleted=False).aggregate(
            sent=Sum('stats_sent'),
            delivered=Sum('stats_delivered'),
            opened=Sum('stats_opened'),
            clicked=Sum('stats_clicked')
        )
        
        sent_count = email_stats.get('sent') or 0
        opened_count = email_stats.get('opened') or 0
        open_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0

        # Recent Campaigns
        recent_campaigns = Campaign.objects.filter(
            organization=organization, is_deleted=False
        ).order_by('-created_at')[:5]
        
        campaigns_data = CampaignListSerializer(recent_campaigns, many=True, context={'request': request}).data

        # Recent Delivery Logs
        recent_logs = EmailDeliveryLog.objects.filter(
            organization=organization
        ).select_related('campaign', 'contact').order_by('-sent_at')[:10]
        
        logs_data = []
        for log in recent_logs:
            logs_data.append({
                "id": str(log.id),
                "recipient": log.recipient_email,
                "status": log.delivery_status,
                "subject": log.subject,
                "campaign_name": log.campaign.name if log.campaign else "N/A",
                "sent_at": log.sent_at
            })

        return Response({
            "total_campaigns": total_campaigns,
            "total_contacts": total_contacts,
            "emails_sent": sent_count,
            "open_rate": round(open_rate, 1),
            "recent_campaigns": campaigns_data,
            "recent_activity": logs_data
        })


@extend_schema(request=BulkContactCreateSerializer)
class ContactBulkImportView(APIView):
    """
    Bulk import contacts from CSV or JSON.
    
    POST /contacts/bulk/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
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
        # Ensure user has an organization
        if not request.user.organization:
            return Response(
                {'error': 'User is not associated with any organization.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Detailed campaign lookup with specific error messages
        # First, check if campaign exists at all (including soft-deleted)
        campaign = Campaign.all_objects.filter(pk=pk).first()
        
        if not campaign:
            return Response(
                {'error': f'Campaign with ID {pk} does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if campaign.is_deleted:
            return Response(
                {'error': 'This campaign has been deleted.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if campaign.organization_id != request.user.organization_id:
            return Response(
                {'error': 'You do not have permission to access this campaign.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Provide helpful error messages based on current status
        if campaign.status == 'SENDING':
            return Response(
                {'error': 'Campaign is already sending. Use /pause/ to pause or /cancel/ to stop it.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif campaign.status == 'SENT':
            return Response(
                {'error': 'Campaign has already been sent. Use /duplicate/ to create a copy and send again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif campaign.status == 'CANCELLED':
            return Response(
                {'error': 'Campaign was cancelled. Use /duplicate/ to create a copy and send again.'},
                status=status.HTTP_400_BAD_REQUEST
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
        # Ensure user has an organization
        if not request.user.organization:
            return Response(
                {'error': 'User is not associated with any organization.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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
        # Ensure user has an organization
        if not request.user.organization:
            return Response(
                {'error': 'User is not associated with any organization.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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
        # Ensure user has an organization
        if not request.user.organization:
            return Response(
                {'error': 'User is not associated with any organization.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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
        # Ensure user has an organization
        if not request.user.organization:
            return Response(
                {'error': 'User is not associated with any organization.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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


class CampaignResetView(APIView):
    """
    Reset a stuck campaign back to DRAFT status.
    
    POST /campaigns/{id}/reset/
    
    Use this when a campaign is stuck in SENDING status 
    (e.g., Celery task failed or server restarted).
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrganizationRateThrottle]
    
    def post(self, request, pk):
        """Reset campaign to DRAFT status."""
        # Ensure user has an organization
        if not request.user.organization:
            return Response(
                {'error': 'User is not associated with any organization.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        campaign = get_object_or_404(
            Campaign,
            pk=pk,
            organization=request.user.organization,
            is_deleted=False
        )
        
        if campaign.status in ['SENT']:
            return Response(
                {'error': 'Cannot reset a completed campaign. Use /duplicate/ instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset to draft
        old_status = campaign.status
        campaign.status = 'DRAFT'
        campaign.started_at = None
        campaign.scheduled_at = None
        campaign.save(update_fields=['status', 'started_at', 'scheduled_at'])
        
        return Response({
            'message': f'Campaign reset from {old_status} to DRAFT',
            'status': campaign.status,
            'previous_status': old_status
        })


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
            'confirm_url': f'/campaigns/unsubscribe/?token={token}'
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


class PublicContactSubscribeView(PublicCORSMixin, APIView):
    """
    Public endpoint for contact subscription via signup forms.
    
    This endpoint allows unauthenticated users to subscribe to a contact list
    by providing their email and optional information.
    
    Features:
    - No authentication required (public endpoint)
    - Honeypot spam protection (website field)
    - Rate limiting per IP
    - CORS enabled for cross-origin form submissions
    - Double opt-in support (based on list configuration)
    
    POST /public/subscribe/
    
    Request body:
    {
        "list_token": "abc123...",  # Required - identifies the contact list
        "email": "user@example.com",  # Required
        "first_name": "John",  # Optional
        "last_name": "Doe",  # Optional
        "phone": "+1234567890",  # Optional
        "custom_fields": {"company": "Acme"},  # Optional
        "website": ""  # Honeypot - must be empty
    }
    """
    permission_classes = []  # Public endpoint - no authentication
    throttle_classes = [PublicSubscriptionThrottle]
    
    def post(self, request):
        """Subscribe a contact to a list via public form."""
        serializer = PublicSubscribeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check honeypot - if filled, return fake success to fool bots
        if serializer.validated_data.get('_is_bot', False):
            return Response({
                'message': 'Successfully subscribed',
                'status': 'subscribed'
            }, status=status.HTTP_200_OK)
        
        # Get the contact list by subscription token
        list_token = serializer.validated_data['list_token']
        contact_list = ContactList.objects.filter(
            subscription_token=list_token,
            is_active=True,
            is_deleted=False
        ).first()
        
        if not contact_list:
            return Response(
                {'error': 'Invalid or inactive list'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        email = serializer.validated_data['email']
        organization = contact_list.organization
        
        # Determine status based on double opt-in setting
        contact_status = 'PENDING' if contact_list.double_opt_in else 'ACTIVE'
        
        # Create or update contact
        contact, created = Contact.objects.get_or_create(
            organization=organization,
            email__iexact=email,
            defaults={
                'email': email,
                'first_name': serializer.validated_data.get('first_name', ''),
                'last_name': serializer.validated_data.get('last_name', ''),
                'phone': serializer.validated_data.get('phone', ''),
                'custom_fields': serializer.validated_data.get('custom_fields', {}),
                'source': 'SIGNUP_FORM',
                'status': contact_status,
            }
        )
        
        # If contact already exists, update optional fields if provided
        if not created:
            updated = False
            if serializer.validated_data.get('first_name') and not contact.first_name:
                contact.first_name = serializer.validated_data['first_name']
                updated = True
            if serializer.validated_data.get('last_name') and not contact.last_name:
                contact.last_name = serializer.validated_data['last_name']
                updated = True
            if serializer.validated_data.get('phone') and not contact.phone:
                contact.phone = serializer.validated_data['phone']
                updated = True
            if serializer.validated_data.get('custom_fields'):
                contact.custom_fields.update(serializer.validated_data['custom_fields'])
                updated = True
            if updated:
                contact.save()
        
        # Add contact to the list (many-to-many)
        contact.lists.add(contact_list)
        
        # Update list statistics
        contact_list.update_stats()
        
        # Response message based on double opt-in
        if contact_list.double_opt_in and created:
            message = 'Please check your email to confirm subscription'
            sub_status = 'pending_confirmation'
        elif not created:
            message = 'Contact updated and added to list'
            sub_status = 'updated'
        else:
            message = 'Successfully subscribed'
            sub_status = 'subscribed'
        
        return Response({
            'message': message,
            'status': sub_status,
            'double_opt_in': contact_list.double_opt_in
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
