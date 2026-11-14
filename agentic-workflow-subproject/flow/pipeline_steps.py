"""Reusable, checkpointable business steps for the initial ticket pipeline."""

from flow.context import plan_context
from flow.contracts import FlowDeps, PipelineWork, QualifierResult, RoutingDecision, Ticket, TicketRun, load_config
from flow.evidence import decide_evidence, unavailable_stubs
from flow.field_check import check_fields
from flow.pipeline import _attempt_draft, _carry_history, _next_status, _policy_reason_codes
from flow.policy import PolicyContext, check_draft
from flow.router import decide_later_turn, decide_route
from flow.turns import is_within_automated_turn_limit
from ml.qualifier.src.dataset_build.schema import OTHER, UNDEFINED


def intake_step(ticket: Ticket, deps: FlowDeps, previous_run: TicketRun | None) -> PipelineWork:
    """Validate conversation continuity and enforce the configured turn cap."""
    from flow.pipeline import _require_next_turn

    _require_next_turn(ticket, previous_run)
    config = deps.flow_config or load_config()
    if is_within_automated_turn_limit(ticket.turn, config.max_automated_turns):
        return PipelineWork(ticket=ticket, previous_run=previous_run)
    qualifier = QualifierResult(
        status="unavailable", label=None, raw=None, model_version="not_run",
        latency_seconds=0.0, error="turn limit reached",
    )
    desk = previous_run.desk if previous_run is not None else "triage"
    decision = RoutingDecision(
        decision_version=config.routing_version,
        policy_version=deps.policy_version,
        desk=desk,
        priority=previous_run.decision.priority if previous_run is not None else "unknown",
        reason_codes=("TURN_LIMIT_REACHED",),
    )
    old_drafts = previous_run.drafts if previous_run is not None else ()
    early = TicketRun(
        ticket=ticket, qualifier=qualifier, decision=decision, desk=desk,
        status="awaiting_reroute",
        drafts=tuple(item.model_copy(update={"stale": True}) for item in old_drafts),
        reroute_count=previous_run.reroute_count if previous_run is not None else 0,
        reason_codes=("TURN_LIMIT_REACHED",),
        foreign_identifiers=previous_run.foreign_identifiers if previous_run else (),
        **_carry_history(previous_run),
    )
    return PipelineWork(ticket=ticket, previous_run=previous_run, early_run=early)


def qualifier_step(work: PipelineWork, deps: FlowDeps) -> PipelineWork:
    if work.early_run is not None:
        return work
    return work.model_copy(update={"qualifier": deps.qualify(work.ticket)})


def field_check_step(work: PipelineWork) -> PipelineWork:
    if work.early_run is not None or work.qualifier is None:
        return work
    result = check_fields(work.ticket, work.qualifier.label) if work.qualifier.label else None
    return work.model_copy(update={"field_check": result})


def routing_step(work: PipelineWork, deps: FlowDeps) -> PipelineWork:
    if work.early_run is not None or work.qualifier is None:
        return work
    config = deps.flow_config or load_config()
    previous = work.previous_run
    decision = (
        decide_later_turn(work.qualifier, deps.policy_version, previous.desk, config.routing_version)
        if previous is not None
        else decide_route(work.qualifier, deps.policy_version, config.routing_version)
    )
    if work.qualifier.status != "valid" or work.qualifier.label is None or work.qualifier.label.intent in {OTHER, UNDEFINED}:
        desk = previous.desk if previous is not None else decision.desk
        decision = decision.model_copy(update={"desk": desk})
    elif previous is not None and previous.desk == "triage":
        decision = decision.model_copy(update={"desk": previous.desk})
    return work.model_copy(update={"decision": decision})


def needs_human_routing(work: PipelineWork) -> bool:
    if work.early_run is not None or work.qualifier is None or work.decision is None:
        return True
    previous = work.previous_run
    return (
        work.qualifier.status != "valid" or work.qualifier.label is None
        or work.qualifier.label.intent in {OTHER, UNDEFINED}
        or (previous is not None and previous.desk == "triage")
    )


def context_plan_step(work: PipelineWork, deps: FlowDeps) -> PipelineWork:
    if needs_human_routing(work):
        return work
    assert work.qualifier is not None and work.qualifier.label is not None
    assert work.decision is not None and work.decision.desk != "triage"
    config = deps.flow_config or load_config()
    plan = plan_context(work.decision.desk, work.qualifier.label, work.ticket.merchant_id, work.field_check, config)
    return work.model_copy(update={"context_plan": plan})


