from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignupView,
    EmailVerifyView,
    LoginView,
    LogoutView,
    ChangePasswordView,
    RequestPasswordResetView,
    ResetPasswordView,
    ProfileDetailView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("verify-email/", EmailVerifyView.as_view(), name="verify-email"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("request-password-reset/", RequestPasswordResetView.as_view(), name="request-password-reset"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("profile/details/", ProfileDetailView.as_view(), name="profile-details"),
]