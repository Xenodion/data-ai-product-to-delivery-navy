"""Deterministic context plan for the fixed per-desk workflow (node 5)."""

from flow.contracts import ContextPlan, Desk, FieldCheckResult, FlowConfig, load_config
from ml.qualifier.src.dataset_build.schema import TicketLabel, UNDEFINED


# Payment-specific sub-intents require a transaction fact. A general policy
# answer can still be prepared from approved documentation when no ID exists.
def plan_context(
    desk: Desk,
    label: TicketLabel,
    merchant_id: str,
    field_check: FieldCheckResult | None = None,
    config: FlowConfig | None = None,
) -> ContextPlan:
    """Select fixed, read-only sources; never derive tenant scope from the ticket text."""
    cfg = config or load_config()
    if label.sub_intent in cfg.human_only_sub_intents:
        return ContextPlan(
            desk=desk,
            merchant_id=merchant_id,
            sub_intent=label.sub_intent,
            ledger_required=False,
            knowledge_required=False,
            status="human_only",
            reason_codes=("HUMAN_ONLY_TOPIC",),
        )
    if desk == "payments":
        ledger = label.sub_intent in cfg.payment_fact_sub_intents
        if ledger and (
            label.transaction_id in ("", UNDEFINED)
            or field_check is None
            or field_check.transaction_id.status != "verified"
        ):
            reason = (
                "PAYMENT_ID_ABSENT"
                if label.transaction_id in ("", UNDEFINED)
                else "PAYMENT_ID_UNVERIFIED"
            )
            return ContextPlan(
                desk=desk,
                merchant_id=merchant_id,
                sub_intent=label.sub_intent,
                ledger_required=True,
                knowledge_required=True,
                transaction_id=None,
                status="clarification",
                reason_codes=(reason,),
            )
        return ContextPlan(
            desk=desk,
            merchant_id=merchant_id,
            sub_intent=label.sub_intent,
            ledger_required=ledger,
            knowledge_required=True,
            transaction_id=label.transaction_id if ledger else None,
            status="planned",
        )

    if desk == "disputes":
        ledger = label.sub_intent in cfg.dispute_fact_sub_intents
        if ledger and (
            label.transaction_id in ("", UNDEFINED)
            or field_check is None
            or field_check.transaction_id.status != "verified"
        ):
            reason = (
                "PAYMENT_ID_ABSENT"
                if label.transaction_id in ("", UNDEFINED)
                else "PAYMENT_ID_UNVERIFIED"
            )
            return ContextPlan(
                desk=desk,
                merchant_id=merchant_id,
                sub_intent=label.sub_intent,
                ledger_required=True,
                knowledge_required=True,
                transaction_id=None,
                status="clarification",
                reason_codes=(reason,),
            )
        return ContextPlan(
            desk=desk,
            merchant_id=merchant_id,
            sub_intent=label.sub_intent,
            ledger_required=ledger,
            knowledge_required=True,
            transaction_id=label.transaction_id if ledger else None,
            status="planned",
        )

    # Technical/API and compliance answers are documentary. No payment lookup
    # is permitted, even if the Qualifier happened to extract a transaction ID.
    return ContextPlan(
        desk=desk,
        merchant_id=merchant_id,
        sub_intent=label.sub_intent,
        ledger_required=False,
        knowledge_required=True,
        transaction_id=None,
        status="planned",
    )
