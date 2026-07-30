"""
Public unsubscribe API — supports human confirmation page data and RFC 8058 one-click.
"""
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from apps.utils.view_mixins import PublicCORSMixin
from apps.campaigns.models import Contact
from apps.campaigns.serializers.campaign_serializers import UnsubscribeSerializer


class UnsubscribeView(PublicCORSMixin, APIView):
    """
    Public endpoint for unsubscribing contacts.

    GET  /unsubscribe/?token=xxx  — confirmation page data for the frontend
    POST /unsubscribe/?token=xxx  — process unsubscribe (JSON or RFC 8058 one-click form)
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def _get_contact(self, token: str):
        if not token:
            return None
        return Contact.objects.select_related('organization').filter(
            unsubscribe_token=token
        ).first()

    def get(self, request):
        token = request.query_params.get('token') or request.query_params.get('t')
        if not token:
            return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)

        contact = self._get_contact(token)
        if not contact:
            return Response({'error': 'Invalid or expired unsubscribe link'}, status=status.HTTP_404_NOT_FOUND)

        org_name = ''
        if contact.organization_id:
            org_name = contact.organization.name

        frontend = getattr(settings, 'FRONTEND_URL', 'http://localhost:3001').rstrip('/')
        already = contact.status == 'UNSUBSCRIBED'

        return Response({
            'email': contact.email,
            'first_name': contact.first_name or '',
            'status': contact.status,
            'already_unsubscribed': already,
            'organization_name': org_name,
            'message': 'Already unsubscribed' if already else 'Confirm unsubscribe',
            'confirm_url': f'{frontend}/unsubscribe?token={token}',
            'token': token,
        })

    def post(self, request):
        """
        Accepts:
        - JSON: { "token": "...", "reason": "..." }
        - Query token + form body List-Unsubscribe=One-Click (RFC 8058)
        - Form fields: token, reason
        """
        token = (
            request.data.get('token')
            or request.query_params.get('token')
            or request.query_params.get('t')
        )
        reason = request.data.get('reason') or ''

        # RFC 8058 one-click: body is List-Unsubscribe=One-Click
        one_click = (
            str(request.data.get('List-Unsubscribe', '')).lower() == 'one-click'
            or request.content_type == 'application/x-www-form-urlencoded'
            and 'one-click' in str(request.data).lower()
        )
        if one_click and not reason:
            reason = 'One-click unsubscribe'

        if not token:
            return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)

        contact = self._get_contact(token)
        if not contact:
            return Response({'error': 'Invalid or expired unsubscribe link'}, status=status.HTTP_404_NOT_FOUND)

        if contact.status == 'UNSUBSCRIBED':
            return Response({
                'message': 'Already unsubscribed',
                'email': contact.email,
                'already_unsubscribed': True,
            })

        # Validate via serializer when JSON reason is present (skip strict "already" check)
        if request.data.get('token') and not one_click:
            serializer = UnsubscribeSerializer(data={'token': token, 'reason': reason})
            # Soft-validate: only reject truly invalid tokens (already handled above)
            if not serializer.is_valid():
                # If only error is "Already unsubscribed", treat as success
                errors = serializer.errors.get('token', [])
                if any('Already' in str(e) for e in errors):
                    return Response({
                        'message': 'Already unsubscribed',
                        'email': contact.email,
                        'already_unsubscribed': True,
                    })
                # Invalid token already returned 404 above; other validation errors:
                if 'Invalid' in str(errors):
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        contact.unsubscribe(reason or 'User unsubscribed')

        # Mark related delivery logs
        try:
            from apps.campaigns.models import EmailDeliveryLog
            EmailDeliveryLog.objects.filter(
                contact=contact,
                delivery_status__in=['SENT', 'DELIVERED', 'OPENED', 'CLICKED'],
            ).update(delivery_status='UNSUBSCRIBED')
        except Exception:
            pass

        return Response({
            'message': 'Successfully unsubscribed',
            'email': contact.email,
            'already_unsubscribed': False,
            'organization_name': contact.organization.name if contact.organization_id else '',
        })
