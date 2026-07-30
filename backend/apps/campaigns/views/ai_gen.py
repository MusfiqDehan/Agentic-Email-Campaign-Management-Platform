from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import json
import logging
import re

from apps.campaigns.utils.ai_client import (
    AIConfigurationError,
    AIGenerationError,
    generate_json_text,
)

logger = logging.getLogger(__name__)

VALID_TONES = {
    'professional', 'friendly', 'persuasive', 'urgent', 'warm',
    'playful', 'formal', 'concise',
}

VALID_CATEGORIES = {
    'NEWSLETTER', 'PROMOTIONAL', 'ANNOUNCEMENT', 'WELCOME',
    'EMAIL_VERIFICATION', 'PASSWORD_RESET', 'INVITATION', 'REMINDER',
    'NOTIFICATION', 'SUBSCRIPTION_CONFIRMATION', 'SUBSCRIPTION_RENEWAL',
    'OTHER',
}


def _parse_json_payload(text_content: str):
    cleaned = text_content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).replace("```", "")
    elif cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "")
    return json.loads(cleaned.strip())


def _build_prompt(
    template_name: str,
    subject: str,
    *,
    category: str = 'OTHER',
    tone: str = 'professional',
    audience: str = '',
    cta_text: str = '',
    brand_name: str = '',
    language: str = 'English',
    extra_instructions: str = '',
) -> str:
    audience_line = audience or 'general subscribers of an email marketing platform'
    brand_line = brand_name or 'the organization'
    cta_line = cta_text or 'a clear primary call-to-action button'
    extra = f"\nAdditional instructions from the user:\n{extra_instructions}\n" if extra_instructions else ""

    return f"""
You are an expert email marketing designer and copywriter for a modern SaaS email platform.

Create a production-ready email template with strong visual hierarchy, scannable sections,
and mobile-friendly HTML (single-column, max-width ~600px, inline CSS only).

Inputs:
- Template Name: {template_name}
- Subject Line: {subject}
- Category: {category}
- Tone: {tone}
- Audience: {audience_line}
- Brand / sender organization: {brand_line}
- Primary CTA: {cta_line}
- Language: {language}
{extra}

Return ONLY a valid JSON object with these keys:
1. "email_body": HTML email body (inline CSS). Requirements:
   - Start with a clean header that features the brand name as a strong visual signal
   - One clear hero headline + one short supporting sentence
   - One primary CTA button (use an <a> styled as a button, href="#")
   - Optional secondary content section with 2-3 short bullets or paragraphs
   - Footer MUST include: physical/compliance line AND an unsubscribe link using exactly {{{{unsubscribe_url}}}}
   - Use ONLY these merge tags where personalization is needed:
     {{{{first_name}}}}, {{{{last_name}}}}, {{{{full_name}}}}, {{{{email}}}},
     {{{{organization_name}}}}, {{{{unsubscribe_url}}}}, {{{{current_year}}}}, {{{{campaign_name}}}}
   - Do NOT invent other merge tags. Do NOT use {{{{company_name}}}}.
   - No lorem ipsum, no "[placeholder]", no broken social icon grids
   - Avoid purple-on-white clichés; prefer a clean blue/slate professional palette with subtle gradient header
   - Accessible contrast; font stack: Arial, Helvetica, sans-serif
2. "text_body": Plain-text alternative mirroring the HTML content, including unsubscribe URL as {{{{unsubscribe_url}}}}
3. "preview_text": Inbox preview / preheader (max 90 characters)
4. "description": Internal description of the template purpose (max 200 characters)
5. "tags": Array of 3-6 short lowercase tags (e.g. ["welcome","onboarding","saas"])

Return ONLY the JSON object. No markdown fences.
""".strip()


def _postprocess(content_data: dict) -> dict:
    """Ensure required keys / unsubscribe footer presence."""
    html = content_data.get('email_body') or ''
    text = content_data.get('text_body') or ''

    if '{{unsubscribe_url}}' not in html:
        footer = (
            '<div style="margin-top:32px;padding-top:16px;border-top:1px solid #e5e7eb;'
            'font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#6b7280;text-align:center;">'
            '<p style="margin:0 0 8px;">You are receiving this email from {{organization_name}}.</p>'
            '<p style="margin:0;"><a href="{{unsubscribe_url}}" style="color:#2563eb;">Unsubscribe</a></p>'
            '</div>'
        )
        if re.search(r'</body>', html, re.I):
            html = re.sub(r'</body>', footer + '</body>', html, count=1, flags=re.I)
        else:
            html = html + footer
        content_data['email_body'] = html

    if '{{unsubscribe_url}}' not in text:
        content_data['text_body'] = (
            text.rstrip()
            + "\n\n---\nUnsubscribe: {{unsubscribe_url}}\n"
        )

    # Normalize company_name mistakes
    if content_data.get('email_body'):
        content_data['email_body'] = content_data['email_body'].replace(
            '{{company_name}}', '{{organization_name}}'
        )
    if content_data.get('text_body'):
        content_data['text_body'] = content_data['text_body'].replace(
            '{{company_name}}', '{{organization_name}}'
        )

    if not isinstance(content_data.get('tags'), list):
        content_data['tags'] = []

    return content_data


class GenerateEmailContentAIView(APIView):
    """
    Generate polished email templates with Gemini (DeepSeek fallback).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        subject = (request.data.get('email_subject') or '').strip()
        template_name = (request.data.get('template_name') or '').strip()

        if not subject or not template_name:
            return Response(
                {"error": "Both 'email_subject' and 'template_name' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        category = (request.data.get('category') or 'OTHER').upper()
        if category not in VALID_CATEGORIES:
            category = 'OTHER'

        tone = (request.data.get('tone') or 'professional').lower()
        if tone not in VALID_TONES:
            tone = 'professional'

        audience = (request.data.get('audience') or '').strip()[:300]
        cta_text = (request.data.get('cta_text') or '').strip()[:120]
        language = (request.data.get('language') or 'English').strip()[:40]
        extra_instructions = (request.data.get('extra_instructions') or '').strip()[:800]

        brand_name = ''
        org = getattr(request.user, 'organization', None)
        if org:
            brand_name = org.name

        prompt = _build_prompt(
            template_name,
            subject,
            category=category,
            tone=tone,
            audience=audience,
            cta_text=cta_text,
            brand_name=brand_name,
            language=language,
            extra_instructions=extra_instructions,
        )

        try:
            text_content, provider = generate_json_text(prompt)
            content_data = _parse_json_payload(text_content)
            content_data = _postprocess(content_data)
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
