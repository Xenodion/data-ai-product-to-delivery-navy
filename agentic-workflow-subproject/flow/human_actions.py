"""Validator and simulated-send actions (nodes 13–15)."""

from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal

from langfuse import observe

from flow.contracts import (
    Draft,
    HumanActionEvent,
    SendDisposition,
    SimulatedSendReceipt,
    TicketRun,
)
from flow.policy import PolicyContext, check_final_text, can_approve_model_draft


def _actor(value: str) -> str:
    actor = value.strip()
    if not actor:
        raise ValueError("actor is required for human actions")
    return actor


def _event(
    action: Literal[
        "edit", "write", "approve", "handoff", "reroute", "close", "send", "send_blocked"
    ],
    actor: str,
    text: str,
    reason: str | None = None,
    send_disposition: SendDisposition | None = None,
) -> HumanActionEvent:
    return HumanActionEvent(
        action=action,
        actor=_actor(actor),
        reason=reason.strip() if reason and reason.strip() else None,
        text_sha256=sha256(text.encode("utf-8")).hexdigest(),
        send_disposition=send_disposition,
        created_at=datetime.now(UTC),
    )


@observe(capture_input=False, capture_output=False)
def edit_draft(run: TicketRun, text: str, *, actor: str) -> TicketRun:
    """Store a human edit as a new version and invalidate any prior approval."""
    if run.status not in {"awaiting_validation", "ready_to_send"}:
        raise ValueError("ticket is not at the Validator")
    if not text.strip():
        raise ValueError("edited reply must not be empty")
    current = next((draft for draft in reversed(run.drafts) if not draft.stale), None)
    if current is None:
        raise ValueError("there is no current draft to edit")
    stale = tuple(d.model_copy(update={"stale": True}) for d in run.drafts)
    edited = current.model_copy(
        update={
            "version": max((d.version for d in run.drafts), default=0) + 1,
            "text": text,
            "model": "human-edit",
            "prompt_version": "human-edit-v1",
            "cost_usd": 0.0,
            "latency_seconds": 0.0,
            "stale": False,
            "blocked": False,
        }
    )
    return run.model_copy(
        update={
            "drafts": (*stale, edited),
            "status": "awaiting_validation",
            "final_text": text,
            "final_author": "human",
            "approved_by": None,
            "policy_check": None,
            "final_policy_check": None,
            "send_key": None,
            "send_disposition": None,
            "send_receipt": None,
            "human_actions": (*run.human_actions, _event("edit", actor, text)),
        }
    )


@observe(capture_input=False, capture_output=False)
def write_reply(run: TicketRun, text: str, *, actor: str) -> TicketRun:
    """Record a person-written response, still awaiting explicit approval."""
    if run.status not in {"awaiting_validation", "awaiting_reroute", "manual_handling"}:
        raise ValueError("ticket is not waiting for a human response")
    if not text.strip():
        raise ValueError("reply must not be empty")
    evidence = run.evidence_decision
    version = max((draft.version for draft in run.drafts), default=0) + 1
    written = Draft(
        version=version,
        text=text,
        desk=run.desk,
        model="human-write",
        prompt_version="human-write-v1",
        cost_usd=0.0,
        latency_seconds=0.0,
        evidence_mode=evidence.mode if evidence else "clarification",
        source_ids=evidence.source_ids if evidence else (),
        source_versions=(
            tuple(sorted({(fact.source_id, fact.source_version) for fact in evidence.facts}))
            if evidence
            else ()
        ),
    )
    stale = tuple(item.model_copy(update={"stale": True}) for item in run.drafts)
    return run.model_copy(
        update={
            "drafts": (*stale, written),
            "final_text": text,
            "final_author": "human",
            "approved_by": None,
            "final_policy_check": None,
            "status": "awaiting_validation",
            "send_key": None,
            "send_disposition": None,
            "send_receipt": None,
            "human_actions": (*run.human_actions, _event("write", actor, text)),
        }
    )


@observe(capture_input=False, capture_output=False)
def approve_reply(run: TicketRun, *, actor: str) -> TicketRun:
    """Record an explicit approval of the exact current reply text."""
    if run.status not in {"awaiting_validation", "manual_handling"}:
        raise ValueError("ticket is not awaiting approval")
    text = run.final_text
    if not text or not text.strip():
        raise ValueError("there is no reply to approve")
    if run.final_author not in {"model", "human"}:
        raise ValueError("reply author is missing")
    if run.final_author == "model":
        current = next((d for d in reversed(run.drafts) if not d.stale), None)
        if current is None or current.text != text or run.policy_check is None:
            raise ValueError("model draft is missing or no longer matches its policy check")
        if not can_approve_model_draft(current, run.policy_check):
            raise ValueError("model draft is blocked, stale, empty, or has not passed policy")
    return run.model_copy(
        update={
            "status": "ready_to_send",
            "approved_by": _actor(actor),
            "human_actions": (*run.human_actions, _event("approve", actor, text)),
        }
    )


