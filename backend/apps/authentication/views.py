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
    UserProfileSerializer,
    OrganizationProfileSerializer,
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
            
            # Build user data with organization info
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_platform_admin": user.is_platform_admin,
            }
            
            # Include organization info if user belongs to one
            organization_data = None
            if user.organization:
                organization_data = {
                    "id": str(user.organization.id),
                    "name": user.organization.name,
                    "slug": user.organization.slug,
                    "is_owner": user.is_org_owner,
                    "is_admin": user.is_org_admin,
                }
            
            data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": user_data,
                "organization": organization_data,
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


class ProfileDetailView(ResponseMixin, GenericAPIView):
    """
    Get or update user and organization profile details.
    
    GET /profile/details/
    PATCH /profile/details/
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        return UserProfileSerializer

    def get(self, request):
        serializer = self.get_serializer(request.user)
        return self.success(serializer.data)

    def patch(self, request):
        user = request.user
        organization = user.organization

        # Separate user and organization data from request
        user_data = request.data.copy()
        org_data = {}
        
        # If 'organization_details' is in request, it might be nested
        if 'organization_details' in user_data:
            org_data = user_data.pop('organization_details')
        
        # Also check for top-level org fields if they aren't nested (common in multipart)
        org_fields = ['name', 'description', 'logo']
        for field in org_fields:
            if field in user_data and field not in org_data:
                org_data[field] = user_data.pop(field)

        # Update User
        user_serializer = UserProfileSerializer(user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return self.error("Failed to update user profile", errors=user_serializer.errors)

        # Update Organization if user is admin/owner
        if organization and org_data and user.is_org_admin:
            org_serializer = OrganizationProfileSerializer(organization, data=org_data, partial=True)
            if org_serializer.is_valid():
                org_serializer.save()
            else:
                return self.error("Failed to update organization profile", errors=org_serializer.errors)

        return self.success(UserProfileSerializer(user).data, message="Profile updated successfully")