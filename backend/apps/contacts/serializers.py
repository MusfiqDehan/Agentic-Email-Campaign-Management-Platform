from rest_framework import serializers
from .models import Contact, ContactList


class ContactListSerializer(serializers.ModelSerializer):
    contact_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ContactList
        fields = ['id', 'name', 'description', 'contact_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_contact_count(self, obj):
        return obj.contacts.count()


class ContactSerializer(serializers.ModelSerializer):
    lists_data = ContactListSerializer(source='lists', many=True, read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'email', 'name', 'first_name', 'last_name', 
            'company', 'phone', 'lists', 'lists_data', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
