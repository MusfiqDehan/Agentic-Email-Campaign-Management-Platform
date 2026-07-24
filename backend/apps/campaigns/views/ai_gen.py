from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from apps.campaigns.utils.ai_client import (
    AIConfigurationError,
    AIGenerationError,
    generate_json_text,
)

logger = logging.getLogger(__name__)


def _parse_json_payload(text_content: str):
    cleaned = text_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).replace("```", "")
    elif cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "")
    return json.loads(cleaned.strip())


class GenerateEmailContentAIView(APIView):
    """
    API View to generate email content using Gemini, with DeepSeek fallback on rate limits.
    """

    def post(self, request):
        subject = request.data.get('email_subject')
        template_name = request.data.get('template_name')

        if not subject or not template_name:
            return Response(
                {"error": "Both 'email_subject' and 'template_name' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        try:
            text_content, provider = generate_json_text(prompt)
            content_data = _parse_json_payload(text_content)
            content_data["_provider"] = provider
            return Response(content_data, status=status.HTTP_200_OK)
        except AIConfigurationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except json.JSONDecodeError:
            return Response(
                {"error": "Failed to parse AI response as JSON."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except AIGenerationError as exc:
            logger.error("AI generation failed: %s", exc)
            return Response(
                {"error": f"AI generation failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error("Unexpected AI generation failure: %s", e)
            return Response(
                {"error": f"AI generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
