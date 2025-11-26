from rest_framework.throttling import SimpleRateThrottle

class AuthBurstRateThrottle(SimpleRateThrottle):
    scope = 'auth_burst'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_{self.scope}_{ident}"

class AuthSustainedRateThrottle(SimpleRateThrottle):
    scope = 'auth_sustained'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_{self.scope}_{ident}"