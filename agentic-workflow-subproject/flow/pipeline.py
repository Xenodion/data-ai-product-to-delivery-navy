"""The ticket flow: from a received ticket to the first human step, and desk corrections."""

import logging
from datetime import UTC, datetime
from typing import get_args

from langfuse import observe

from flow.contracts import (
    Desk,
    Draft,
    EvidenceDecision,
    FlowDeps,
    HumanActionEvent,
    PolicyCheckResult,
    QualifierResult,
    Route,
    RoutingDecision,
    Status,
    Ticket,
    TicketRun,
    load_config,
)
from flow.llm import DraftRejected, LLMError
from flow.field_check import check_fields
from flow.context import plan_context
from flow.evidence import decide_evidence, unavailable_stubs
from flow.policy import PolicyContext, check_draft
from flow.router import decide_later_turn, decide_route
from flow.turns import is_within_automated_turn_limit
from ml.qualifier.src.dataset_build.schema import OTHER, UNDEFINED

logger = logging.getLogger(__name__)

REJECTED_PREFIX = "rejected: "  # draft_error is a plain string; the prefix tells rejection from outage

def _require_next_turn(ticket: Ticket, previous_run: TicketRun | None) -> None:
    if ticket.turn == 1:
        if previous_run is not None:
            raise ValueError("turn 1 cannot have a preceding TicketRun")
        return
    if previous_run is None:
        raise ValueError("later turns require the preceding TicketRun")
    if (
        previous_run.ticket.ticket_id != ticket.ticket_id
        or previous_run.ticket.merchant_id != ticket.merchant_id
        or previous_run.ticket.turn + 1 != ticket.turn
    ):
        raise ValueError("later turn must continue the same ticket and merchant sequentially")


def _next_status(desk: Route) -> Status:
    if desk == "triage":
        return "awaiting_reroute"
    # A failed Drafter still reaches the Validator with context and no draft.
    return "awaiting_validation"


def _attempt_draft(
    ticket: Ticket,
    qualifier: QualifierResult,
    desk: Route,
    version: int,
    deps: FlowDeps,
    evidence: EvidenceDecision | None = None,
) -> tuple[Draft | None, str | None]:
    try:
        if deps.grounded_draft is not None and evidence is not None:
            return deps.grounded_draft(ticket, qualifier, desk, version, evidence=evidence), None
        return deps.draft(ticket, qualifier, desk, version), None
    except DraftRejected as exc:
        logger.error("Draft rejected for %s: %s", ticket.ticket_id, exc)
        return None, f"{REJECTED_PREFIX}{exc}"
    except LLMError as exc:
        logger.error("Draft failed for %s: %s", ticket.ticket_id, exc)
        return None, str(exc)


def draft_failure_codes(error: str | None) -> tuple[str, ...]:
    """Reason code of a failed draft: the model's answer was rejected, or it never answered."""
    if not error:
        return ()
    return ("DRAFT_REJECTED",) if error.startswith(REJECTED_PREFIX) else ("DRAFTER_UNAVAILABLE",)


def _policy_reason_codes(policy: PolicyCheckResult | None) -> tuple[str, ...]:
    if policy is None or policy.status != "blocked":
        return ()
    if "POLICY_CHECK_ERROR" in policy.findings:
        return ("POLICY_CHECK_ERROR", "CONTENT_POLICY_BLOCK")
    return ("CONTENT_POLICY_BLOCK",)


def _carry_history(previous_run: TicketRun | None) -> dict[str, object]:
    if previous_run is None:
        return {}
    return {
        "human_actions": previous_run.human_actions,
        "send_key": previous_run.send_key,
        "send_receipt": previous_run.send_receipt,
        "send_receipts": previous_run.send_receipts,
    }


# Arguments stay out of traces because deps holds the HTTP clients. The output has the ticket.
@observe(capture_input=False, capture_output=False)
def process(
    ticket: Ticket, deps: FlowDeps, *, previous_run: TicketRun | None = None
) -> TicketRun:
    """Run intake gates, Qualifier, Routing Node and Drafter to the first human step."""
    from flow.pipeline_steps import (
        context_plan_step, drafter_step, evidence_gate_step, field_check_step,
        finalize_step, intake_step, qualifier_step, routing_step, tools_step,
        policy_check_step,
    )

    work = intake_step(ticket, deps, previous_run)
    for operation, args in (
        (qualifier_step, (deps,)),
        (field_check_step, ()),
        (routing_step, (deps,)),
        (context_plan_step, (deps,)),
        (tools_step, (deps,)),
        (evidence_gate_step, ()),
        (drafter_step, (deps,)),
        (policy_check_step, ()),
    ):
        work = operation(work, *args)
    return finalize_step(work, deps)

