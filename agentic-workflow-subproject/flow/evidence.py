"""Deterministic evidence gate (node 8): decide whether drafting is safe."""

from flow.contracts import ContextPlan, EvidenceDecision, EvidenceResult, PreparationMode


def decide_evidence(plan: ContextPlan, result: EvidenceResult) -> EvidenceDecision:
    """Factual mode requires every planned source and verified merchant scope."""
    if plan.status == "human_only":
        return EvidenceDecision(mode="no_draft", reason_codes=plan.reason_codes)
    if plan.status == "clarification":
        found = result.retrieval
        if found.status == "found" and found.source_ids and found.facts and all(
            fact.source_id in found.source_ids for fact in found.facts
        ):
            return EvidenceDecision(
                mode="clarification",
                reason_codes=plan.reason_codes,
                source_ids=found.source_ids,
                facts=found.facts,
            )
        return EvidenceDecision(mode="clarification", reason_codes=plan.reason_codes)

    ledger = result.ledger
    retrieval = result.retrieval
    if ledger.status == "wrong_merchant" or (
        plan.ledger_required and ledger.merchant_id is not None and ledger.merchant_id != plan.merchant_id
    ):
        return EvidenceDecision(mode="no_draft", reason_codes=("PAYMENT_WRONG_MERCHANT",))
    if ledger.status in {"conflict", "blocked"} or retrieval.status == "blocked":
        return EvidenceDecision(mode="no_draft", reason_codes=("EVIDENCE_BLOCKED",))

    if plan.ledger_required:
        if ledger.status == "candidate_selection":
            return EvidenceDecision(mode="clarification", reason_codes=("PAYMENT_CANDIDATES_REQUIRE_SELECTION",))
        if ledger.status == "not_found":
            return EvidenceDecision(mode="clarification", reason_codes=("PAYMENT_NOT_FOUND",))
        if ledger.status in {"unavailable", "not_run", "not_required"}:
            return EvidenceDecision(mode="clarification", reason_codes=("LOOKUP_UNAVAILABLE",))
        if ledger.status == "exact_id" and ledger.merchant_id != plan.merchant_id:
            return EvidenceDecision(mode="no_draft", reason_codes=("PAYMENT_WRONG_MERCHANT",))
        if (
            ledger.status != "exact_id"
            or not ledger.verified_transaction_id
            or not ledger.source_ids
            or not ledger.facts
        ):
            return EvidenceDecision(mode="clarification", reason_codes=("PAYMENT_ID_UNVERIFIED",))
        if ledger.verified_transaction_id != plan.transaction_id:
            return EvidenceDecision(mode="no_draft", reason_codes=("LOOKUP_RESULT_MISMATCH",))
        if any(fact.source_id not in ledger.source_ids for fact in ledger.facts):
            return EvidenceDecision(mode="no_draft", reason_codes=("EVIDENCE_BLOCKED",))

    if plan.knowledge_required:
        if retrieval.status in {"unavailable", "not_run", "not_required"}:
            return EvidenceDecision(mode="clarification", reason_codes=("RETRIEVAL_UNAVAILABLE",))
        if retrieval.status != "found" or not retrieval.source_ids or not retrieval.facts:
            return EvidenceDecision(mode="clarification", reason_codes=("SOURCE_MISSING",))

        if any(fact.source_id not in retrieval.source_ids for fact in retrieval.facts):
            return EvidenceDecision(mode="no_draft", reason_codes=("EVIDENCE_BLOCKED",))

    source_ids = tuple(dict.fromkeys((*ledger.source_ids, *retrieval.source_ids)))
    facts = (*ledger.facts, *retrieval.facts)
    if not facts:
        return EvidenceDecision(mode="clarification", reason_codes=("SOURCE_MISSING",))

    mode: PreparationMode = "factual" if plan.ledger_required else "documentary"
    return EvidenceDecision(
        mode=mode,
        reason_codes=("EVIDENCE_READY",),
        source_ids=source_ids,
        facts=facts,
        allowed_figures=ledger.allowed_figures,
    )


def unavailable_stubs(_plan: ContextPlan) -> EvidenceResult:
    """Tier 1 tool stubs: explicit unavailability, never fabricated empty results."""
    from flow.contracts import LedgerToolResult, RetrievalToolResult

    return EvidenceResult(
        ledger=LedgerToolResult(
            status="unavailable" if _plan.ledger_required else "not_required"
        ),
        retrieval=RetrievalToolResult(
            status="unavailable" if _plan.knowledge_required else "not_required"
        ),
    )
