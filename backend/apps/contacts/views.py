from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Contact, ContactList
from .serializers import ContactSerializer, ContactListSerializer


class ContactListViewSet(viewsets.ModelViewSet):
    queryset = ContactList.objects.all()
    serializer_class = ContactListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        contact_list = self.get_object()
        contacts = contact_list.contacts.all()
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'first_name', 'last_name', 'company']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        list_id = self.request.query_params.get('list_id', None)
        if list_id:
            queryset = queryset.filter(lists__id=list_id)
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset
