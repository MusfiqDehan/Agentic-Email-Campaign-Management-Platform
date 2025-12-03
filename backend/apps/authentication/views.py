from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    EmailVerificationSerializer,
)
from apps.authentication.services.email_service import EmailService
from apps.utils.view_mixins import ResponseMixin
from apps.utils.throttles import AuthBurstRateThrottle, AuthSustainedRateThrottle

BLACKLIST_PREFIX = "bltoken:"


class SignupView(ResponseMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthBurstRateThrottle, AuthSustainedRateThrottle]

    def post(self, request):
        serializer = SignupSerializer(
            data=request.data, context={"email_service": EmailService()}
        )
        if serializer.is_valid():
            serializer.save()
            return self.success(
                serializer.data,
                message="Signup successful. Please verify email.",
                status_code=201,
            )
        return self.error("Signup failed", errors=serializer.errors, status_code=400)


class EmailVerifyView(ResponseMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = EmailVerificationSerializer(
            data={"token": request.query_params.get("token")}
        )
        if serializer.is_valid():
            serializer.save()
            return self.success(message="Email verified")
        return self.error("Verification failed", errors=serializer.errors)


class LoginView(ResponseMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthBurstRateThrottle, AuthSustainedRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {"id": user.id, "email": user.email, "username": user.username},
            }
            return self.success(data=data, message="Login successful")
        return self.error("Login failed", errors=serializer.errors)


class LogoutView(ResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return self.error("Refresh token required")
        try:
            token_obj = RefreshToken(refresh_token)
            jti = token_obj["jti"]
            # Blacklist for its remaining lifetime
            cache.set(
                f"{BLACKLIST_PREFIX}{jti}",
                True,
                timeout=int(token_obj.access_token.lifetime.total_seconds()),
            )
            return self.success(message="Logged out")
        except Exception as e:
            return self.error("Invalid token", errors={"detail": str(e)})


class ChangePasswordView(ResponseMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return self.success(message="Password changed")
        return self.error("Change failed", errors=serializer.errors)


class RequestPasswordResetView(ResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(
            data=request.data, context={"email_service": EmailService()}
        )
        if serializer.is_valid():
            serializer.save()
            return self.success(message="If the email exists a reset was sent")
        return self.error("Request failed", errors=serializer.errors)


class ResetPasswordView(ResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(message="Password reset complete")
        return self.error("Reset failed", errors=serializer.errors)