from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from google import genai
import json
import logging

logger = logging.getLogger(__name__)

class GenerateEmailContentAIView(APIView):
    """
    API View to generate email content using Google Gemini AI.
    """
    
    def post(self, request):
        subject = request.data.get('email_subject')
        template_name = request.data.get('template_name')
        
        if not subject or not template_name:
            return Response(
                {"error": "Both 'email_subject' and 'template_name' are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return Response(
                {"error": "GEMINI_API_KEY is not configured in settings."}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
            You are an expert email marketing copywriter.
            Generate an email template based on the following details:
            
            Template Name: {template_name}
            Subject Line: {subject}
            
            Please generate a JSON object with the following fields:
            1. "email_body": The HTML content of the email. Use inline CSS for styling. Use double curly brackets ({{}}) for dynamic content placeholders (e.g., {{first_name}}, {{company_name}}).
            2. "text_body": A plain text version of the email body.
            3. "description": A brief internal description (max 200 chars) explaining the purpose of this email.
            4. "tags": A list of strings (tags) to categorize this email (e.g., ["marketing", "newsletter"]).
            
            There should be no placeholder text like "lorem ipsum" or [Link to Social Media] in the email_body and text_body. Instead, use realistic sample content.
            Ensure the JSON is well-formed.

            Return ONLY the JSON object.
            """

            # Using gemini-2.5-flash-lite as it has good limit.
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite", 
                contents=prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )
            
            # Parse the response
            try:
                text_content = response.text
                # Clean up markdown if present despite mime_type config
                if text_content.strip().startswith("```json"):
                    text_content = text_content.replace("```json", "").replace("```", "")
                
                content_data = json.loads(text_content)
                return Response(content_data, status=status.HTTP_200_OK)
                
            except json.JSONDecodeError:
                return Response(
                    {"error": "Failed to parse AI response as JSON.", "raw_response": response.text},
                    status=status.HTTP_502_BAD_GATEWAY
                )

        except Exception as e:
            logger.error(f"Gemini AI generation failed: {str(e)}")
            return Response(
                {"error": f"AI generation failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )