"""
Serializers for push notifications.
"""
from rest_framework import serializers
from apps.campaigns.models.push_models import PushSubscription


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for push subscription."""
    subscription = serializers.JSONField(write_only=True)

    class Meta:
        model = PushSubscription
        fields = ['id', 'subscription', 'is_active', 'created_at', 'last_used']
        read_only_fields = ['id', 'created_at', 'last_used']

    def create(self, validated_data):
        """Create or update push subscription."""
        subscription_data = validated_data.pop('subscription')
        user = self.context['request'].user
        
        # Extract subscription details
        endpoint = subscription_data['endpoint']
        keys = subscription_data['keys']
        
        # Get user agent from request
        user_agent = self.context['request'].META.get('HTTP_USER_AGENT', '')
        
        # Update or create subscription
        obj, created = PushSubscription.objects.update_or_create(
            user=user,
            endpoint=endpoint,
            defaults={
                'organization': user.organization,
                'p256dh': keys['p256dh'],
                'auth': keys['auth'],
                'is_active': True,
                'user_agent': user_agent
            }
        )
        
        return obj


class PushSubscriptionListSerializer(serializers.ModelSerializer):
    """Serializer for listing push subscriptions."""
    
    class Meta:
        model = PushSubscription
        fields = ['id', 'is_active', 'created_at', 'last_used', 'user_agent']
        read_only_fields = fields
