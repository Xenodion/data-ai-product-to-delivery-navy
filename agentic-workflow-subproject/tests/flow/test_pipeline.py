from datetime import UTC, datetime
from pathlib import Path

import pytest

from flow.contracts import (
    Draft,
    DraftWriter,
    FlowDeps,
    QualifierResult,
    Route,
    Ticket,
    TicketRun,
)
from flow.llm import LLMError
from flow.pipeline import process, reroute
from ml.qualifier.src.dataset_build.schema import TicketLabel

TICKET = Ticket(ticket_id="t1", merchant_id="m1", text="hello", created_at=datetime(2026, 11, 5, tzinfo=UTC))
LABEL = TicketLabel(
    intent="dispute",
    sub_intent="chargeback",
    transaction_id="",
    amount="",
    currency="",
    urgency="high",
    sentiment="neutral",
)
VALID = QualifierResult(status="valid", label=LABEL, raw="{}", model_version="m", latency_seconds=0)
UNAVAILABLE = QualifierResult(status="unavailable", label=None, raw=None, model_version="m", latency_seconds=0)
INVALID = UNAVAILABLE.model_copy(update={"status": "invalid", "raw": "oops"})


def _write(ticket: Ticket, qualifier: QualifierResult, desk: Route, version: int) -> Draft:
    return Draft(
        version=version, text="reply", desk=desk, model="m", prompt_version="p", cost_usd=0, latency_seconds=0
    )


def _fail(ticket: Ticket, qualifier: QualifierResult, desk: Route, version: int) -> Draft:
    raise LLMError("down")


def _deps(result: QualifierResult = VALID, draft: DraftWriter = _write) -> FlowDeps:
    return FlowDeps(qualify=lambda _: result, draft=draft, policy_version="p1")


def _no_qualifier(_: Ticket) -> QualifierResult:
    raise AssertionError("a correction must not call the Qualifier")


def _fixing(draft: DraftWriter = _write) -> FlowDeps:
    return FlowDeps(qualify=_no_qualifier, draft=draft, policy_version="p1")


def test_traced_functions_never_capture_their_arguments() -> None:
    for module in (Path("flow/pipeline.py"), Path("flow/qualifier.py"), Path("flow/drafter.py")):
        source = module.read_text(encoding="utf-8")
        assert "@observe(capture_input=False)" in source
        assert "@observe()" not in source


def test_process_waits_for_validation_on_a_known_desk() -> None:
    run = process(TICKET, _deps())
    assert (run.desk, run.status, len(run.drafts)) == ("disputes", "awaiting_validation", 1)
    assert run.decision.priority == "high"


@pytest.mark.parametrize(
    ("result", "reason"), [(INVALID, "QUALIFIER_INVALID"), (UNAVAILABLE, "QUALIFIER_UNAVAILABLE")]
)
def test_process_still_drafts_when_qualifier_fails(result: QualifierResult, reason: str) -> None:
    run = process(TICKET, _deps(result))
    assert (run.desk, run.status, len(run.drafts)) == ("triage", "awaiting_reroute", 1)
    assert run.reason_codes == (reason,)


def test_process_goes_to_manual_handling_when_drafter_fails_on_a_known_desk() -> None:
    run = process(TICKET, _deps(draft=_fail))
    assert (run.desk, run.status, run.drafts) == ("disputes", "manual_handling", ())
    assert "DRAFTER_UNAVAILABLE" in run.reason_codes
    assert run.draft_error == "down"


def test_process_stays_with_rerouter_when_drafter_fails_on_unknown_desk() -> None:
    run = process(TICKET, _deps(UNAVAILABLE, _fail))
    assert (run.desk, run.status, run.drafts) == ("triage", "awaiting_reroute", ())


def test_reroute_first_change_writes_one_new_draft_and_keeps_the_old_one() -> None:
    run = reroute(process(TICKET, _deps()), "payments", _fixing())
    assert (run.desk, run.status, run.reroute_count) == ("payments", "awaiting_validation", 1)
    assert [(d.version, d.stale, d.desk) for d in run.drafts] == [(1, True, "disputes"), (2, False, "payments")]
    assert run.decision.desk == "disputes"
    assert "FIRST_REROUTE_RECOMPUTE" in run.reason_codes


def test_reroute_first_change_goes_to_manual_handling_when_drafter_fails() -> None:
    run = reroute(process(TICKET, _deps()), "payments", _fixing(_fail))
    assert (run.desk, run.status) == ("payments", "manual_handling")
    assert [d.stale for d in run.drafts] == [True]
    assert {"FIRST_REROUTE_RECOMPUTE", "DRAFTER_UNAVAILABLE"} <= set(run.reason_codes)


def test_reroute_second_change_goes_to_manual_handling_without_a_new_draft() -> None:
    first = reroute(process(TICKET, _deps()), "payments", _fixing())
    second = reroute(first, "compliance", _fixing(_fail))
    assert (second.desk, second.status, second.reroute_count) == ("triage", "manual_handling", 2)
    assert len(second.drafts) == 2
    assert all(d.stale for d in second.drafts)
    assert "SECOND_REROUTE_MANUAL" in second.reason_codes


def test_reroute_rejects_a_third_change() -> None:
    run: TicketRun = process(TICKET, _deps())
    run = reroute(reroute(run, "payments", _fixing()), "compliance", _fixing())
    with pytest.raises(ValueError, match="corrections"):
        reroute(run, "payments", _fixing())


@pytest.mark.parametrize("desk", ["disputes", "triage", "nowhere"])
def test_reroute_rejects_current_or_unknown_desk(desk: str) -> None:
    with pytest.raises(ValueError):
        reroute(process(TICKET, _deps()), desk, _fixing())  # type: ignore[arg-type]
