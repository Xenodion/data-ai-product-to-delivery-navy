from datetime import UTC, datetime

from flow.contracts import FlowConfig, QualifierResult, Ticket, load_config
from flow.prompt_management import PromptRelease
from flow.qualifier import qualify, qualifier_output_schema

VALID = {
    "intent": "dispute", "sub_intent": "chargeback", "transaction_id": "TX-123456",
    "amount": "10.00", "currency": "EUR", "urgency": "low", "sentiment": "neutral",
}
TICKET = Ticket(ticket_id="t1", merchant_id="m1", text="hello", created_at=datetime(2026, 11, 5, tzinfo=UTC))


def _config() -> FlowConfig:
    return load_config().model_copy(update={"retry_wait_seconds": 0.0})


class _StructuredModel:
    def __init__(self, answer: object) -> None:
        self.answer = answer
        self.inputs: list[object] = []

    def invoke(self, value: object) -> object:
        self.inputs.append(value)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


class _Prompt:
    def compile(self, **variables: str) -> str:
        return f"Ticket:\n{variables['ticket']}"


def _call(answer: object) -> tuple[QualifierResult, _StructuredModel]:
    model = _StructuredModel(answer)
    prompt = PromptRelease(_Prompt(), "test/qualifier", "test", "3")
    return qualify(TICKET, model=model, prompt=prompt, config=_config()), model  # type: ignore[arg-type]


def test_qualify_returns_label_when_structured_output_is_valid() -> None:
    result, model = _call(VALID)
    assert result.status == "valid"
    assert result.label is not None and result.label.intent == "dispute"
    assert "Ticket:\nhello" in str(model.inputs[0])


def test_qualifier_schema_is_closed_and_contains_taxonomy_enums() -> None:
    schema = qualifier_output_schema()
    assert schema["additionalProperties"] is False
    assert schema["properties"]["intent"]["enum"]


def test_qualify_keeps_cross_field_validation_after_structured_generation() -> None:
    invalid_pair = {**VALID, "intent": "dispute", "sub_intent": "auth_failure"}
    result, _ = _call(invalid_pair)
    assert (result.status, result.label) == ("invalid", None)


def test_qualify_marks_invalid_structured_payload_invalid() -> None:
    result, _ = _call({"intent": "dispute"})
    assert (result.status, result.label) == ("invalid", None)


def test_qualify_marks_model_transport_error_unavailable() -> None:
    result, _ = _call(RuntimeError("connection failed"))
    assert result.status == "unavailable"
