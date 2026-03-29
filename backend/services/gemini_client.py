"""Shared Gemini client for LLM-enhanced agent reasoning."""

import json
import logging
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)

_client = None
MODEL = "gemini-3.1-pro-preview"


def _get_client():
    """Lazy-initialize the Gemini client."""
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            return None
        try:
            import google.genai as genai
            _client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("Gemini client initialized (model=%s)", MODEL)
        except Exception as e:
            logger.warning("Failed to initialize Gemini client: %s", e)
            return None
    return _client


async def generate(prompt: str, system_instruction: str = "", json_mode: bool = False) -> str | None:
    """Generate text with Gemini. Returns None if unavailable.

    Args:
        prompt: The user prompt.
        system_instruction: Optional system instruction.
        json_mode: If True, request JSON output.

    Returns:
        Generated text string, or None if Gemini is unavailable/fails.
    """
    client = _get_client()
    if client is None:
        return None

    try:
        config: dict[str, Any] = {}
        if system_instruction:
            config["system_instruction"] = system_instruction
        if json_mode:
            config["response_mime_type"] = "application/json"

        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=config,
        )
        return resp.text.strip() if resp.text else None
    except Exception as e:
        logger.warning("Gemini generation failed: %s", e)
        return None


async def generate_json(prompt: str, system_instruction: str = "") -> dict | None:
    """Generate and parse JSON from Gemini. Returns None on failure."""
    text = await generate(prompt, system_instruction, json_mode=True)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Gemini returned invalid JSON: %s", text[:200])
        return None
