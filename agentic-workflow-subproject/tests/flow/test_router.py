import pytest

from flow.contracts import QualifierResult
from flow.router import decide_route
from research.qualifier.src.dataset_build.schema import TicketLabel


def _label(**changes: str) -> TicketLabel:
    fields = {
        "intent": "payment_status",
        "sub_intent": "delayed_credit",
        "transaction_id": "",
        "amount": "",
        "currency": "",
        "urgency": "medium",
        "sentiment": "neutral",
    }
    return TicketLabel(**(fields | changes))


def _valid(**changes: str) -> QualifierResult:
    return QualifierResult(status="valid", label=_label(**changes), raw="{}", model_version="m", latency_seconds=0)


@pytest.mark.parametrize(
    ("intent", "sub_intent", "desk"),
    [
        ("payment_status", "delayed_credit", "payments"),
        ("dispute", "chargeback", "disputes"),
        ("technical_api", "api_error", "technical_api"),
        ("compliance", "kyc_update", "compliance"),
    ],
)
def test_decide_route_maps_supported_intent_to_desk(intent: str, sub_intent: str, desk: str) -> None:
    decision = decide_route(_valid(intent=intent, sub_intent=sub_intent), "p1")
    assert decision.desk == desk
    assert decision.reason_codes == ("DESK_FROM_SUPPORTED_INTENT",)
    assert decision.policy_version == "p1"


@pytest.mark.parametrize(
    ("intent", "reason"), [("UNDEFINED", "INTENT_UNDECIDABLE"), ("OTHER", "INTENT_UNSUPPORTED")]
)
def test_decide_route_sends_unroutable_intent_to_triage_and_keeps_urgency(intent: str, reason: str) -> None:
    decision = decide_route(_valid(intent=intent, sub_intent=intent, urgency="high"), "p1")
    assert decision.desk == "triage"
    assert decision.priority == "high"
    assert decision.reason_codes == (reason, "HIGH_PRIORITY_SURFACE_ONLY")


@pytest.mark.parametrize(
    ("status", "reason"), [("invalid", "QUALIFIER_INVALID"), ("unavailable", "QUALIFIER_UNAVAILABLE")]
)
def test_decide_route_gives_unknown_priority_without_label(status: str, reason: str) -> None:
    result = QualifierResult(status=status, label=None, raw=None, model_version="m", latency_seconds=0)
    decision = decide_route(result, "p1")
    assert (decision.desk, decision.priority, decision.reason_codes) == ("triage", "unknown", (reason,))


def test_decide_route_marks_undefined_urgency_as_unknown_priority() -> None:
    decision = decide_route(_valid(urgency="UNDEFINED"), "p1")
    assert decision.desk == "payments"
    assert decision.priority == "unknown"
    assert "PRIORITY_UNKNOWN" in decision.reason_codes


def test_decide_route_keeps_desk_when_sentiment_is_undefined() -> None:
    decision = decide_route(_valid(sentiment="UNDEFINED"), "p1")
    assert decision.desk == "payments"
    assert "SENTIMENT_NEUTRAL_FALLBACK" in decision.reason_codes


def test_decide_route_is_repeatable() -> None:
    assert decide_route(_valid(), "p1") == decide_route(_valid(), "p1")
