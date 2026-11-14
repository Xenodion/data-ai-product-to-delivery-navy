"""A clarification reads the approved guidance (never the ledger) so that its question is specific."""

from datetime import UTC, datetime

from flow import tools
from flow.contracts import ContextPlan, Ticket, load_config
from flow.evidence import decide_evidence

TICKET = Ticket(
    ticket_id="t1", merchant_id="M-DEMO", created_at=datetime(2026, 11, 5, tzinfo=UTC),
    text="My payment is missing and has not arrived, please check the missing payment.",
)


def _plan(**overrides: object) -> ContextPlan:
    values = {
        "desk": "payments", "merchant_id": "M-DEMO", "sub_intent": "missing_payment",
        "ledger_required": True, "knowledge_required": True, "status": "clarification",
        "reason_codes": ("PAYMENT_ID_ABSENT",),
    }
    return ContextPlan(**(values | overrides))


def test_a_clarification_reads_guidance_and_never_the_ledger() -> None:
    result = tools.gather_evidence(TICKET, _plan(), load_config())
    assert result.ledger.status == "not_required"
    assert result.retrieval.status == "found" and result.retrieval.facts


def test_the_evidence_gate_keeps_the_clarification_and_carries_the_guidance() -> None:
    plan = _plan()
    decision = decide_evidence(plan, tools.gather_evidence(TICKET, plan, load_config()))
    assert decision.mode == "clarification" and decision.reason_codes == ("PAYMENT_ID_ABSENT",)
    assert decision.facts and set(decision.source_ids) == {f.source_id for f in decision.facts}
    assert decision.allowed_figures == ()


def test_a_clarification_without_guidance_stays_a_plain_question() -> None:
    plan = _plan(sub_intent="no_such_intent")
    decision = decide_evidence(plan, tools.gather_evidence(TICKET, plan, load_config()))
    assert decision.mode == "clarification" and decision.facts == () and decision.source_ids == ()


def test_a_human_only_plan_still_reads_nothing() -> None:
    plan = _plan(status="human_only", ledger_required=False, knowledge_required=False)
    result = tools.gather_evidence(TICKET, plan, load_config())
    assert (result.ledger.status, result.retrieval.status) == ("not_required", "not_required")
