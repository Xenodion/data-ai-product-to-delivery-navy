# Routing Node Contracts

This file defines a versioned target interface for Feature 004. It does not modify the Qualifier Model's existing `TicketLabel` schema.

## Input envelope

```json
{
  "contract_version": "ticket-label-v1",
  "ticket": {"ticket_id": "K-00017", "merchant_id": "M-0003", "created_at": "2026-11-03T09:15:00Z"},
  "qualifier": {"status": "valid", "label": {"intent": "payment_status", "sub_intent": "delayed_credit", "transaction_id": "TX-992100", "amount": "4850.00", "currency": "EUR", "urgency": "high", "sentiment": "negative"}},
  "context": {"desk_override": null, "reroute_count": 0, "current_draft_version": "draft-0"},
  "lookup": {"status": "exact_id", "merchant_id": "M-0003", "transaction_ids": ["TX-992100"]},
  "retrieval": {"status": "found", "source_ids": ["synthetic_kb_payment_01"]},
  "policy_version": "demo-policy-v1"
}
```

`qualifier.status` is one of `valid`, `invalid`, `unavailable`; only `valid` carries a label. Lookup is one of `not_run`, `not_required`, `exact_id`, `candidate_selection`, `not_found`, `conflict`, `wrong_merchant`, `unavailable`. Retrieval is one of `not_run`, `not_required`, `found`, `empty`, `unavailable`, `blocked`.

## Output envelope

```json
{
  "decision_version": "routing-node-v1",
  "desk": "payments",
  "priority": "high",
  "priority_signals": [{"value": "high", "source": "qualifier.urgency"}],
  "required_human_step": "review",
  "blocking_dependency": null,
  "payment_resolution": "exact_id",
  "preparation_mode": "factual",
  "downstream_actions": ["lookup", "retrieval", "draft"],
  "draft_status": "recompute",
  "reason_codes": ["DESK_FROM_SUPPORTED_INTENT", "PAYMENT_EXACT_ID_VERIFIED", "HIGH_PRIORITY_SURFACE_ONLY"]
}
```

## Enumerations

- `desk`: `payments`, `disputes`, `technical_api`, `compliance`, `triage`.
- `priority`: `high`, `medium`, `low`, `unknown`.
- `required_human_step`: `none`, `qualification`, `payment_selection`, `review`, `manual_handling`.
- `blocking_dependency`: `intent`, `sub_intent`, `payment_identity`, `merchant_scope`, `source`, `model_output`, `policy`, or `null`.
- `payment_resolution`: `not_required`, `exact_id`, `candidate_selection`, `clarification`, `not_found`, `conflict`, `wrong_merchant`, `unavailable`.
- `preparation_mode`: `factual`, `documentary`, `clarification`, `manual`, `blocked`.
- `draft_status`: `unchanged`, `recompute`, `stale`, `none`.

Stable reason-code names are API contract. The exact human-readable sentence may be localized in the interface. Initial reason codes: `QUALIFIER_INVALID`, `QUALIFIER_UNAVAILABLE`, `INTENT_UNDECIDABLE`, `INTENT_UNSUPPORTED`, `DESK_FROM_SUPPORTED_INTENT`, `SUB_INTENT_REQUIRED`, `SENTIMENT_NEUTRAL_FALLBACK`, `PRIORITY_UNKNOWN`, `PRIORITY_SIGNAL_FROM_TEXT`, `HIGH_PRIORITY_SURFACE_ONLY`, `PAYMENT_NOT_REQUIRED`, `PAYMENT_ID_ABSENT`, `PAYMENT_EXACT_ID_VERIFIED`, `PAYMENT_CANDIDATES_REQUIRE_SELECTION`, `PAYMENT_EXTERNAL_REFERENCE`, `PAYMENT_NOT_FOUND`, `PAYMENT_CONFLICT`, `PAYMENT_WRONG_MERCHANT`, `LOOKUP_UNAVAILABLE`, `SOURCE_FOUND`, `SOURCE_MISSING`, `RETRIEVAL_UNAVAILABLE`, `DRAFTER_UNAVAILABLE`, `CONTENT_POLICY_BLOCK`, `FIRST_REROUTE_RECOMPUTE`, `SECOND_REROUTE_MANUAL`, `HUMAN_REVIEW_REQUIRED`.

## Invariants

- The Routing Node consumes a validation result; it never rewrites the raw seven-field model output.
- `UNDEFINED` is never globally treated as absent and never automatically maps to one universal route.
- A known desk survives unresolved `transaction_id`; payment-specific claims do not.
- A merchant-scope mismatch is an error/blocked fact path, not a candidate to display.
- High priority is an attention signal, not a draft permission bit.
- The output does not contain `send=true`, a send token, or a ledger mutation instruction.
- Event and trace IDs refer to stored records; sensitive ticket text is governed by separate data policy.
