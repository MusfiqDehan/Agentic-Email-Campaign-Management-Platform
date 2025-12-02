"""
Debug view to test auto health check functionality
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from ..models import EmailProvider
from ..utils.email_providers import EmailProviderFactory
import logging

logger = logging.getLogger(__name__)


class DebugAutoHealthCheckView(APIView):
    """Debug view to test automatic health check functionality"""
    
    def post(self, request):
        """Test auto health check with provided configuration"""
        
        config = request.data.get('config', {})
        provider_type = request.data.get('provider_type', 'SMTP')
        name = request.data.get('name', 'Debug Test Provider')
        
        if not config:
            return Response({
                'error': 'config is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        debug_info = {
            'step': 'starting',
            'config_received': bool(config),
            'provider_type': provider_type
        }
        
        try:
            # Step 1: Create provider instance
            debug_info['step'] = 'creating_provider_instance'
            provider = EmailProviderFactory.create_provider(provider_type, config)
            debug_info['provider_created'] = True
            
            # Step 2: Test health check
            debug_info['step'] = 'running_health_check'
            is_healthy, message = provider.health_check()
            debug_info.update({
                'health_check_completed': True,
                'is_healthy': is_healthy,
                'health_message': message
            })
            
            # Step 3: Test config validation
            debug_info['step'] = 'validating_config'
            is_valid, validation_message = provider.validate_config(config)
            debug_info.update({
                'config_validation_completed': True,
                'is_valid_config': is_valid,
                'validation_message': validation_message
            })
            
            return Response({
                'success': True,
                'debug_info': debug_info,
                'results': {
                    'health_status': 'HEALTHY' if is_healthy else 'UNHEALTHY',
                    'health_details': message,
                    'config_status': 'VALID' if is_valid else 'INVALID',
                    'config_details': validation_message
                }
            })
            
        except Exception as e:
            debug_info.update({
                'error_occurred': True,
                'error_message': str(e),
                'error_type': type(e).__name__
            })
            
            logger.error(f"Debug health check failed: {e}", exc_info=True)
            
            return Response({
                'success': False,
                'debug_info': debug_info,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Get debug information about existing providers"""
        
        providers = EmailProvider.objects.all().order_by('-created_at')[:5]
        
        provider_info = []
        for provider in providers:
            try:
                config = provider.decrypt_config()
                provider_info.append({
                    'id': str(provider.id),
                    'name': provider.name,
                    'provider_type': provider.provider_type,
                    'health_status': provider.health_status,
                    'health_details': provider.health_details,
                    'last_health_check': provider.last_health_check,
                    'has_config': bool(config),
                    'config_fields': list(config.keys()) if config else []
                })
            except Exception as e:
                provider_info.append({
                    'id': str(provider.id),
                    'name': provider.name,
                    'error': str(e)
                })
        
        return Response({
            'total_providers': EmailProvider.objects.count(),
            'recent_providers': provider_info
        })