def tools_step(work: PipelineWork, deps: FlowDeps) -> PipelineWork:
    if work.context_plan is None:
        return work
    plan = work.context_plan
    result = (
        deps.gather_evidence(work.ticket, plan)
        if deps.gather_evidence is not None and plan.status == "planned"
        else unavailable_stubs(plan)
    )
    return work.model_copy(update={"tool_results": result})


def evidence_gate_step(work: PipelineWork) -> PipelineWork:
    if work.context_plan is None or work.tool_results is None:
        return work
    return work.model_copy(update={"evidence_decision": decide_evidence(work.context_plan, work.tool_results)})


def drafter_step(work: PipelineWork, deps: FlowDeps) -> PipelineWork:
    if work.evidence_decision is None or work.evidence_decision.mode == "no_draft":
        return work
    assert work.qualifier is not None and work.decision is not None
    old_drafts = work.previous_run.drafts if work.previous_run else ()
    draft, error = _attempt_draft(
        work.ticket, work.qualifier, work.decision.desk, len(old_drafts) + 1,
        deps, evidence=work.evidence_decision,
    )
    return work.model_copy(update={"draft": draft, "draft_error": error})


def policy_check_step(work: PipelineWork) -> PipelineWork:
    if work.draft is None or work.evidence_decision is None or work.tool_results is None:
        return work
    result = check_draft(
        work.draft.text,
        PolicyContext(
            merchant_id=work.ticket.merchant_id,
            allowed_figures=work.evidence_decision.allowed_figures,
            approved_source_ids=work.evidence_decision.source_ids,
            foreign_identifiers=work.tool_results.ledger.foreign_identifiers,
            evidence_facts=work.evidence_decision.facts,
        ),
    )
    draft = work.draft.model_copy(update={"blocked": result.status == "blocked"})
    return work.model_copy(update={"draft": draft, "policy_check": result})


def finalize_step(work: PipelineWork, deps: FlowDeps) -> TicketRun:
    """Assemble the stable domain result after all applicable graph nodes complete."""
    if work.early_run is not None:
        return work.early_run
    previous = work.previous_run
    qualifier, decision = work.qualifier, work.decision
    if qualifier is None or decision is None:
        raise ValueError("pipeline stopped before qualifier/routing completed")
    if needs_human_routing(work):
        desk = previous.desk if previous is not None else decision.desk
        decision = decision.model_copy(update={"desk": desk})
        return TicketRun(
            ticket=work.ticket, qualifier=qualifier, decision=decision, desk=desk,
            status="awaiting_reroute",
            drafts=tuple(d.model_copy(update={"stale": True}) for d in previous.drafts) if previous else (),
            reroute_count=previous.reroute_count if previous else 0,
            reason_codes=decision.reason_codes, field_check=work.field_check,
            foreign_identifiers=previous.foreign_identifiers if previous else (),
            **_carry_history(previous),
        )

    plan, evidence = work.context_plan, work.evidence_decision
    tool_results = work.tool_results
    if plan is None or evidence is None or tool_results is None:
        raise ValueError("pipeline stopped before context/evidence completion")
    old_drafts = previous.drafts if previous else ()
    stale = tuple(item.model_copy(update={"stale": True}) for item in old_drafts)
    if evidence.mode == "no_draft":
        return TicketRun(
            ticket=work.ticket, qualifier=qualifier, decision=decision, desk=decision.desk,
            status="awaiting_validation", drafts=stale,
            reroute_count=previous.reroute_count if previous else 0,
            reason_codes=(*decision.reason_codes, *evidence.reason_codes),
            field_check=work.field_check, context_plan=plan, evidence_decision=evidence,
            foreign_identifiers=tool_results.ledger.foreign_identifiers,
            final_text=None, final_author=None, **_carry_history(previous),
        )

    policy = work.policy_check
    failures = ("DRAFTER_UNAVAILABLE",) if work.draft_error else ()
    new_drafts = (*stale, work.draft) if work.draft else stale
    return TicketRun(
        ticket=work.ticket, qualifier=qualifier, decision=decision, desk=decision.desk,
        status=_next_status(decision.desk), drafts=new_drafts,
        reroute_count=previous.reroute_count if previous else 0,
        reason_codes=(
            *decision.reason_codes, *evidence.reason_codes,
            *_policy_reason_codes(policy), *failures,
        ),
        draft_error=work.draft_error, field_check=work.field_check,
        context_plan=plan, evidence_decision=evidence, policy_check=policy,
        foreign_identifiers=tool_results.ledger.foreign_identifiers,
        final_text=work.draft.text if work.draft else None,
        final_author="model" if work.draft else None,
        **_carry_history(previous),
    )
