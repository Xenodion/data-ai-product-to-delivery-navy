"""Calls the served D-q4 model with the prompt of its evaluation and validates the answer."""

import logging
import re
import time

import httpx
from langfuse import observe

from flow.contracts import FlowConfig, QualifierResult, Ticket
from flow.llm import LLMError, post_json
from research.qualifier.src.prompt import build_user_message
from research.qualifier.src.scoring import parse_output

logger = logging.getLogger(__name__)

STOP_TOKENS = ("<|im_end|>", "<|endoftext|>")
# Same text as apply_chat_template on the Qwen tokenizer. The evaluation sent this raw prompt,
# while a chat route would apply the template stored in the GGUF instead.
CHAT_TEMPLATE = (
    "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n"
    "<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
)


def build_prompt(ticket_text: str) -> str:
    return CHAT_TEMPLATE.format(user=build_user_message(ticket_text))


@observe(capture_input=False)
def qualify(ticket: Ticket, *, client: httpx.Client, config: FlowConfig) -> QualifierResult:
    """Return the validated label. A bad answer is never retried or repaired."""
    start = time.perf_counter()
    try:
        answer = post_json(
            client,
            config.qualifier_url,
            {
                "prompt": build_prompt(ticket.text),
                "n_predict": config.qualifier_max_tokens,
                "temperature": 0.0,
                "stop": list(STOP_TOKENS),
            },
            timeout_seconds=config.qualifier_timeout_seconds,
            retries=config.transient_retries,
            wait_seconds=config.retry_wait_seconds,
        )
    except LLMError as exc:
        logger.error("Qualifier unavailable for %s: %s", ticket.ticket_id, exc)
        return QualifierResult(
            status="unavailable",
            label=None,
            raw=None,
            model_version=config.qualifier_model_version,
            latency_seconds=time.perf_counter() - start,
            error=str(exc),
        )
    raw = re.split(r"<\|im_end\|>|<\|endoftext\|>", str(answer.get("content", "")))[0].strip()
    label = parse_output(raw)
    return QualifierResult(
        status="valid" if label else "invalid",
        label=label,
        raw=raw,
        model_version=config.qualifier_model_version,
        latency_seconds=time.perf_counter() - start,
    )
