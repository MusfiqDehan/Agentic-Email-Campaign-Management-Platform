"""
Shared AI generation helpers.

Primary: Google Gemini
Fallback: DeepSeek (OpenAI-compatible) when Gemini hits rate/quota limits.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx
from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"
GEMINI_MODEL = "gemini-3.5-flash-lite"


class AIConfigurationError(Exception):
    """Raised when no usable AI provider is configured."""


class AIGenerationError(Exception):
    """Raised when all AI providers fail to generate content."""


def _is_rate_limit_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    markers = (
        "429",
        "rate limit",
        "rate_limit",
        "quota",
        "resource_exhausted",
        "resource exhausted",
        "too many requests",
        "exceeded your current quota",
        "insufficient_quota",
    )
    return any(marker in message for marker in markers)


def _generate_with_gemini(prompt: str) -> str:
    api_key = getattr(settings, "GEMINI_API_KEY", None) or ""
    if not api_key:
        raise AIConfigurationError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    text = (response.text or "").strip()
    if not text:
        raise AIGenerationError("Gemini returned an empty response.")
    return text


def _generate_with_deepseek(prompt: str) -> str:
    api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or ""
    if not api_key:
        raise AIConfigurationError("DEEPSEEK_API_KEY is not configured.")

    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a precise assistant. Return ONLY a valid JSON object. "
                    "Do not wrap the response in markdown fences."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=90.0) as client:
        response = client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise AIGenerationError(
                f"DeepSeek request failed ({response.status_code}): {response.text[:500]}"
            )
        data = response.json()

    try:
        text = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise AIGenerationError(f"Unexpected DeepSeek response shape: {data}") from exc

    if not text:
        raise AIGenerationError("DeepSeek returned an empty response.")
    return text


def generate_json_text(prompt: str) -> tuple[str, str]:
    """
    Generate model text expected to be JSON.

    Returns:
        (text, provider_name) where provider_name is 'gemini' or 'deepseek'.
    """
    gemini_key = getattr(settings, "GEMINI_API_KEY", None) or ""
    deepseek_key = getattr(settings, "DEEPSEEK_API_KEY", None) or ""

    if not gemini_key and not deepseek_key:
        raise AIConfigurationError(
            "Neither GEMINI_API_KEY nor DEEPSEEK_API_KEY is configured."
        )

    last_error: Optional[BaseException] = None

    if gemini_key:
        try:
            return _generate_with_gemini(prompt), "gemini"
        except Exception as exc:  # noqa: BLE001 - provider boundary
            last_error = exc
            # Fall back to DeepSeek on rate limits OR when DeepSeek is configured
            # and Gemini fails for any recoverable reason (timeouts, 5xx, empty).
            can_fallback = bool(deepseek_key) and (
                _is_rate_limit_error(exc)
                or any(
                    marker in str(exc).lower()
                    for marker in ("timeout", "503", "502", "500", "unavailable", "empty response")
                )
            )
            if not can_fallback:
                raise AIGenerationError(f"Gemini AI generation failed: {exc}") from exc
            logger.warning(
                "Gemini failed; falling back to DeepSeek: %s",
                exc,
            )

    if deepseek_key:
        try:
            return _generate_with_deepseek(prompt), "deepseek"
        except Exception as exc:  # noqa: BLE001 - provider boundary
            if last_error is not None:
                raise AIGenerationError(
                    f"AI generation failed after Gemini and DeepSeek attempts. "
                    f"Gemini: {last_error}; DeepSeek: {exc}"
                ) from exc
            raise AIGenerationError(f"DeepSeek AI generation failed: {exc}") from exc

    raise AIGenerationError(f"AI generation failed: {last_error}")
