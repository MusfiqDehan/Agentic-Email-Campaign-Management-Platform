"""
Admin views for platform administrators.

These endpoints are for platform-level operations like managing shared providers.
All views use APIView for explicit control over request handling.
"""
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Avg
from django.utils import timezone

from ..models import EmailProvider, OrganizationEmailConfiguration
from ..serializers import EmailProviderSerializer


class IsPlatformAdmin(IsAdminUser):
    """
    Permission class for platform administrators.
    
    Platform admins can manage shared providers and view all organizations.
    Checks is_platform_admin field on User model (not is_staff).
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'is_platform_admin', False)
        )


# =============================================================================
# ADMIN EMAIL PROVIDER VIEWS
# =============================================================================

class AdminEmailProviderListCreateView(APIView):
    """
    List all providers or create a new shared provider.
    
    GET /admin/providers/
    POST /admin/providers/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self, request):
        """Return shared providers or all providers for superusers."""
        queryset = EmailProvider.objects.filter(is_deleted=False)
        
        # Filter to shared providers only unless superuser
        if not request.user.is_superuser:
            queryset = queryset.filter(is_shared=True)
        
        # Filter by type
        provider_type = request.query_params.get('type')
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        
        # Filter by health status
        health = request.query_params.get('health')
        if health:
            queryset = queryset.filter(health_status=health)
        
        return queryset.order_by('priority', 'name')
    
    def get(self, request):
        """List all providers."""
        providers = self.get_queryset(request)
        serializer = EmailProviderSerializer(providers, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a shared provider."""
        serializer = EmailProviderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                is_shared=True,
                organization=None  # Shared providers have no organization
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminEmailProviderDetailView(APIView):
    """
    Retrieve, update or delete a provider.
    
    GET /admin/providers/{id}/
    PUT /admin/providers/{id}/
    PATCH /admin/providers/{id}/
    DELETE /admin/providers/{id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        queryset = EmailProvider.objects.filter(is_deleted=False)
        if not user.is_superuser:
            queryset = queryset.filter(is_shared=True)
        return get_object_or_404(queryset, pk=pk)
    
    def get(self, request, pk):
        """Retrieve a provider."""
        provider = self.get_object(pk, request.user)
        serializer = EmailProviderSerializer(provider)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Update a provider."""
        provider = self.get_object(pk, request.user)
        serializer = EmailProviderSerializer(provider, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """Partially update a provider."""
        provider = self.get_object(pk, request.user)
        serializer = EmailProviderSerializer(provider, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Soft delete a provider."""
        provider = self.get_object(pk, request.user)
        provider.is_deleted = True
        provider.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminEmailProviderSetDefaultView(APIView):
    """
    Set provider as default shared provider.
    
    POST /admin/providers/{id}/set-default/
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        """Set provider as default shared provider."""
        provider = get_object_or_404(
            EmailProvider,
            pk=pk,
            is_deleted=False,
            is_shared=True
        )
        
        provider.is_default = True
        provider.save()
        
        return Response({
            'message': f'{provider.name} is now the default shared provider',
            'provider_id': str(provider.id)
        })


class AdminEmailProviderHealthCheckView(APIView):
    """
    Run health check on provider.
    
    POST /admin/providers/{id}/health-check/
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        """Run health check on provider."""
        queryset = EmailProvider.objects.filter(is_deleted=False)
        if not request.user.is_superuser:
            queryset = queryset.filter(is_shared=True)
        
        provider = get_object_or_404(queryset, pk=pk)
        
        # TODO: Implement actual health check logic
        provider.last_health_check = timezone.now()
        provider.health_status = 'HEALTHY'
        provider.save()
        
        return Response({
            'provider_id': str(provider.id),
            'provider_name': provider.name,
            'health_status': provider.health_status,
            'last_health_check': provider.last_health_check
        })


class AdminEmailProviderTestSendView(APIView):
    """
    Send a test email using this provider.
    
    POST /admin/providers/{id}/test-send/
    Body: {"email": "test@example.com"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Send a test email using this provider."""
        from django.core.mail import EmailMultiAlternatives
        from ..backends import DynamicEmailBackend
        import logging
        
        logger = logging.getLogger(__name__)
        
        queryset = EmailProvider.objects.filter(is_deleted=False)
        if not request.user.is_superuser:
            queryset = queryset.filter(is_shared=True)
        
        provider = get_object_or_404(queryset, pk=pk)
        
        test_email = request.data.get('email')
        if not test_email:
            return Response(
                {'error': 'email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if provider can send emails
        can_send, reason = provider.can_send_email()
        if not can_send:
            return Response(
                {'error': f'Provider cannot send emails: {reason}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decrypt provider configuration
        try:
            config = provider.decrypt_config()
        except Exception as e:
            logger.error(f"Failed to decrypt provider config: {str(e)}")
            return Response(
                {'error': 'Failed to decrypt provider configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Build email connection using the provider
        try:
            connection, metadata = DynamicEmailBackend.build_provider_connection(
                provider_type=provider.provider_type,
                config=config,
                fail_silently=False
            )
            
            from_email = metadata.get('from_email') or config.get('from_email', 'noreply@example.com')
            
            # Create test email
            subject = f'Test Email from {provider.name}'
            text_content = f"""
This is a test email from the Email Campaign Management Platform.

Provider Details:
- Name: {provider.name}
- Type: {provider.provider_type}
- Health Status: {provider.health_status}

If you received this email, the provider is working correctly!

Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
            
            html_content = f"""
<html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
            .details {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #4CAF50; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            .success {{ color: #4CAF50; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>✓ Test Email Successful</h2>
            </div>
            <div class="content">
                <p class="success">This is a test email from the Email Campaign Management Platform.</p>
                
                <div class="details">
                    <h3>Provider Details:</h3>
                    <ul>
                        <li><strong>Name:</strong> {provider.name}</li>
                        <li><strong>Type:</strong> {provider.provider_type}</li>
                        <li><strong>Health Status:</strong> {provider.health_status}</li>
                    </ul>
                </div>
                
                <p>If you received this email, the provider is configured correctly and working as expected!</p>
                
                <div class="footer">
                    <p>Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p><small>Email Campaign Management Platform</small></p>
                </div>
            </div>
        </div>
    </body>
</html>
"""
            
            # Create and send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[test_email],
                connection=connection
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send the email
            email.send()
            
            # Update provider stats
            provider.last_used_at = timezone.now()
            provider.emails_sent_today += 1
            provider.emails_sent_this_hour += 1
            provider.health_status = 'HEALTHY'
            provider.last_health_check = timezone.now()
            provider.save(update_fields=[
                'last_used_at', 
                'emails_sent_today', 
                'emails_sent_this_hour',
                'health_status',
                'last_health_check'
            ])
            
            logger.info(f"Test email sent successfully via {provider.name} to {test_email}")
            
            return Response({
                'success': True,
                'message': f'Test email sent successfully to {test_email}',
                'provider': provider.name,
                'provider_type': provider.provider_type,
                'sent_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send test email via {provider.name}: {str(e)}")
            
            # Update provider health status
            provider.health_status = 'UNHEALTHY'
            provider.health_details = str(e)
            provider.last_health_check = timezone.now()
            provider.save(update_fields=['health_status', 'health_details', 'last_health_check'])
            
            return Response(
                {
                    'error': f'Failed to send test email: {str(e)}',
                    'provider': provider.name,
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# ADMIN ORGANIZATION CONFIG VIEWS
# =============================================================================

class AdminOrganizationConfigListView(APIView):
    """
    List all organization configurations.
    
    GET /admin/organizations/
    """
    permission_classes = [IsPlatformAdmin]
    
    def get(self, request):
        """List all organization configurations."""
        configs = OrganizationEmailConfiguration.objects.filter(
            is_deleted=False
        ).select_related('organization')
        
        from ..serializers import OrganizationEmailConfigurationSerializer
        serializer = OrganizationEmailConfigurationSerializer(configs, many=True)
        return Response(serializer.data)


class AdminOrganizationConfigDetailView(APIView):
    """
    Retrieve organization configuration details.
    
    GET /admin/organizations/{id}/
    """
    permission_classes = [IsPlatformAdmin]
    
    def get(self, request, pk):
        """Retrieve organization configuration."""
        config = get_object_or_404(
            OrganizationEmailConfiguration,
            pk=pk,
            is_deleted=False
        )
        
        from ..serializers import OrganizationEmailConfigurationSerializer
        serializer = OrganizationEmailConfigurationSerializer(config)
        return Response(serializer.data)


class AdminOrganizationSuspendView(APIView):
    """
    Suspend an organization's email service.
    
    POST /admin/organizations/{id}/suspend/
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        """Suspend an organization's email service."""
        config = get_object_or_404(
            OrganizationEmailConfiguration,
            pk=pk,
            is_deleted=False
        )
        
        reason = request.data.get('reason', 'Suspended by platform admin')
        
        config.is_suspended = True
        config.suspension_reason = reason
        config.suspended_at = timezone.now()
        config.save()
        
        return Response({
            'message': f'Organization {config.organization.name} has been suspended',
            'reason': reason
        })


class AdminOrganizationUnsuspendView(APIView):
    """
    Unsuspend an organization's email service.
    
    POST /admin/organizations/{id}/unsuspend/
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        """Unsuspend an organization's email service."""
        config = get_object_or_404(
            OrganizationEmailConfiguration,
            pk=pk,
            is_deleted=False
        )
        
        config.is_suspended = False
        config.suspension_reason = ''
        config.suspended_at = None
        config.save()
        
        return Response({
            'message': f'Organization {config.organization.name} has been unsuspended'
        })


class AdminOrganizationUpgradePlanView(APIView):
    """
    Upgrade an organization's plan.
    
    POST /admin/organizations/{id}/upgrade-plan/
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        """Upgrade an organization's plan."""
        config = get_object_or_404(
            OrganizationEmailConfiguration,
            pk=pk,
            is_deleted=False
        )
        
        new_plan = request.data.get('plan_type')
        if not new_plan:
            return Response(
                {'error': 'plan_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_plans = ['FREE', 'BASIC', 'PROFESSIONAL', 'ENTERPRISE']
        if new_plan.upper() not in valid_plans:
            return Response(
                {'error': f'Invalid plan. Must be one of: {valid_plans}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_plan = config.plan_type
        config.plan_type = new_plan.upper()
        config.save()  # This will auto-sync plan limits
        
        return Response({
            'message': f'Organization {config.organization.name} upgraded from {old_plan} to {config.plan_type}',
            'new_limits': config.plan_limits
        })


class AdminPlatformStatsView(APIView):
    """
    Get platform-wide statistics.
    
    GET /admin/stats/
    """
    permission_classes = [IsPlatformAdmin]
    
    def get(self, request):
        """Get platform-wide statistics."""
        configs = OrganizationEmailConfiguration.objects.filter(is_deleted=False)
        
        stats = configs.aggregate(
            total_orgs=Count('id'),
            total_emails_today=Sum('emails_sent_today'),
            total_emails_month=Sum('emails_sent_this_month'),
            avg_bounce_rate=Avg('bounce_rate'),
            avg_complaint_rate=Avg('complaint_rate'),
        )
        
        plan_breakdown = configs.values('plan_type').annotate(
            count=Count('id')
        ).order_by('plan_type')
        
        suspended_count = configs.filter(is_suspended=True).count()
        
        return Response({
            'total_organizations': stats['total_orgs'],
            'total_emails_today': stats['total_emails_today'] or 0,
            'total_emails_this_month': stats['total_emails_month'] or 0,
            'average_bounce_rate': round(stats['avg_bounce_rate'] or 0, 2),
            'average_complaint_rate': round(stats['avg_complaint_rate'] or 0, 4),
            'suspended_organizations': suspended_count,
            'plan_breakdown': list(plan_breakdown)
        })
