"""Calls the served D-q4 model with the prompt of its evaluation and validates the answer."""

import json
import logging
import time

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langfuse import observe
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from flow.contracts import FlowConfig, QualifierResult, Ticket
from flow.prompt_management import PromptRelease, fetch_prompt, record_prompt_release
from ml.qualifier.src.dataset_build.schema import (
    CURRENCIES,
    SENTIMENTS,
    SENTINELS,
    SUB_INTENTS,
    UNDEFINED,
    URGENCIES,
    TicketLabel,
)
from ml.qualifier.src.prompt import INSTRUCTION
from ml.qualifier.src.scoring import parse_output

logger = logging.getLogger(__name__)


def qualifier_output_schema() -> dict[str, object]:
    """JSON Schema used by llama.cpp constrained decoding, derived from the Pydantic contract."""
    schema = TicketLabel.model_json_schema()
    properties = schema["properties"]
    properties["intent"]["enum"] = [*SUB_INTENTS, *SENTINELS]
    properties["sub_intent"]["enum"] = [
        *(sub_intent for values in SUB_INTENTS.values() for sub_intent in values),
        *SENTINELS,
    ]
    properties["currency"]["enum"] = [*CURRENCIES, "", UNDEFINED]
    properties["urgency"]["enum"] = [*URGENCIES, UNDEFINED]
    properties["sentiment"]["enum"] = [*SENTIMENTS, UNDEFINED]
    return schema


def build_qualifier_model(config: FlowConfig) -> Runnable:
    """Build LangChain's structured-output runnable over llama.cpp's OpenAI-compatible API."""
    model = ChatOpenAI(
        base_url=config.qualifier_url,
        api_key="local-llama-cpp",
        model=config.qualifier_model_version,
        temperature=config.qualifier_temperature,
        max_tokens=config.qualifier_max_tokens,
        timeout=config.qualifier_timeout_seconds,
        max_retries=0,  # tenacity below owns bounded transient retries
    )
    return model.with_structured_output(
        qualifier_output_schema(), method="json_schema", strict=True, include_raw=True
    )


def load_qualifier_prompt(config: FlowConfig) -> PromptRelease:
    """Resolve the production prompt from Langfuse, preserving the training instruction as fallback."""
    return fetch_prompt(
        name=config.qualifier_prompt_name,
        label=config.qualifier_prompt_label,
        prompt_type="text",
        fallback=f"{INSTRUCTION}\n\nTicket:\n{{{{ticket}}}}",
    )


@observe(capture_input=False, capture_output=False)
def qualify(
    ticket: Ticket, *, model: Runnable, config: FlowConfig,
    prompt: PromptRelease | None = None,
) -> QualifierResult:
    """Return the validated label. A bad answer is never retried or repaired."""
    start = time.perf_counter()
    prompt = prompt or load_qualifier_prompt(config)
    record_prompt_release(prompt)
    try:
        def is_transient(exc: BaseException) -> bool:
            return isinstance(
                exc, (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)
            )

        @retry(
            retry=retry_if_exception(is_transient),
            stop=stop_after_attempt(config.transient_retries),
            wait=wait_exponential(multiplier=config.retry_wait_seconds, max=20),
            reraise=True,
        )
        def invoke() -> object:
            return model.invoke(prompt.compile(ticket=ticket.message_text))

        answer = invoke()
    except Exception as exc:  # SDK transport/provider errors become a stable flow outcome
        logger.error("Qualifier unavailable for %s: %s", ticket.ticket_id, exc)
        return QualifierResult(
            status="unavailable",
            label=None,
            raw=None,
            model_version=config.qualifier_model_version,
            prompt_name=prompt.name,
            prompt_version=prompt.version,
            latency_seconds=time.perf_counter() - start,
            error=str(exc),
        )
    if isinstance(answer, dict) and "parsed" in answer:
        raw_message = answer.get("raw")
        raw = str(getattr(raw_message, "content", ""))
        if answer.get("parsing_error") is not None or answer.get("parsed") is None:
            return QualifierResult(
                status="invalid", label=None, raw=raw,
                model_version=config.qualifier_model_version,
                prompt_name=prompt.name,
                prompt_version=prompt.version,
                latency_seconds=time.perf_counter() - start,
                error=str(answer.get("parsing_error") or "structured output was empty"),
            )
        raw = json.dumps(answer["parsed"], ensure_ascii=False)
    elif hasattr(answer, "model_dump"):
        raw = answer.model_dump_json()
    elif isinstance(answer, dict):
        raw = json.dumps(answer, ensure_ascii=False)
    else:
        raw = str(answer)
    label = parse_output(raw)
    return QualifierResult(
        status="valid" if label else "invalid",
        label=label,
        raw=raw,
        model_version=config.qualifier_model_version,
        prompt_name=prompt.name,
        prompt_version=prompt.version,
        latency_seconds=time.perf_counter() - start,
    )