@observe(capture_input=False, capture_output=False)
def reroute(
    run: TicketRun,
    desk: Desk,
    deps: FlowDeps,
    *,
    actor: str | None = None,
    reason: str | None = None,
) -> TicketRun:
    """Apply a human desk correction: one new draft the first time, manual handling the second."""
    if desk not in get_args(Desk):
        raise ValueError(f"not a desk: {desk}")
    if run.status not in {"awaiting_reroute", "awaiting_validation"}:
        raise ValueError(f"ticket {run.ticket.ticket_id} cannot be rerouted from {run.status}")
    if actor is not None and not actor.strip():
        raise ValueError("reroute actor is required")
    if actor is not None and not (reason and reason.strip()):
        raise ValueError("reroute reason is required")
    if desk == run.desk:
        raise ValueError(f"ticket {run.ticket.ticket_id} is already on desk {desk}")
    config = deps.flow_config or load_config()
    max_reroutes = config.max_reroutes
    if run.reroute_count >= max_reroutes:
        raise ValueError(f"ticket {run.ticket.ticket_id} already reached {max_reroutes} corrections")

    reroute_event = (
        HumanActionEvent(
            action="reroute",
            actor=actor.strip(),
            reason=reason.strip() if reason else None,
            created_at=datetime.now(UTC),
        )
        if actor
        else None
    )
    next_actions = (*run.human_actions, reroute_event) if reroute_event else run.human_actions

    stale = tuple(draft.model_copy(update={"stale": True}) for draft in run.drafts)
    if run.reroute_count + 1 == max_reroutes:
        return run.model_copy(
            update={
                "desk": "triage",
                "status": "manual_handling",
                "drafts": stale,
                "reroute_count": max_reroutes,
                "reason_codes": (*run.reason_codes, "SECOND_REROUTE_MANUAL"),
                "draft_error": None,
                "policy_check": None,
                "final_text": None,
                "final_author": None,
                "approved_by": None,
                "human_actions": next_actions,
            }
        )

    label = run.qualifier.label
    if run.qualifier.status != "valid" or label is None or label.intent in {OTHER, UNDEFINED}:
        return run.model_copy(
            update={
                "desk": desk,
                "status": "manual_handling",
                "drafts": stale,
                "reroute_count": run.reroute_count + 1,
                "reason_codes": (*run.reason_codes, "FIRST_REROUTE_RECOMPUTE"),
                "draft_error": None,
                "context_plan": None,
                "evidence_decision": None,
                "policy_check": None,
                "final_text": None,
                "final_author": None,
                "approved_by": None,
                "human_actions": next_actions,
            }
        )

    plan = plan_context(desk, label, run.ticket.merchant_id, run.field_check, config, run.ticket.body)
    tool_results = (
        deps.gather_evidence(run.ticket, plan)
        if deps.gather_evidence is not None and plan.status in {"planned", "clarification"}
        else unavailable_stubs(plan)
    )
    evidence = decide_evidence(plan, tool_results)
    if evidence.mode == "no_draft":
        return run.model_copy(
            update={
                "desk": desk,
                "status": "awaiting_validation",
                "drafts": stale,
                "reroute_count": run.reroute_count + 1,
                "reason_codes": (*run.reason_codes, "FIRST_REROUTE_RECOMPUTE", *evidence.reason_codes),
                "draft_error": None,
                "context_plan": plan,
                "evidence_decision": evidence,
                "policy_check": None,
                "foreign_identifiers": tool_results.ledger.foreign_identifiers,
                "final_text": None,
                "final_author": None,
                "approved_by": None,
                "human_actions": next_actions,
            }
        )

    draft, error = _attempt_draft(
        run.ticket, run.qualifier, desk, len(run.drafts) + 1, deps, evidence=evidence
    )
    policy = (
        check_draft(
            draft.text,
            PolicyContext(
                merchant_id=run.ticket.merchant_id,
                allowed_figures=evidence.allowed_figures,
                approved_source_ids=evidence.source_ids,
                foreign_identifiers=tool_results.ledger.foreign_identifiers,
                evidence_facts=evidence.facts,
            ),
        )
        if draft is not None
        else None
    )
    if draft is not None and policy is not None:
        draft = draft.model_copy(update={"blocked": policy.status == "blocked"})
    failure = draft_failure_codes(error)
    policy_failure = _policy_reason_codes(policy)
    return run.model_copy(
        update={
            "desk": desk,
            "status": _next_status(desk),
            "drafts": (*stale, draft) if draft else stale,
            "reroute_count": run.reroute_count + 1,
            "reason_codes": (
                *run.reason_codes,
                "FIRST_REROUTE_RECOMPUTE",
                *policy_failure,
                *failure,
            ),
            "draft_error": error,
            "policy_check": policy,
            "context_plan": plan,
            "evidence_decision": evidence,
            "foreign_identifiers": tool_results.ledger.foreign_identifiers,
            "final_text": draft.text if draft is not None else None,
            "final_author": "model" if draft is not None else None,
            "approved_by": None,
            "human_actions": next_actions,
        }
    )
