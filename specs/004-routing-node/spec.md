# Feature Specification: Deterministic Routing Node

**Feature**: 004-routing-node<br>
**Created**: 3 November 2026<br>
**Status**: Router tree and evaluation contract specified; production policy values and integrated acceptance remain open<br>
**Authority**: [Root product spec](../../spec.md), [workflow decision tree](../../docs/design/copilot-workflow.md), and [canonical terminology](../../docs/design/terminology.md).

**Router decision tree and metrics**: [`error-consequences.md`](error-consequences.md) defines the initial desk/priority mapping, Re-router handoff, offline model comparison and post-deployment monitoring. Historical Qualifier gates remain in its [`scoring_protocol.md`](../../agentic-workflow-subproject/docs/scoring_protocol.md); product ownership remains in [`governance.md`](../../governance.md).

## Decision boundary

The Router's first decision is deterministic: validate the Qualifier output, map a supported intent to one desk or create a Re-router task, then surface `high`, non-high or unknown priority. A valid urgent ticket with an unknown intent still shows urgency while Re-router handles the desk. `sub_intent`, sentiment and payment fields do not change this initial desk. The Validator reviews drafts and, when needed, corrects and re-routes. These are the two human nodes of the target flow; an urgent ticket does not create another human gate. Lookup, evidence, draft preparation and send controls are downstream responsibilities described elsewhere in this feature and the product workflow.

## Problem

The fine-tuned Qualifier Model extracts ticket fields. It is not a router. A separate, deterministic Python Routing Node must combine the validated extraction with trusted ticket context, scoped lookup/retrieval outcomes, approved policy configuration, and human decisions to choose a desk and the next allowed step. Today this node and its contract are not implemented.

## User stories

### US1 — Route a supported request deterministically (P1)

As a Support Agent, I need a known request assigned to the correct desk with a readable reason so that I can verify or correct it quickly.

### US2 — Resolve only the ambiguity that blocks an action (P1)

As a Support Agent, I need missing or ambiguous information to block only dependent actions, so a missing payment reference does not discard a known desk or unrelated context.

### US3 — Surface urgency without stopping useful preparation (P1)

As a Support Agent, I need priority, signals, provenance, and handling reasons visible while safe preparation continues in parallel.

### US4 — Recover safely from corrections and failures (P1)

As a Support Agent, I need stale work invalidated, histories preserved, and automatic reroutes bounded so I can recover without sending a draft for the wrong desk or payment.

## Decision invariants

1. The Qualifier Model contract stays at seven string fields. It does not emit a desk, confidence score, permission, or tool action.
2. Given the same contract version, policy version, trusted context, lookup/retrieval outcomes, human decisions, and reroute count, the Routing Node returns the same decision and reason codes.
3. `payment_status → payments`, `dispute → disputes`, `technical_api → technical_api`, and `compliance → compliance`.
4. `intent=UNDEFINED`, `OTHER`, invalid output, or model unavailability creates a Re-router task to determine the request/desk. A valid high urgency remains visible on this path. Do not automatically split multiple intents.
5. A known desk is retained when payment identity is missing or ambiguous. Block only payment-specific claims/actions; selecting a verified candidate or preparing a clarification are valid outcomes.
6. `sub_intent=UNDEFINED` keeps a known desk; qualify the procedure only when that procedure needs the sub-intent. `sentiment=UNDEFINED` uses neutral tone and does not block routing.
7. High priority and independently detected deadline/risk signals are surfaced and may affect ordering/acknowledgement. Priority alone never pauses draft preparation or forces desk confirmation. Every reply still requires Human Review.
8. A lookup is scoped to `merchant_id`; neither a result nor a candidate from another merchant may be displayed or used.
9. A first desk reroute invalidates dependent work and permits one preparation run for the new desk. A second desk reroute requires manual triage. Payment selection alone is not a desk reroute.
10. Routing never sends, writes to a ledger, refunds, or unfreezes funds.

## Required inputs and output

The initial Python interface should be a pure decision function. Side effects (claiming work, calling a model, lookup/retrieval, writing events, or sending) remain in the backend orchestration layer.

Inputs, versioned or referenced by immutable IDs:

- Validated `TicketLabel` or a typed validation/unavailable result.
- Server-created ticket ID, merchant ID, creation time, and received text reference.
- Current desk and human correction history, if any.
- Merchant-scoped `LookupResult` and approved `RetrievalResult`, including explicit success/empty/ambiguous/error states.
- Approved `PolicyConfig` version containing desk map, priority signals, applicable required fields, and any deadlines/escalation rules.
- Reroute count and current preparation/draft version.

