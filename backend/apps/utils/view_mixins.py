from .responses import success, error

class ResponseMixin:
    def success(self, data=None, message="OK", status_code=200, meta=None):
        return success(data=data, message=message, status_code=status_code, meta=meta)

    def error(self, message="Error", errors=None, status_code=400, meta=None):
        return error(message=message, errors=errors, status_code=status_code, meta=meta)