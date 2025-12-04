"""View mixins for DRF views."""

from rest_framework import status
from django.utils import timezone
from rest_framework.response import Response


class CustomResponseMixin:
    """
    A mixin to provide a consistent JSON response structure for successful API view responses.
    Error responses are handled by the custom_exception_handler.
    """
    
    def success_response(self, data=None, message="Success", status_code=status.HTTP_200_OK):
        """
        Return a success response with consistent structure
        """
        response_data = {
            "message": message,
            "status_type": "success",
            "status_code": status_code,
            "timestamp": timezone.now().isoformat(),
            "data": data or {}
        }
        return Response(response_data, status=status_code)
    
    def error_response(self, message="Error", data=None, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
        """
        Return an error response with consistent structure
        """
        response_data = {
            "message": message,
            "status_type": "error",
            "status_code": status_code,
            "timestamp": timezone.now().isoformat()
        }
        
        if data is not None:
            response_data["data"] = data
            
        if errors is not None:
            response_data["errors"] = errors
            
        return Response(response_data, status=status_code)

    def finalize_response(self, request, response, *args, **kwargs):
        # First, handle the special case of a successful DELETE (204 No Content)
        # by transforming it into a 200 OK with a body.
        if response.status_code == status.HTTP_204_NO_CONTENT and request.method == 'DELETE':
            response.status_code = status.HTTP_200_OK
            response.data = {
                "message": "Resource deleted successfully.",
                "status_type": "success",
                "status_code": status.HTTP_200_OK,
                "timestamp": timezone.now().isoformat(),
                "data": {}
            }
            # The response is now formatted, so we can proceed to the super call.

        # We only format other successful responses. Error responses are handled by the custom exception handler.
        elif 200 <= response.status_code < 300 and hasattr(response, 'data') and response.data is not None:
            # If the response is already structured, pass it through without modification.
            if isinstance(response.data, dict) and all(k in response.data for k in ['status_type', 'timestamp', 'message', 'data']):
                return super().finalize_response(request, response, *args, **kwargs)
            
            response_data = response.data
            message = "Success"
            original_status = response.status_code

            # If the original response data is a dict and has a 'message' key, use it.
            if isinstance(response_data, dict) and 'message' in response_data:
                message = response_data.pop('message') # Use and remove from original data
                if not response_data:
                    response_data = {}

            if original_status == status.HTTP_200_OK:
                if request.method in ['PATCH', 'PUT']:
                    message = "Resource updated successfully."
                elif request.method == 'GET':
                    if isinstance(response_data, dict) and 'results' in response_data and 'count' in response_data:
                        message = "Resources retrieved successfully."
                    else:
                        message = "Resource retrieved successfully."

            elif original_status == status.HTTP_201_CREATED:
                message = "Resource created successfully."
            
            # Extract results from paginated responses
            if isinstance(response_data, dict) and 'results' in response_data and 'count' in response_data:
                response_data = response_data['results']
            
            structured_response = {
                "message": message,
                "status_type": "success",
                "status_code": response.status_code,
                "timestamp": timezone.now().isoformat(),
                "data": response_data
            }
            response.data = structured_response
        
        return super().finalize_response(request, response, *args, **kwargs)


# Backward compatibility aliases
ResponseMixin = CustomResponseMixin

__all__ = ['CustomResponseMixin', 'ResponseMixin']
