import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from flow.contracts import Draft, FlowDeps, QualifierResult, Route, Ticket, TicketRun
from flow.llm import LLMError
from flow.pipeline import process
from flow.runner import VAL_PATH, run_tickets, select_tickets


def _unavailable(_: Ticket) -> QualifierResult:
    return QualifierResult(status="unavailable", label=None, raw=None, model_version="m", latency_seconds=0)


def _no_draft(ticket: Ticket, qualifier: QualifierResult, desk: Route, version: int) -> Draft:
    raise LLMError("down")


DEPS = FlowDeps(qualify=_unavailable, draft=_no_draft, policy_version="p1")


def _csv(path: Path, rows: int) -> Path:
    lines = ["card_id,ticket,target"] + [f"c{i},text {i},SECRET" for i in range(rows)]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_select_tickets_is_repeatable_with_a_seed(tmp_path: Path) -> None:
    source = _csv(tmp_path / "val.csv", 20)
    first = [t.ticket_id for t in select_tickets(source, 5, 7, "m")]
    assert first == [t.ticket_id for t in select_tickets(source, 5, 7, "m")]
    assert first != [t.ticket_id for t in select_tickets(source, 5, 8, "m")]


def test_select_tickets_never_carries_expected_labels(tmp_path: Path) -> None:
    ticket = select_tickets(_csv(tmp_path / "val.csv", 3), 1, 7, "m")[0]
    assert "SECRET" not in ticket.model_dump_json()


def test_ticket_refuses_a_target_field() -> None:
    with pytest.raises(ValidationError):
        Ticket(ticket_id="t", merchant_id="m", text="x", created_at="2026-11-05T00:00:00Z", target="y")


def test_val_path_points_at_the_validation_split() -> None:
    assert VAL_PATH.name == "val.csv"


def test_run_tickets_keeps_finished_lines_when_a_ticket_crashes(tmp_path: Path) -> None:
    tickets = select_tickets(_csv(tmp_path / "val.csv", 3), 3, 7, "m")
    output = tmp_path / "runs" / "run.jsonl"
    seen: list[str] = []

    def crash_on_second(ticket: Ticket, deps: FlowDeps) -> TicketRun:
        seen.append(ticket.ticket_id)
        if len(seen) == 2:
            raise RuntimeError("boom")
        return process(ticket, deps)

    with pytest.raises(RuntimeError):
        run_tickets(tickets, DEPS, output, step=crash_on_second)
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["ticket"]["ticket_id"] == tickets[0].ticket_id
