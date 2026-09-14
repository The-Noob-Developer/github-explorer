"""Talks to the Groq chat-completions API to turn natural language into the
structured JSON described in `config/prompts.py`.

Retries are bounded and narrow on purpose: transient network errors and 5xx
responses are worth retrying (the same request will likely succeed a moment
later), but a 4xx or a response that fails JSON parsing is retried zero
times -- retrying with the exact same prompt would almost certainly fail the
exact same way, and "retry with a different prompt until it works" is
explicitly out of scope (Section 3): a bad interpretation should surface as
`groq_invalid_output`, not be silently patched over by prompt-jiggling.
"""

from __future__ import annotations

import asyncio
import json
import logging

import httpx

from app.config.prompts import SYSTEM_PROMPT
from app.models.search_models import SearchInterpretation
from app.utils.errors import GroqInvalidOutputError, GroqUnavailableError
from app.utils.validation import parse_and_validate_interpretation

logger = logging.getLogger("app.groq_service")

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

_MAX_RETRIES = 2
_BACKOFF_BASE_SECONDS = 0.5


async def interpret(
    client: httpx.AsyncClient,
    query: str,
    *,
    api_key: str,
    model: str,
    timeout_seconds: float,
    clarification_context: str | None = None,
) -> str:
    """Send the NL query to Groq and return the raw JSON text it produced.

    `clarification_context` is appended to the user turn when this call is a
    continuation of an earlier `needs_clarification` round-trip (Section 19),
    so Groq sees both the original request and the user's follow-up answer.
    """

    user_content = query
    if clarification_context:
        user_content = f"{query}\n\nUser clarification: {clarification_context}"

    body = {
        "model": model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await client.post(
                GROQ_CHAT_COMPLETIONS_URL,
                json=body,
                headers=headers,
                timeout=timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            last_exc = exc
            logger.warning("Groq request timed out (attempt %s)", attempt + 1)
        except httpx.HTTPError as exc:
            last_exc = exc
            logger.warning("Groq request network error (attempt %s): %s", attempt + 1, exc)
        else:
            if response.status_code >= 500:
                last_exc = GroqUnavailableError()
                logger.warning(
                    "Groq returned 5xx (attempt %s): status=%s", attempt + 1, response.status_code
                )
            elif response.status_code >= 400:
                # 4xx is not retried -- the request itself is malformed/unauthorized
                # and retrying with the same payload will not help.
                logger.error("Groq returned 4xx: status=%s body=%s", response.status_code, response.text[:500])
                raise GroqUnavailableError()
            else:
                try:
                    payload = response.json()
                    return payload["choices"][0]["message"]["content"]
                except (KeyError, IndexError, json.JSONDecodeError) as exc:
                    # The HTTP call succeeded but the response shape was
                    # unexpected -- this is Groq producing something we
                    # can't even extract text from, not a bad *content*.
                    raise GroqInvalidOutputError() from exc

        if attempt < _MAX_RETRIES:
            await asyncio.sleep(_BACKOFF_BASE_SECONDS * (2**attempt))

    logger.error("Groq unavailable after %s attempts: %s", _MAX_RETRIES + 1, last_exc)
    raise GroqUnavailableError()


def parse_and_validate(raw: str) -> SearchInterpretation:
    """Parse and validate Groq's raw JSON text into a `SearchInterpretation`.

    Thin wrapper around `utils.validation.parse_and_validate_interpretation`
    so the pipeline step named in Section 3 (`groq_service.parse_and_validate`)
    lives where callers expect it, while the actual shape-checking logic is
    shared and unit-testable from `utils/validation.py`.
    """

    return parse_and_validate_interpretation(raw)
