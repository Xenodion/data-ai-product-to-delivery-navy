import json
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from flow.contracts import FlowConfig, QualifierResult, Ticket, load_config
from flow.qualifier import build_prompt, qualify

VALID = json.dumps(
    {
        "intent": "dispute",
        "sub_intent": "chargeback",
        "transaction_id": "TX-123456",
        "amount": "10.00",
        "currency": "EUR",
        "urgency": "low",
        "sentiment": "neutral",
    }
)
TICKET = Ticket(ticket_id="t1", merchant_id="m1", text="hello", created_at=datetime(2026, 11, 5, tzinfo=UTC))


def _config() -> FlowConfig:
    return load_config().model_copy(update={"retry_wait_seconds": 0.0})


def _call(handler: Callable[[httpx.Request], httpx.Response]) -> tuple[QualifierResult, list[httpx.Request]]:
    calls: list[httpx.Request] = []

    def counting(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    with httpx.Client(transport=httpx.MockTransport(counting)) as client:
        return qualify(TICKET, client=client, config=_config()), calls


def test_qualify_returns_label_when_output_is_valid() -> None:
    result, calls = _call(lambda _: httpx.Response(200, json={"content": VALID + "<|im_end|>"}))
    assert result.status == "valid"
    assert result.label is not None
    assert result.label.intent == "dispute"
    assert json.loads(calls[0].content)["temperature"] == 0.0


def test_qualify_never_retries_or_repairs_malformed_output() -> None:
    result, calls = _call(lambda _: httpx.Response(200, json={"content": '{"intent": "dispute"'}))
    assert (result.status, result.label) == ("invalid", None)
    assert result.raw == '{"intent": "dispute"'
    assert len(calls) == 1


def test_qualify_is_unavailable_after_transient_retries() -> None:
    result, calls = _call(lambda _: httpx.Response(503))
    assert result.status == "unavailable"
    assert len(calls) == _config().transient_retries


def test_qualify_is_unavailable_on_client_error_without_retry() -> None:
    result, calls = _call(lambda _: httpx.Response(400))
    assert result.status == "unavailable"
    assert len(calls) == 1


def test_qualify_recovers_when_a_transient_error_clears() -> None:
    answers = iter([httpx.Response(503), httpx.Response(200, json={"content": VALID})])
    result, calls = _call(lambda _: next(answers))
    assert result.status == "valid"
    assert len(calls) == 2


def test_build_prompt_wraps_ticket_in_chat_turns() -> None:
    prompt = build_prompt("my ticket")
    assert prompt.endswith("Ticket:\nmy ticket<|im_end|>\n<|im_start|>assistant\n")
