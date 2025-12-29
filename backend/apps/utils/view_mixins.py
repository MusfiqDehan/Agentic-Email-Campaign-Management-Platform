from .responses import success, error

class ResponseMixin:
    def success(self, data=None, message="OK", status_code=200, meta=None):
        return success(data=data, message=message, status_code=status_code, meta=meta)

    def error(self, message="Error", errors=None, status_code=400, meta=None):
        return error(message=message, errors=errors, status_code=status_code, meta=meta)


class PublicCORSMixin:
    """
    Mixin that adds permissive CORS headers for public endpoints.
    
    Use this for endpoints that need to be accessible from any origin,
    such as tracking pixels, public signup forms, and unsubscribe links.
    
    This keeps the global CORS configuration restrictive while allowing
    specific public endpoints to be accessed cross-origin.
    """
    
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Allow requests from any origin
        response["Access-Control-Allow-Origin"] = "*"
        
        # Allow common HTTP methods
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        
        # Allow common headers
        response["Access-Control-Allow-Headers"] = "Content-Type, Accept"
        
        # Cache preflight for 1 hour
        response["Access-Control-Max-Age"] = "3600"
        
        return response
    
    def options(self, request, *args, **kwargs):
        """Handle preflight OPTIONS requests."""
        from rest_framework.response import Response
        return Response(status=200)