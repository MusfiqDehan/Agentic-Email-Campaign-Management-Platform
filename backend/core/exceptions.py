from rest_framework.views import exception_handler
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # First, get the standard error response from DRF
    response = exception_handler(exc, context)

    # If DRF did not handle the exception, we handle it here.
    if response is None:
        # Handle specific Python exceptions if needed, e.g., ValueError
        if isinstance(exc, ValueError):
            status_code = status.HTTP_400_BAD_REQUEST
            message = str(exc)
            errors = {'detail': message}
        else:
            # For any other unhandled exception, return a generic 500 error.
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            message = "An unexpected server error occurred."
            # In a production environment, you might want to avoid sending the raw error.
            # For debugging, str(exc) is useful.
            errors = {'detail': str(exc)}

        custom_response = {
            "message": message,
            "status_type": "error",
            "status_code": status_code,
            "timestamp": timezone.now().isoformat(),
            "errors": errors
        }
        return Response(custom_response, status=status_code)

    # If DRF handled the exception, we re-format the response.
    if response is not None:
        
        # Default message if none is found
        message = "An error occurred."
        
        # Try to get a more specific message from the response data
        if isinstance(response.data, dict):
            # For validation errors, DRF puts details in the data.
            # We can try to extract the first error message.
            error_detail = next(iter(response.data.values()), None)
            if error_detail:
                if isinstance(error_detail, list):
                    message = error_detail[0]
                else:
                    message = str(error_detail)
            # For other errors, 'detail' key is common
            elif 'detail' in response.data:
                message = response.data['detail']

        custom_response = {
            "message": message,
            "status_type": "error",
            "status_code": response.status_code,
            "timestamp": timezone.now().isoformat(),
            "errors": response.data  # Keep original errors for debugging
        }
        response.data = custom_response

    return response
