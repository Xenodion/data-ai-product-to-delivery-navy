"""The ticket flow: from a received ticket to the first human step, and desk corrections."""

import logging
from typing import Final, get_args

from langfuse import observe

from flow.contracts import (
    Desk,
    Draft,
    FlowDeps,
    QualifierResult,
    Route,
    Status,
    Ticket,
    TicketRun,
)
from flow.llm import LLMError
from flow.router import decide_route

logger = logging.getLogger(__name__)

MAX_REROUTES: Final = 2


def _next_status(desk: Route, draft: Draft | None) -> Status:
    if desk == "triage":
        return "awaiting_reroute"
    return "awaiting_validation" if draft else "manual_handling"


def _attempt_draft(
    ticket: Ticket, qualifier: QualifierResult, desk: Route, version: int, deps: FlowDeps
) -> tuple[Draft | None, str | None]:
    try:
        return deps.draft(ticket, qualifier, desk, version), None
    except LLMError as exc:
        logger.error("Draft failed for %s: %s", ticket.ticket_id, exc)
        return None, str(exc)


# Arguments stay out of traces because deps holds the HTTP clients. The output has the ticket.
@observe(capture_input=False)
def process(ticket: Ticket, deps: FlowDeps) -> TicketRun:
    """Run Qualifier, Routing Node and Drafter. The Drafter attempts every ticket."""
    qualifier = deps.qualify(ticket)
    decision = decide_route(qualifier, deps.policy_version)
    draft, error = _attempt_draft(ticket, qualifier, decision.desk, 1, deps)
    failure = ("DRAFTER_UNAVAILABLE",) if error else ()
    return TicketRun(
        ticket=ticket,
        qualifier=qualifier,
        decision=decision,
        desk=decision.desk,
        status=_next_status(decision.desk, draft),
        drafts=(draft,) if draft else (),
        reason_codes=(*decision.reason_codes, *failure),
        draft_error=error,
    )


@observe(capture_input=False)
def reroute(run: TicketRun, desk: Desk, deps: FlowDeps) -> TicketRun:
    """Apply a human desk correction: one new draft the first time, manual handling the second."""
    if desk not in get_args(Desk):
        raise ValueError(f"not a desk: {desk}")
    if desk == run.desk:
        raise ValueError(f"ticket {run.ticket.ticket_id} is already on desk {desk}")
    if run.reroute_count >= MAX_REROUTES:
        raise ValueError(f"ticket {run.ticket.ticket_id} already reached {MAX_REROUTES} corrections")

    stale = tuple(draft.model_copy(update={"stale": True}) for draft in run.drafts)
    if run.reroute_count + 1 == MAX_REROUTES:
        return run.model_copy(
            update={
                "desk": "triage",
                "status": "manual_handling",
                "drafts": stale,
                "reroute_count": MAX_REROUTES,
                "reason_codes": (*run.reason_codes, "SECOND_REROUTE_MANUAL"),
                "draft_error": None,
            }
        )

    draft, error = _attempt_draft(run.ticket, run.qualifier, desk, len(run.drafts) + 1, deps)
    failure = ("DRAFTER_UNAVAILABLE",) if error else ()
    return run.model_copy(
        update={
            "desk": desk,
            "status": _next_status(desk, draft),
            "drafts": (*stale, draft) if draft else stale,
            "reroute_count": run.reroute_count + 1,
            "reason_codes": (*run.reason_codes, "FIRST_REROUTE_RECOMPUTE", *failure),
            "draft_error": error,
        }
    )
