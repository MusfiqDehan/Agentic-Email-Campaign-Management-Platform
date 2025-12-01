import requests
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TenantServiceAPI:
    """API client for the Tenant Service following the same pattern as AuthServiceAPI."""
    
    @staticmethod
    def _get_base_url():
        """Get the base URL for tenant service from settings"""
        return getattr(settings, 'TENANT_SERVICE_BASE_URL', 'http://localhost:8001/')
    
    @staticmethod
    def _get_headers(request=None):
        """Get headers for tenant service API calls"""
        headers = {'Content-Type': 'application/json'}
        if request and request.headers.get('Authorization'):
            headers['Authorization'] = request.headers.get('Authorization')
        return headers
    
    @classmethod
    def get_tenant_details(cls, tenant_id, request=None):
        """Get tenant details from Tenant Service with caching"""
        cache_key = f"tenant_details_{tenant_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{cls._get_base_url()}api/tenants/{tenant_id}/"
            headers = cls._get_headers(request)
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No tenant found for ID: {tenant_id}")
                return {
                    "tenant_id": tenant_id,
                    "name": None,
                    "email": None,
                    "domain": None,
                    "subdomain": None,
                    "status": "inactive"
                }
            
            # Standardize the response format
            tenant_data = {
                "tenant_id": str(data.get("tenant_id", tenant_id)),
                "name": data.get("name"),
                "email": data.get("email"),
                "domain": data.get("domain"),
                "subdomain": data.get("subdomain"),
                "status": data.get("status", "inactive"),
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "trial_days": data.get("trial_days", 30)
            }
            
            try:
                # Cache the result for 5 minutes
                cache.set(cache_key, tenant_data, timeout=300)
            except Exception as cache_error:
                logger.error(f"Error caching tenant details: {cache_error}")
            
            return tenant_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Tenant Microservice for tenant {tenant_id}: {e}")
            # Return None to indicate service unavailable (not the same as inactive)
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_tenant_details: {e}")
            # Return None to indicate error (not the same as inactive)
            return None
    
    @classmethod
    def get_tenant_metadata(cls, tenant_id, key=None, request=None):
        """Get tenant metadata from Tenant Service"""
        cache_key = f"tenant_metadata_{tenant_id}_{key}" if key else f"tenant_metadata_{tenant_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{cls._get_base_url()}api/tenants/{tenant_id}/metadata/"
            if key:
                url += f"?key={key}"
            
            headers = cls._get_headers(request)
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            try:
                # Cache the result for 10 minutes
                cache.set(cache_key, data, timeout=600)
            except Exception as cache_error:
                logger.error(f"Error caching tenant metadata: {cache_error}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Tenant Microservice for metadata {tenant_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_tenant_metadata: {e}")
            return {}
    
    @classmethod
    def get_tenant_organization(cls, tenant_id, request=None):
        """Get tenant organization details from Tenant Service"""
        cache_key = f"tenant_organization_{tenant_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{cls._get_base_url()}api/tenants/{tenant_id}/organization/"
            headers = cls._get_headers(request)
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            try:
                # Cache the result for 10 minutes
                cache.set(cache_key, data, timeout=600)
            except Exception as cache_error:
                logger.error(f"Error caching tenant organization: {cache_error}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Tenant Microservice for organization {tenant_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_tenant_organization: {e}")
            return {}
    
    @classmethod
    def get_tenant_plan_limits(cls, tenant_id, request=None):
        """Get email limits based on tenant plan and metadata"""
        tenant = cls.get_tenant_details(tenant_id, request)
        if not tenant:
            # Return default free limits
            return {
                'emails_per_day': 50,
                'emails_per_month': 500,
                'emails_per_minute': 5,
                'custom_domain_allowed': False,
                'advanced_analytics': False
            }
        
        # Map tenant status to limits
        status_limits = {
            'trial': {
                'emails_per_day': 50,
                'emails_per_month': 500, 
                'emails_per_minute': 5,
                'custom_domain_allowed': False,
                'advanced_analytics': False
            },
            'active': {
                'emails_per_day': 1000,
                'emails_per_month': 10000,
                'emails_per_minute': 50,
                'custom_domain_allowed': True,
                'advanced_analytics': True
            },
            'inactive': {
                'emails_per_day': 0,
                'emails_per_month': 0,
                'emails_per_minute': 0,
                'custom_domain_allowed': False,
                'advanced_analytics': False
            },
            'past_due': {
                'emails_per_day': 10,
                'emails_per_month': 100,
                'emails_per_minute': 2,
                'custom_domain_allowed': False,
                'advanced_analytics': False
            }
        }
        
        # Get plan-specific metadata if available
        metadata = cls.get_tenant_metadata(tenant_id, 'email_plan', request)
        if metadata and 'plan_limits' in metadata:
            return metadata['plan_limits']
        
        return status_limits.get(tenant.get('status'), status_limits['trial'])
    
    @classmethod
    def is_tenant_active(cls, tenant_id, request=None):
        """
        Check if tenant is active and can use email services.
        
        Returns:
            True: Tenant is active
            False: Tenant is explicitly inactive
            None: Could not determine (service unavailable)
        """
        tenant = cls.get_tenant_details(tenant_id, request)
        if tenant is None:
            # Service unavailable
            return None
        if not tenant:
            # Empty response (not found)
            return False
        
        status = tenant.get('status', 'inactive')
        return status in ['active', 'trial']
    
    @classmethod
    def get_tenant_domain_info(cls, tenant_id, request=None):
        """Get tenant domain information for email configuration"""
        tenant = cls.get_tenant_details(tenant_id, request)
        organization = cls.get_tenant_organization(tenant_id, request)
        
        domain_info = {
            'subdomain': tenant.get('subdomain'),
            'domain': tenant.get('domain'),
            'custom_domain': organization.get('company_website'),
            'default_from_email': f"noreply@{tenant.get('domain', 'techforing.com')}",
        }
        
        return domain_info
    
    @classmethod
    def invalidate_tenant_cache(cls, tenant_id):
        """Invalidate all cached data for a tenant"""
        cache_keys = [
            f"tenant_details_{tenant_id}",
            f"tenant_metadata_{tenant_id}",
            f"tenant_organization_{tenant_id}",
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        # Also delete any metadata with specific keys (this is approximate)
        # In production, you might want to use cache versioning or tagging
        logger.info(f"Invalidated cache for tenant {tenant_id}")


# Helper function for backward compatibility and ease of use
def get_tenant_info(tenant_id, request=None):
    """Convenience function to get tenant information"""
    return TenantServiceAPI.get_tenant_details(tenant_id, request)


def get_tenant_email_limits(tenant_id, request=None):
    """Convenience function to get tenant email limits"""
    return TenantServiceAPI.get_tenant_plan_limits(tenant_id, request)