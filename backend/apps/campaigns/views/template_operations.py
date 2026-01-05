"""
Template operations views for duplication, versioning, approval, and testing.
"""
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.authentication.permissions import IsPlatformAdmin
from core import CustomResponseMixin

from ..models import (
    EmailTemplate, TemplateUsageLog, TemplateApprovalRequest,
    TemplateUpdateNotification, OrganizationTemplateNotification
)
from ..serializers import (
    EmailTemplateSerializer, TemplateUsageLogSerializer,
    TemplateApprovalRequestSerializer, TemplatePreviewSerializer
)
from ..utils.template_utils import (
    generate_unique_template_name, calculate_template_diff
)
from ..services.template_notification_service import (
    create_template_update_notification, create_approval_request_notification
)


class EmailTemplateUseView(CustomResponseMixin, APIView):
    """
    Duplicate a global template to user's organization.
    POST /campaigns/templates/<uuid>/use/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            # Get the source global template
            source_template = EmailTemplate.objects.get(
                id=pk,
                is_global=True,
                is_deleted=False,
                approval_status=EmailTemplate.ApprovalStatus.APPROVED
            )
        except EmailTemplate.DoesNotExist:
            raise NotFound("Global template not found or not approved")
        
        # Check user has an organization
        if not request.user.organization_id:
            raise ValidationError("You must belong to an organization to use templates")
        
        # Generate unique name for the duplicate
        unique_name = generate_unique_template_name(
            request.user.organization_id,
            source_template.template_name
        )
        
        # Create the duplicate with transaction
        with transaction.atomic():
            # Create new template
            new_template = EmailTemplate.objects.create(
                organization_id=request.user.organization_id,
                template_name=unique_name,
                category=source_template.category,
                email_subject=source_template.email_subject,
                preview_text=source_template.preview_text,
                email_body=source_template.email_body,
                text_body=source_template.text_body,
                description=source_template.description,
                tags=source_template.tags.copy() if source_template.tags else [],
                # Link to source
                is_global=False,
                source_template=source_template,
                duplicated_by=request.user,
                version=source_template.version,
                # Approved by default for organization templates
                approval_status=EmailTemplate.ApprovalStatus.APPROVED,
                is_draft=False,
            )
            
            # Create usage log
            TemplateUsageLog.objects.create(
                template=source_template,
                organization_id=request.user.organization_id,
                user=request.user,
                duplicated_template=new_template,
                template_name_at_duplication=source_template.template_name,
                template_version_at_duplication=source_template.version,
            )
            
            # Increment usage count
            source_template.usage_count += 1
            source_template.save(update_fields=['usage_count'])
        
        serializer = EmailTemplateSerializer(new_template)
        return Response({
            'message': 'Template duplicated successfully',
            'template': serializer.data,
            'redirect_url': f'/dashboard/templates/{new_template.id}/edit'
        }, status=status.HTTP_201_CREATED)


class EmailTemplateBulkUseView(CustomResponseMixin, APIView):
    """
    Duplicate multiple global templates at once.
    POST /campaigns/templates/bulk-use/
    Body: {"template_ids": ["uuid1", "uuid2"]}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        template_ids = request.data.get('template_ids', [])
        
        if not template_ids:
            raise ValidationError("template_ids is required")
        
        if not request.user.organization_id:
            raise ValidationError("You must belong to an organization")
        
        created_templates = []
        failed_templates = []
        
        for template_id in template_ids:
            try:
                with transaction.atomic():
                    source_template = EmailTemplate.objects.get(
                        id=template_id,
                        is_global=True,
                        is_deleted=False,
                        approval_status=EmailTemplate.ApprovalStatus.APPROVED
                    )
                    
                    unique_name = generate_unique_template_name(
                        request.user.organization_id,
                        source_template.template_name
                    )
                    
                    new_template = EmailTemplate.objects.create(
                        organization_id=request.user.organization_id,
                        template_name=unique_name,
                        category=source_template.category,
                        email_subject=source_template.email_subject,
                        preview_text=source_template.preview_text,
                        email_body=source_template.email_body,
                        text_body=source_template.text_body,
                        description=source_template.description,
                        tags=source_template.tags.copy() if source_template.tags else [],
                        is_global=False,
                        source_template=source_template,
                        duplicated_by=request.user,
                        version=source_template.version,
                        approval_status=EmailTemplate.ApprovalStatus.APPROVED,
                    )
                    
                    TemplateUsageLog.objects.create(
                        template=source_template,
                        organization_id=request.user.organization_id,
                        user=request.user,
                        duplicated_template=new_template,
                        template_name_at_duplication=source_template.template_name,
                        template_version_at_duplication=source_template.version,
                    )
                    
                    source_template.usage_count += 1
                    source_template.save(update_fields=['usage_count'])
                    
                    created_templates.append(EmailTemplateSerializer(new_template).data)
            
            except EmailTemplate.DoesNotExist:
                failed_templates.append({
                    'template_id': template_id,
                    'error': 'Template not found or not approved'
                })
            except Exception as e:
                failed_templates.append({
                    'template_id': template_id,
                    'error': str(e)
                })
        
        return Response({
            'message': f'Successfully duplicated {len(created_templates)} templates',
            'created': created_templates,
            'failed': failed_templates,
            'summary': {
                'total_requested': len(template_ids),
                'successful': len(created_templates),
                'failed': len(failed_templates)
            }
        })


