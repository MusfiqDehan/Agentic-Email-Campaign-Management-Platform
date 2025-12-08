from django.contrib.auth import authenticate, password_validation
from django.utils.text import slugify
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.authentication.models import Organization, OrganizationMembership, EmailVerificationToken, PasswordResetToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "organization"]
        read_only_fields = ["id", "organization"]


class OrganizationSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "owner", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "owner", "created_at", "updated_at"]


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    organization_name = serializers.CharField(max_length=120)
    first_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    is_platform_admin = serializers.BooleanField(required=False, default=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name")
        password = validated_data.pop("password")
        is_platform_admin = validated_data.pop("is_platform_admin", False)
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False  # Require email verification
        user.is_platform_admin = is_platform_admin
        user.save()
        slug = slugify(org_name)
        i = 1
        base_slug = slug
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{i}"; i += 1
        org = Organization.objects.create(name=org_name, slug=slug, owner=user)
        OrganizationMembership.objects.create(user=user, organization=org, role="owner")
        user.organization = org
        user.save(update_fields=["organization"])
        token = EmailVerificationToken.objects.create(user=user)
        # Stub: replace with real email sending integration
        self.context.get("email_service").send_verification_email(user.email, str(token.token))
        return user

    def to_representation(self, instance):
        return {
            "user": UserSerializer(instance).data,
            "organization": OrganizationSerializer(instance.organization).data,
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("Invalid credentials")
        if not user.is_active:
            raise ValidationError("Email not verified")
        user = authenticate(username=user.username, password=password)
        if not user:
            raise ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise ValidationError("Old password incorrect")
        password_validation.validate_password(attrs['new_password'], user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("If the email exists a reset will be sent.")
        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        token = PasswordResetToken.objects.create(user=user)
        self.context.get("email_service").send_password_reset_email(user.email, str(token.token))
        return token


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        token_val = attrs['token']
        try:
            token_obj = PasswordResetToken.objects.get(token=token_val, is_used=False)
        except PasswordResetToken.DoesNotExist:
            raise ValidationError("Invalid or used token")
        if timezone.now() > token_obj.expires_at:
            raise ValidationError("Token expired")
        attrs['token_obj'] = token_obj
        password_validation.validate_password(attrs['new_password'], token_obj.user)
        return attrs

    def save(self, **kwargs):
        token_obj = self.validated_data['token_obj']
        user = token_obj.user
        user.set_password(self.validated_data['new_password'])
        user.save()
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])
        return user


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate(self, attrs):
        token_val = attrs['token']
        try:
            token_obj = EmailVerificationToken.objects.get(token=token_val, is_used=False)
        except EmailVerificationToken.DoesNotExist:
            raise ValidationError("Invalid or used token")
        if timezone.now() > token_obj.expires_at:
            raise ValidationError("Token expired")
        attrs['token_obj'] = token_obj
        return attrs

    def save(self, **kwargs):
        token_obj = self.validated_data['token_obj']
        user = token_obj.user
        user.is_active = True
        user.save(update_fields=['is_active'])
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])
        return user