Output is a typed `RoutingDecision`, not a mutation of the seven-field model output. It must carry:

- Decision version and stable reason codes with brief agent-facing explanations.
- Desk, or `triage`/manual state when a Re-router task is required.
- Priority (`high`, `medium`, `low`, or `unknown`) plus signal provenance; never invent `critical`.
- Required human step and exact dependency (intent/desk, sub-intent/procedure, payment selection/clarification, or manual recovery).
- Payment resolution state (`not_required`, `exact_id`, `candidate_selection`, `clarification`, `not_found`, `conflict`, `wrong_merchant`, `unavailable`).
- Preparation mode (`factual`, `documentary`, `clarification`, `manual`, or `blocked`) and which downstream results must be recomputed.
- Whether an existing draft is current, stale, or absent; the decision function itself never marks a draft sendable.

See [`contracts.md`](contracts.md), [`data-model.md`](data-model.md), and [`decision-cases.md`](decision-cases.md).

## Functional requirements

- **FR-001**: Validate the exact existing seven-string-field contract at the inference boundary. Preserve raw model output and validation result for audit; do not silently coerce malformed output.
- **FR-002**: Apply one versioned desk map in backend Python; front-end code may display decisions but may not reimplement them.
- **FR-003**: Treat empty string as absent only for `transaction_id`, `amount`, and `currency`; `UNDEFINED` means undecidable and is field-specific.
- **FR-004**: Keep desk assignment independent from payment lookup and sentiment. Do not block known desk on absent payment ID alone.
- **FR-005**: Resolve payment only using approved keys and merchant-scoped results. Multiple plausible candidates remain unselected until a Support Agent acts or a clarification is prepared.
- **FR-006**: Calculate priority independently of desk. Continue safe drafting for high priority while emitting attention, signal source, and configured escalation/ordering effects.
- **FR-007**: Create a Re-router task when the request/desk cannot be determined or a required policy decision cannot safely proceed. Explain exactly what is needed.
- **FR-008**: Choose factual/documentary drafting only when required facts and sources resolve; choose clarification when information is missing; use manual handling for invalid/failed/content-blocked paths that cannot safely be drafted.
- **FR-009**: After desk change, mark downstream lookup/retrieval/draft stale. Permit one re-preparation; send a second change to manual triage and prevent automatic loops.
- **FR-010**: Emit a complete decision event with ticket, tenant, actor/system, model/contract version, policy/rule version, reason codes, input/result references, and timestamps. Do not include sensitive data in Langfuse unless separately approved by the demo data boundary.
- **FR-011**: Keep send checks and explicit simulated send outside the Routing Node. A draft decision is never a send authorization.
- **FR-012**: Keep deterministic decision code independent from model training/inference code so policy edits do not imply retraining.

## Success criteria

- **SC-001**: All approved decision cases produce the exact desk, priority, dependency, preparation mode, stale-state effect, and reason codes expected.
- **SC-002**: Repeating a case with identical versioned inputs yields the same output; changing any decision-relevant input changes only the decisions that depend on it.
- **SC-003**: Unknown sentiment and high priority do not themselves add a Re-router task or block preparation.
- **SC-004**: Missing payment identity preserves a known desk and prohibits payment-specific claims until resolution or clarification.
- **SC-005**: Cross-merchant lookup results are never accepted as facts or candidates.
- **SC-006**: Reroute count cannot produce an automatic loop; a second desk change always becomes manual triage.
- **SC-007**: No Routing Node path can send a message or mutate a ledger.
- **SC-008**: Every decision is traceable to contract, policy, and source/result versions without a fabricated confidence value.
- **SC-009**: Offline comparison reports the initial action matrix, automatic coverage, unnecessary Re-router, urgent wrong-desk and missed-urgency counts/rates on the same labelled tickets. It preserves the historical Qualifier scorer and gates without claiming they validate the integrated Router.
- **SC-010**: Operational monitoring records contract health, latency, versions, decision distribution, Re-router/Validator corrections and urgent waiting time. Accuracy and urgent error rates are recalculated only on separately verified labelled samples.

## Out of scope

Training a new Qualifier Model; changing the seven-field schema; defining unapproved business deadlines or legal rules; automatic multi-intent splitting; automatic payment selection among ambiguous candidates; autonomous send; real payment/ledger mutation; real-data external drafting or traces; UI-owned routing logic.

## Open policy decisions before production

Support and Compliance must approve exact deadline sources, priority overrides, case-specific required sub-intents, safe documentary reply policies, content blocks, retention, and escalation ownership. These values are not invented in this feature. The synthetic demo must clearly label its fixture configuration and must not treat it as production policy.
