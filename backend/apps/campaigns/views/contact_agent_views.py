from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.shortcuts import get_object_or_404
from google import genai
import json
import logging
from ..models import Contact, ContactList

logger = logging.getLogger(__name__)

class ContactAgentView(APIView):
    """
    API View to manage contacts and contact lists using Google Gemini AI agent.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return Response({"error": "GEMINI_API_KEY not configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            client = genai.Client(api_key=api_key)
            
            system_instruction = """
            You are an AI assistant that manages contacts and contact lists for an email marketing platform.
            Interpret the user's natural language request and convert it into a structured JSON action.
            
            Supported Actions:
            - CREATE_CONTACT: Create a new contact.
            - UPDATE_CONTACT: Update an existing contact.
            - DELETE_CONTACT: Delete a contact (soft delete).
            - ADD_TO_LIST: Add a contact to a specific list.
            - REMOVE_FROM_LIST: Remove a contact from a specific list.
            - CREATE_CONTACT_LIST: Create a new contact list.
            - UPDATE_CONTACT_LIST: Update an existing contact list.
            - DELETE_CONTACT_LIST: Delete a contact list.

            Output JSON Format:
            {
                "action": "ACTION_NAME",
                "data": {
                    "email": "email@example.com", (REQUIRED for contact actions)
                    "first_name": "John", (Optional for contact actions)
                    "last_name": "Doe", (Optional for contact actions)
                    "phone": "+1234567890", (Optional for contact actions)
                    "list_name": "Newsletter", (Required for list actions and ADD_TO_LIST/REMOVE_FROM_LIST)
                    "new_list_name": "New Newsletter Name", (Optional for UPDATE_CONTACT_LIST)
                    "description": "List description", (Optional for list actions)
                    "tags": ["tag1", "tag2"] (Optional list of strings)
                }
            }
            
            If the request is ambiguous, return {"error": "Description of the error"}.
            For contact actions (CREATE/UPDATE/DELETE/ADD_TO/REMOVE_FROM), email is required.
            For list actions (CREATE/UPDATE/DELETE_CONTACT_LIST), list_name is required.
            Return ONLY the JSON object.
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=f"{system_instruction}\n\nUser Request: {prompt}",
                config={'response_mime_type': 'application/json'}
            )
            
            try:
                text_content = response.text
                if text_content.strip().startswith("```json"):
                    text_content = text_content.replace("```json", "").replace("```", "")
                result = json.loads(text_content)
            except json.JSONDecodeError:
                return Response(
                    {"error": "Failed to parse AI response as JSON.", "raw_response": response.text},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            if "error" in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            action = result.get("action")
            data = result.get("data", {})
            email = data.get("email", "").strip().lower()
            list_name = data.get("list_name", "").strip()
            
            organization = request.user.organization

            # Validation based on action type
            contact_actions = ["CREATE_CONTACT", "UPDATE_CONTACT", "DELETE_CONTACT", "ADD_TO_LIST", "REMOVE_FROM_LIST"]
            list_actions = ["CREATE_CONTACT_LIST", "UPDATE_CONTACT_LIST", "DELETE_CONTACT_LIST"]

            if action in contact_actions and not email:
                 return Response({"error": "Could not identify email address from prompt"}, status=status.HTTP_400_BAD_REQUEST)
            
            if action in list_actions and not list_name:
                 return Response({"error": "Could not identify list name from prompt"}, status=status.HTTP_400_BAD_REQUEST)

            if action == "CREATE_CONTACT" or action == "ADD_TO_LIST":
                # Check all contacts (including soft-deleted)
                contact = Contact.all_objects.filter(
                    organization=organization,
                    email__iexact=email
                ).first()
                
                created = False
                if not contact:
                    contact = Contact.objects.create(
                        organization=organization,
                        email=email,
                        first_name=data.get("first_name", ""),
                        last_name=data.get("last_name", ""),
                        phone=data.get("phone", ""),
                        source="AGENT"
                    )
                    created = True
                
                msg = "Contact created successfully." if created else "Contact updated successfully."
                
                # Update fields if explicitly provided in CREATE/ADD_TO_LIST prompt
                updated = False
                if data.get("first_name"): 
                    contact.first_name = data.get("first_name")
                    updated = True
                if data.get("last_name"): 
                    contact.last_name = data.get("last_name")
                    updated = True
                if data.get("phone"): 
                    contact.phone = data.get("phone")
                    updated = True
                
                if contact.is_deleted:
                    contact.is_deleted = False
                    updated = True
                    msg = "Contact restored and updated successfully."
                
                if updated:
                    contact.save()
                    if contact.is_deleted is False:
                        # If restored or updated, refresh all its lists
                        for cl in contact.lists.all():
                            cl.update_stats()

                # Handle list addition
                if list_name:
                    contact_list, list_created = ContactList.objects.get_or_create(
                        organization=organization,
                        name__iexact=list_name,
                        defaults={
                            "organization": organization,
                            "name": list_name
                        }
                    )
                    contact.lists.add(contact_list)
                    contact_list.update_stats()
                    msg += f" Added to list '{contact_list.name}'."
                
                # Handle tags
                tags = data.get("tags")
                if tags and isinstance(tags, list):
                    current_tags = contact.tags or []
                    contact.tags = list(set(current_tags + tags))
                    contact.save()

                return Response({"message": msg, "contact": {"id": contact.id, "email": contact.email}})

            elif action == "UPDATE_CONTACT":
                contact = Contact.objects.filter(organization=organization, email__iexact=email).first()
                if not contact:
                    return Response({"error": f"Contact with email {email} not found."}, status=status.HTTP_404_NOT_FOUND)
                
                if data.get("first_name"): contact.first_name = data.get("first_name")
                if data.get("last_name"): contact.last_name = data.get("last_name")
                if data.get("phone"): contact.phone = data.get("phone")
                
                tags = data.get("tags")
                if tags and isinstance(tags, list):
                    current_tags = contact.tags or []
                    contact.tags = list(set(current_tags + tags))
                
                contact.save()
                
                # Refresh stats for all lists this contact is in
                for cl in contact.lists.all():
                    cl.update_stats()
                    
                return Response({"message": "Contact updated successfully.", "contact": {"id": contact.id, "email": contact.email}})

            elif action == "DELETE_CONTACT":
                contact = Contact.objects.filter(organization=organization, email__iexact=email).first()
                if not contact:
                    return Response({"error": f"Contact with email {email} not found."}, status=status.HTTP_404_NOT_FOUND)
                
                contact.is_deleted = True
                contact.save()
                
                # Refresh stats for all lists this contact was in
                for contact_list in contact.lists.all():
                    contact_list.update_stats()
                    
                return Response({"message": f"Contact {contact.email} deleted successfully."})

            elif action == "ADD_TO_LIST":
                if not list_name:
                    return Response({"error": "List name is required for this action."}, status=status.HTTP_400_BAD_REQUEST)
                
                contact = Contact.objects.filter(organization=organization, email=email).first()
                if not contact:
                     return Response({"error": f"Contact with email {email} not found."}, status=status.HTTP_404_NOT_FOUND)

                contact_list, _ = ContactList.objects.get_or_create(
                    organization=organization,
                    name=list_name
                )
                contact.lists.add(contact_list)
                contact_list.update_stats()
                return Response({"message": f"Contact {email} added to list '{list_name}'."})

            elif action == "REMOVE_FROM_LIST":
                if not list_name:
                    return Response({"error": "List name is required for this action."}, status=status.HTTP_400_BAD_REQUEST)
                
                contact = Contact.objects.filter(organization=organization, email__iexact=email).first()
                if not contact:
                    return Response({"error": f"Contact with email {email} not found."}, status=status.HTTP_404_NOT_FOUND)
                
                contact_list = ContactList.objects.filter(organization=organization, name__iexact=list_name).first()
                if contact_list:
                    contact.lists.remove(contact_list)
                    contact_list.update_stats()
                    return Response({"message": f"Contact {contact.email} removed from list '{contact_list.name}'."})
                else:
                    return Response({"error": f"List '{list_name}' not found."}, status=status.HTTP_404_NOT_FOUND)

            elif action == "CREATE_CONTACT_LIST":
                contact_list, created = ContactList.objects.get_or_create(
                    organization=organization,
                    name__iexact=list_name,
                    defaults={
                        "organization": organization,
                        "name": list_name,
                        "description": data.get("description", ""),
                        "tags": data.get("tags", [])
                    }
                )
                if not created:
                    return Response({"message": f"List '{contact_list.name}' already exists.", "list": {"id": contact_list.id, "name": contact_list.name}})
                return Response({"message": f"List '{contact_list.name}' created successfully.", "list": {"id": contact_list.id, "name": contact_list.name}})

            elif action == "UPDATE_CONTACT_LIST":
                contact_list = ContactList.objects.filter(organization=organization, name__iexact=list_name).first()
                if not contact_list:
                    return Response({"error": f"List '{list_name}' not found."}, status=status.HTTP_404_NOT_FOUND)
                
                new_name = data.get("new_list_name")
                if new_name:
                    contact_list.name = new_name
                
                if data.get("description"):
                    contact_list.description = data.get("description")
                
                tags = data.get("tags")
                if tags and isinstance(tags, list):
                    current_tags = contact_list.tags or []
                    contact_list.tags = list(set(current_tags + tags))
                
                contact_list.save()
                return Response({"message": f"List updated successfully.", "list": {"id": contact_list.id, "name": contact_list.name}})

            elif action == "DELETE_CONTACT_LIST":
                contact_list = ContactList.objects.filter(organization=organization, name__iexact=list_name).first()
                if not contact_list:
                    return Response({"error": f"List '{list_name}' not found."}, status=status.HTTP_404_NOT_FOUND)
                
                list_actual_name = contact_list.name
                contact_list.delete()
                return Response({"message": f"List '{list_actual_name}' deleted successfully."})

            else:
                return Response({"error": "Unknown action determined by AI."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Agent error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