class EmailTemplateVersionHistoryView(CustomResponseMixin, generics.ListAPIView):
    """
    Get version history for a template.
    GET /campaigns/templates/<uuid>/versions/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmailTemplateSerializer
    
    def get_queryset(self):
        template_id = self.kwargs.get('pk')
        
        try:
            template = EmailTemplate.objects.get(id=template_id, is_deleted=False)
        except EmailTemplate.DoesNotExist:
            raise NotFound("Template not found")
        
        # Build version chain
        versions = []
        current = template
        
        # Add current version
        versions.append(current)
        
        # Add all parent versions
        while current.parent_version:
            current = current.parent_version
            versions.append(current)
        
        return versions


class EmailTemplateCreateVersionView(CustomResponseMixin, APIView):
    """
    Create a new version of a global template (draft).
    POST /campaigns/templates/<uuid>/create-version/
    Body: {"version_notes": "What changed"}
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        try:
            current_template = EmailTemplate.objects.get(
                id=pk,
                is_global=True,
                is_deleted=False
            )
        except EmailTemplate.DoesNotExist:
            raise NotFound("Global template not found")
        
        version_notes = request.data.get('version_notes', '')
        
        # Create new version as draft
        with transaction.atomic():
            new_version = EmailTemplate.objects.create(
                # Copy all content
                template_name=current_template.template_name,
                category=current_template.category,
                email_subject=current_template.email_subject,
                preview_text=current_template.preview_text,
                email_body=current_template.email_body,
                text_body=current_template.text_body,
                description=current_template.description,
                tags=current_template.tags.copy() if current_template.tags else [],
                # Global template settings
                is_global=True,
                organization=None,
                # Versioning
                version=current_template.version + 1,
                version_notes=version_notes,
                parent_version=current_template,
                # Draft status
                is_draft=True,
                approval_status=EmailTemplate.ApprovalStatus.DRAFT,
            )
        
        serializer = EmailTemplateSerializer(new_version)
        return Response({
            'message': 'New version created as draft',
            'template': serializer.data
        }, status=status.HTTP_201_CREATED)


class EmailTemplateSubmitForApprovalView(CustomResponseMixin, APIView):
    """
    Submit a template for approval.
    POST /campaigns/templates/<uuid>/submit-approval/
    Body: {"approval_notes": "Notes for reviewers"}
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        try:
            template = EmailTemplate.objects.get(
                id=pk,
                is_global=True,
                is_deleted=False,
                is_draft=True
            )
        except EmailTemplate.DoesNotExist:
            raise NotFound("Draft template not found")
        
        if template.approval_status != EmailTemplate.ApprovalStatus.DRAFT:
            raise ValidationError("Template must be in DRAFT status")
        
        approval_notes = request.data.get('approval_notes', '')
        
        # Calculate changes if there's a parent version
        changes_summary = {}
        if template.parent_version:
            changes_summary = calculate_template_diff(template.parent_version, template)
        
        with transaction.atomic():
            # Create approval request
            approval_request = TemplateApprovalRequest.objects.create(
                template=template,
                requested_by=request.user,
                approval_notes=approval_notes,
                version_before_approval=template.version,
                changes_summary=changes_summary,
                status=TemplateApprovalRequest.ApprovalStatus.PENDING
            )
            
            # Update template status
            template.approval_status = EmailTemplate.ApprovalStatus.PENDING_APPROVAL
            template.submitted_for_approval_at = timezone.now()
            template.save()
            
            # Notify other platform admins
            create_approval_request_notification(approval_request)
        
        return Response({
            'message': 'Template submitted for approval',
            'approval_request_id': str(approval_request.id)
        })


class TemplateApprovalReviewView(CustomResponseMixin, APIView):
    """
    Approve or reject a template approval request.
    POST /campaigns/approvals/<uuid>/review/
    Body: {"action": "approve|reject", "notes": "Reviewer notes"}
    """
    permission_classes = [IsPlatformAdmin]
    
    def post(self, request, pk):
        try:
            approval_request = TemplateApprovalRequest.objects.get(id=pk)
        except TemplateApprovalRequest.DoesNotExist:
            raise NotFound("Approval request not found")
        
        if approval_request.status != TemplateApprovalRequest.ApprovalStatus.PENDING:
            raise ValidationError("This approval request has already been reviewed")
        
        action = request.data.get('action')
        notes = request.data.get('notes', '')
        
        if action not in ['approve', 'reject']:
            raise ValidationError("Action must be 'approve' or 'reject'")
        
        with transaction.atomic():
            if action == 'approve':
                approval_request.approve(request.user, notes)
                
                # If this is a new version of an existing global template, create notifications
                template = approval_request.template
                if template.parent_version:
                    create_template_update_notification(
                        template=template,
                        old_version=template.parent_version.version,
                        new_version=template.version,
                        update_summary=template.version_notes or "Template updated"
                    )
                
                message = 'Template approved successfully'
            else:
                approval_request.reject(request.user, notes)
                message = 'Template rejected'
        
        return Response({
            'message': message,
            'approval_request': TemplateApprovalRequestSerializer(approval_request).data
        })


class TemplatePreviewTestView(CustomResponseMixin, APIView):
    """
    Preview and test a template by sending a test email.
    POST /campaigns/templates/preview-test/
    Body: {"template_id": "uuid", "test_email": "email@example.com", "variables": {}}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TemplatePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template_id = serializer.validated_data['template_id']
        test_email = serializer.validated_data['test_email']
        variables = serializer.validated_data.get('variables', {})
        
        try:
            template = EmailTemplate.objects.get(id=template_id, is_deleted=False)
        except EmailTemplate.DoesNotExist:
            raise NotFound("Template not found")
        
        # Check permissions
        if not request.user.is_platform_admin:
            if template.is_global:
                raise PermissionDenied("Cannot test global templates")
            if not request.user.organization_id or str(template.organization_id) != str(request.user.organization_id):
                raise PermissionDenied("Can only test templates from your organization")
        
        # Render template
        rendered = template.render(variables)
        
        # Send test email
        try:
            send_mail(
                subject=f"[TEST] {rendered['subject']}",
                message=rendered['text_body'] or "No text content",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                html_message=rendered['html_body'],
                fail_silently=False,
            )
            
            return Response({
                'message': f'Test email sent successfully to {test_email}',
                'preview': {
                    'subject': rendered['subject'],
                    'preview_text': rendered['preview_text'],
                    'variables_used': list(variables.keys()),
                }
            })
        except Exception as e:
            return Response({
                'error': f'Failed to send test email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailTemplateUpdateFromGlobalView(CustomResponseMixin, APIView):
    """
    Update an organization template to match the latest global template version.
    POST /campaigns/templates/<uuid>/update-from-global/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            org_template = EmailTemplate.objects.get(
                id=pk,
                is_deleted=False,
                is_global=False
            )
        except EmailTemplate.DoesNotExist:
            raise NotFound("Organization template not found")
        
        # Check permissions
        if not request.user.organization_id or str(org_template.organization_id) != str(request.user.organization_id):
            raise PermissionDenied("Can only update templates from your organization")
        
        # Check if template has a source
        if not org_template.source_template:
            raise ValidationError("This template was not created from a global template")
        
        # Get latest version of source template
        try:
            latest_global = EmailTemplate.objects.get(
                id=org_template.source_template.id,
                is_global=True,
                is_deleted=False,
                approval_status=EmailTemplate.ApprovalStatus.APPROVED
            )
        except EmailTemplate.DoesNotExist:
            raise NotFound("Source global template not found")
        
        if latest_global.version <= org_template.version:
            raise ValidationError("Your template is already up to date")
        
        # Update the template
        with transaction.atomic():
            # Keep the organization's custom template name but update everything else
            org_template.category = latest_global.category
            org_template.email_subject = latest_global.email_subject
            org_template.preview_text = latest_global.preview_text
            org_template.email_body = latest_global.email_body
            org_template.text_body = latest_global.text_body
            org_template.description = latest_global.description
            org_template.tags = latest_global.tags.copy() if latest_global.tags else []
            org_template.version = latest_global.version
            org_template.save()
            
            # Mark notification as acted upon if exists
            OrganizationTemplateNotification.objects.filter(
                organization_id=request.user.organization_id,
                notification__global_template_id=latest_global.id,
                template_updated=False
            ).update(template_updated=True)
        
        return Response({
            'message': 'Template updated successfully',
            'template': EmailTemplateSerializer(org_template).data,
            'updated_to_version': latest_global.version
        })
