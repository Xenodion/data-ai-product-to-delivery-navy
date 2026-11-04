# Feature 004 Decision Data Model

## Entities

- **QualifierResult**: raw response reference, parsed seven-field `TicketLabel` when valid, status, model/version, schema validation errors, inference event ID.
- **TicketContext**: immutable ticket/merchant IDs, received time, text/source references, current desk, priority facts, human overrides, reroute count, preparation version.
- **LookupResult**: status, merchant ID checked, candidate IDs and distinguishing fields, source/version, error code. Never store a cross-merchant candidate as usable.
- **RetrievalResult**: status, allowed source IDs and versions, content references, error code.
- **PolicyConfig**: versioned desk map, required dependencies, approved priority signals, factual-source requirements, and demo/production environment label.
- **RoutingDecision**: deterministic result contract in `contracts.md`, with immutable decision ID and input version references.
- **DecisionEvent**: actor/system, ticket and merchant scope, prior/current decision references, reason codes, timestamp, trace correlation ID.
- **DraftVersion**: decision ID, preparation mode, source references, status (`current`, `stale`, `blocked`, `sent_simulated`), content version, human edit history.

## Separation of concerns

QualifierResult is model output; RoutingDecision is business logic; LookupResult and RetrievalResult are evidence; DecisionEvent is an audit record; DraftVersion is prepared text. The Support Agent's desk correction is a human event that becomes input to the next RoutingDecision. A correction must not overwrite the original QualifierResult or previous decisions.

## State transitions

1. `received → qualifier_pending → decision_pending`.
2. Invalid/unavailable/undecidable intent → `reroute_required`; retain any independently derived priority.
3. Supported intent → assign desk. If payment facts are required, `lookup_pending → payment_selection_required | clarification_ready | factual_ready | manual_required` according to scoped results.
4. Required source available → `draft_pending → review_ready`; missing information → `clarification_ready`; unusable component/policy state → `manual_required` or `blocked` with reason.
5. High priority adds an attention attribute and configured ordering/escalation event but does not suspend stages 3–4.
6. Desk correction → current dependent work is stale. First correction permits one re-preparation; second goes to `manual_triage`.
7. Only a Support Agent action from a current, non-empty, non-blocked review version can request simulated send; this send transition is implemented by the review workspace, never the Routing Node.

## Persistence and idempotency

Use server-side IDs and UTC timestamps. Demo injection carries an idempotency key. Store immutable inputs and event history, not only the latest status. Decision calculation must be side-effect free and idempotent. Exact storage technology and retention require the runtime/security plan.
