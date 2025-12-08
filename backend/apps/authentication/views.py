from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    EmailVerificationSerializer,
)
from apps.authentication.services.email_service import EmailService
from apps.utils.view_mixins import ResponseMixin
from apps.utils.throttles import AuthBurstRateThrottle, AuthSustainedRateThrottle

BLACKLIST_PREFIX = "bltoken:"


class SignupView(ResponseMixin, GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthBurstRateThrottle, AuthSustainedRateThrottle]
    serializer_class = SignupSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["email_service"] = EmailService()
        return context

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(
                serializer.data,
                message="Signup successful. Please verify email.",
                status_code=201,
            )
        return self.error("Signup failed", errors=serializer.errors, status_code=400)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name="token",
            type=str,
            required=True,
            location=OpenApiParameter.QUERY,
            description="JWT emailed to the user for verification",
        )
    ]
)
class EmailVerifyView(ResponseMixin, GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def get(self, request):
        serializer = self.get_serializer(
            data={"token": request.query_params.get("token")}
        )
        if serializer.is_valid():
            serializer.save()
            return self.success(message="Email verified")
        return self.error("Verification failed", errors=serializer.errors)


class LoginView(ResponseMixin, GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthBurstRateThrottle, AuthSustainedRateThrottle]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
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


class LogoutView(ResponseMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error("Logout failed", errors=serializer.errors)
        refresh_token = serializer.validated_data["refresh"]
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


class ChangePasswordView(ResponseMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(message="Password changed")
        return self.error("Change failed", errors=serializer.errors)


class RequestPasswordResetView(ResponseMixin, GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestPasswordResetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["email_service"] = EmailService()
        return context

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(message="If the email exists a reset was sent")
        return self.error("Request failed", errors=serializer.errors)


class ResetPasswordView(ResponseMixin, GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success(message="Password reset complete")
        return self.error("Reset failed", errors=serializer.errors)