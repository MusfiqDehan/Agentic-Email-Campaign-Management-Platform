from rest_framework.response import Response


def success(data=None, message="OK", status_code=200, meta=None):
    return Response({
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
        "meta": meta or {}
    }, status=status_code)


def error(message="Error", errors=None, status_code=400, meta=None):
    return Response({
        "success": False,
        "message": message,
        "data": None,
        "errors": errors or {},
        "meta": meta or {}
    }, status=status_code)