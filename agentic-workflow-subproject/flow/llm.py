"""Bounded JSON POST shared by the Qualifier and Drafter calls."""

import json

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

MAX_RETRY_WAIT_SECONDS = 20


class LLMError(RuntimeError):
    """No usable answer: failed exchange, exhausted retries or unexpected response shape."""


class _TransientError(LLMError):
    """Network error, timeout, 429 or 5xx: worth a short retry."""


def post_json(
    client: httpx.Client,
    url: str,
    body: dict[str, object],
    *,
    headers: dict[str, str] | None = None,
    timeout_seconds: float,
    retries: int,
    wait_seconds: float,
) -> dict[str, object]:
    """POST a JSON body and return the decoded object. Every failure ends as ``LLMError``."""

    @retry(
        retry=retry_if_exception_type(_TransientError),
        stop=stop_after_attempt(retries),
        wait=wait_exponential(multiplier=wait_seconds, max=MAX_RETRY_WAIT_SECONDS),
        reraise=True,
    )
    def attempt() -> dict[str, object]:
        try:
            response = client.post(url, json=body, headers=headers, timeout=timeout_seconds)
        except httpx.TransportError as exc:
            raise _TransientError(f"{type(exc).__name__} calling {url}") from exc
        if response.status_code == 429 or response.status_code >= 500:
            raise _TransientError(f"HTTP {response.status_code} from {url}")
        if response.status_code >= 400:
            raise LLMError(f"HTTP {response.status_code} from {url}: {response.text[:200]}")
        try:
            decoded = response.json()
        except json.JSONDecodeError as exc:
            raise LLMError(f"non-JSON response from {url}") from exc
        if not isinstance(decoded, dict):
            raise LLMError(f"unexpected response shape from {url}")
        return decoded

    return attempt()