@observe(capture_input=False, capture_output=False)
def handoff_to_rerouter(run: TicketRun, *, actor: str, reason: str) -> TicketRun:
    """Invalidate the current reply and return a Validator case to the Re-router."""
    if run.status != "awaiting_validation":
        raise ValueError("only a ticket at the Validator can be handed off")
    note = reason.strip()
    if not note:
        raise ValueError("handoff reason is required")
    stale = tuple(d.model_copy(update={"stale": True}) for d in run.drafts)
    return run.model_copy(
        update={
            "status": "awaiting_reroute",
            "desk": "triage",
            "drafts": stale,
            "final_text": None,
            "final_author": None,
            "approved_by": None,
            "policy_check": None,
            "final_policy_check": None,
            "human_actions": (*run.human_actions, _event("handoff", actor, note, note)),
        }
    )


@observe(capture_input=False, capture_output=False)
def close_manual(run: TicketRun, *, actor: str, reason: str) -> TicketRun:
    """Close a manual case without sending a message."""
    if run.status != "manual_handling":
        raise ValueError("only a manually handled ticket can be closed manually")
    note = reason.strip()
    if not note:
        raise ValueError("closure reason is required")
    return run.model_copy(
        update={
            "status": "closed_manual",
            "approved_by": None,
            "final_text": None,
            "final_author": None,
            "human_actions": (*run.human_actions, _event("close", actor, note, note)),
        }
    )


@observe(capture_input=False, capture_output=False)
def send_simulated(
    run: TicketRun,
    *,
    actor: str,
    idempotency_key: str,
    disposition: SendDisposition,
    override_reason: str | None = None,
) -> TicketRun:
    """Run node 14 against the exact approved text, then record one simulated send."""
    key = idempotency_key.strip()
    if not key:
        raise ValueError("idempotency_key is required")
    if disposition not in {"leave_open", "close"}:
        raise ValueError("send disposition must be explicitly selected")
    if run.status in {"sent_open", "sent_closed"}:
        if run.send_key == key and run.send_disposition == disposition:
            return run
        raise ValueError("ticket was already sent with a different idempotency key")
    if run.status != "ready_to_send" or not run.approved_by:
        raise ValueError("explicit human approval is required before sending")
    text = run.final_text
    if not text or not text.strip():
        raise ValueError("approved reply is empty")
    if run.final_author not in {"model", "human"}:
        raise ValueError("reply author is missing")

    evidence = run.evidence_decision
    result = check_final_text(
        text,
        PolicyContext(
            merchant_id=run.ticket.merchant_id,
            allowed_figures=evidence.allowed_figures if evidence else (),
            approved_source_ids=evidence.source_ids if evidence else (),
            foreign_identifiers=run.foreign_identifiers,
            evidence_facts=evidence.facts if evidence else (),
        ),
        author=run.final_author,
        override_reason=override_reason,
    )
    if result.status != "pass":
        return run.model_copy(
            update={
                "status": "awaiting_validation",
                "approved_by": None,
                "send_key": None,
                # Preserve the last successful receipt; the failed attempt is an action event.
                "send_receipt": run.send_receipt,
                "final_policy_check": result,
                "human_actions": (
                    *run.human_actions,
                    _event(
                        "send_blocked", actor, text, ",".join(result.findings),
                        send_disposition=disposition,
                    ),
                ),
            }
        )

    now = datetime.now(UTC)
    status = "sent_closed" if disposition == "close" else "sent_open"
    receipt = SimulatedSendReceipt(
        send_key=key,
        ticket_id=run.ticket.ticket_id,
        text_sha256=result.content_sha256,
        policy_version=run.decision.policy_version,
        disposition=disposition,
        created_at=now,
    )
    return run.model_copy(
        update={
            "status": status,
            "send_key": key,
            "send_disposition": disposition,
            "final_policy_check": result,
            "send_receipt": receipt,
            "send_receipts": (*run.send_receipts, receipt),
            "human_actions": (
                *run.human_actions,
                HumanActionEvent(
                    action="send",
                    actor=_actor(actor),
                    reason=result.override_reason,
                    text_sha256=result.content_sha256,
                    send_disposition=disposition,
                    created_at=now,
                ),
            ),
        }
    )
