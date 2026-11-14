"""A rejected draft is told apart from an outage; ISO stamps keep their day; the Drafter gets reasons."""

from datetime import UTC, datetime

import httpx
import pytest

from flow.contracts import (
    EvidenceDecision,
    EvidenceFact,
    FlowDeps,
    QualifierResult,
    Ticket,
    load_config,
)
from flow.drafter import _prompt_variables, write_draft
from flow.llm import DraftRejected, LLMError
from flow.pipeline import draft_failure_codes, process, reroute
from flow.policy import PolicyContext, check_draft
from ml.qualifier.src.dataset_build.schema import TicketLabel

TICKET = Ticket(ticket_id="t1", merchant_id="m1", text="help", created_at=datetime(2026, 11, 5, tzinfo=UTC))
LABEL = TicketLabel(
    intent="dispute", sub_intent="chargeback", transaction_id="", amount="", currency="",
    urgency="low", sentiment="neutral",
)
VALID = QualifierResult(status="valid", label=LABEL, raw="{}", model_version="m", latency_seconds=0)


def _rejected(ticket, qualifier, desk, version):
    raise DraftRejected("no citation")


def _down(ticket, qualifier, desk, version):
    raise LLMError("down")


def _deps(draft) -> FlowDeps:
    return FlowDeps(qualify=lambda _: VALID, draft=draft, policy_version="p1")


_FACT = EvidenceFact(field="approved_guidance", value="v", source_id="kb_x", source_version="1")
_DOCUMENTARY = EvidenceDecision(mode="documentary", reason_codes=("EVIDENCE_READY",), source_ids=("kb_x",), facts=(_FACT,))


def test_failure_codes_separate_rejection_from_outage() -> None:
    assert draft_failure_codes(None) == ()
    assert draft_failure_codes("down") == ("DRAFTER_UNAVAILABLE",)
    assert draft_failure_codes("rejected: no citation") == ("DRAFT_REJECTED",)


def test_a_rejected_draft_is_reported_as_rejected_in_the_first_pass() -> None:
    run = process(TICKET, _deps(_rejected))
    assert "DRAFT_REJECTED" in run.reason_codes and "DRAFTER_UNAVAILABLE" not in run.reason_codes
    assert run.draft_error == "rejected: no citation"


def test_a_rejected_draft_is_reported_as_rejected_after_a_reroute() -> None:
    first = process(TICKET, _deps(lambda t, q, d, v: _ok(d, v)))
    run = reroute(first, "payments", FlowDeps(qualify=lambda _: VALID, draft=_rejected, policy_version="p1"))
    assert "DRAFT_REJECTED" in run.reason_codes and "DRAFTER_UNAVAILABLE" not in run.reason_codes


def test_an_outage_is_still_reported_as_unavailable() -> None:
    assert "DRAFTER_UNAVAILABLE" in process(TICKET, _deps(_down)).reason_codes


def _ok(desk, version):
    from flow.contracts import Draft

    return Draft(version=version, text="reply", desk=desk, model="m", prompt_version="p", cost_usd=0,
                 latency_seconds=0)


@pytest.mark.parametrize("content", ["", "cut"])
def test_an_unusable_model_answer_raises_draft_rejected(content: str) -> None:
    reason = "length" if content else "stop"
    reply = {"choices": [{"message": {"content": content}, "finish_reason": reason}]}
    config = load_config().model_copy(update={"retry_wait_seconds": 0.0})
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=reply))
    with httpx.Client(transport=transport) as client, pytest.raises(DraftRejected):
        write_draft(TICKET, VALID, "disputes", 1, client=client, config=config, evidence=_DOCUMENTARY)


def test_the_drafter_receives_the_reason_codes_of_the_evidence_mode() -> None:
    evidence = EvidenceDecision(mode="clarification", reason_codes=("PAYMENT_ID_ABSENT",))
    assert _prompt_variables(TICKET, VALID, "disputes", evidence)["reason_codes"] == "PAYMENT_ID_ABSENT"
    assert _prompt_variables(TICKET, VALID, "disputes", None)["reason_codes"] == "none"


@pytest.mark.parametrize("phrase", ["2026-10-03", "3 October 2026", "le 3 octobre 2026 a 12:00", "2026-10-03 12:00"])
def test_an_iso_stamp_in_the_evidence_allows_the_same_day_written_in_a_draft(phrase: str) -> None:
    context = PolicyContext(merchant_id="m1", allowed_figures=("2026-10-03T12:00:00Z",))
    assert "UNSUPPORTED_FIGURE" not in check_draft(f"Your payment was updated on {phrase}.", context).findings


def test_another_day_is_still_unsupported() -> None:
    context = PolicyContext(merchant_id="m1", allowed_figures=("2026-10-03T12:00:00Z",))
    assert "UNSUPPORTED_FIGURE" in check_draft("Your payment was updated on 2026-10-17.", context).findings
