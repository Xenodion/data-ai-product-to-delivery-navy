# Flow v2: measures and deterministic gates

Working contract for issue #54. Thresholds are not inferred from the frozen test sets. Owners below are role owners for the demo, not named production appointments.

## Node measures

| Node | Primary measure and computation | Counter-metric | Reader and decision |
|---|---|---|---|
| Intake | accepted tickets / valid submissions; rejected count by reason | duplicate and malformed submissions | Demo operator: repair input handling; never silently drop a ticket |
| Qualifier | per-field exact match; desk accuracy; silent errors / labeled tickets; urgent wrong-desk / urgent labeled tickets | unnecessary Re-router handoffs | NAVY + Support: model/prompt candidate only after frozen evaluation; probabilities are not a gate |
| Field check | incorrect or malformed extracted references detected / labeled references | valid references incorrectly marked unverified | Support + NAVY: change canonicalization rules only after counterexamples are reviewed |
| Routing | correct desk / routable labeled tickets; priority omissions | avoidable triage and urgency-driven bypasses | Product + Support: version the deterministic mapping; urgency remains a surface signal |
| Context plan | planned required sources / cases requiring those sources; unnecessary calls / all tickets | missed required source; calls per ticket | Product + Support: update the closed desk/sub-intent table |
| Ledger | exact, missing, ambiguous, wrong-merchant and unavailable outcomes by case | known records missed | Demo operator: repair fixtures or scope; wrong-merchant usable results must remain zero |
| Text Search | required passage found / cases with an approved source; source ID coverage | irrelevant/stale passages and passages per draft | Content owner + Support: revise approved KB and filters |
| Evidence gate | factual decisions with every required verified fact and source / factual decisions | safe documentary cases downgraded; unsupported factual drafts | Support + Compliance: change rules only from independently reviewed cases; factual false-allow is zero-tolerance |
| Drafter | drafts approved unchanged / drafts reviewed; unsupported claims / drafts | edit time, latency, cost, clarification share | Support + Compliance: retain or revise prompt/model; every draft stays human-reviewed |
| Policy/final gates | seeded violations blocked / seeded violations; false blocks / safe drafts | missed violation | Compliance: update policy and fixtures; no blocked draft can be sent |
| Human nodes | correction rate, review time, direct human replies, queue wait | sends without explicit action (must be zero) | Support lead: change workflow only with quality held constant |
| Send | duplicate simulated sends (must be zero) | send failures and retries | Demo operator: fix idempotency/recovery |
| Audit | completed event history / processed tickets | sensitive content retained outside policy | NAVY + Compliance: repair logging/retention before demo |

All rates carry numerator, denominator, period, and whether seeded cases are included. Model quality and product impact are reported separately. Confidence intervals describe sampling uncertainty around a measured rate; they do not make token probabilities useful for classifying an individual ticket.

## Orchestrator and runtime measures

Keep execution telemetry separate from business outcomes. The LangGraph prototype emits per-run measurements in `FlowState.metrics`; configured local SQLite also persists allowlisted node events and incremental aggregates. This telemetry store does not replace the application domain event store (#31).

| Measure | Definition | Required dimensions / guardrail |
|---|---|---|
| `node_executions_total` | Completed node invocations counted by node ID and outcome | Include attempts/replays; failures must be recorded by the durable event layer when integrated |
| `node_duration_ms` | Wall time samples for each completed graph node invocation | Aggregate p50/p95 by node and model/provider version; don't combine human wait with active execution |
| `interrupt_count` / `resume_count` | Human pauses and resumed graph actions per flow | Slice by checkpoint type/action; no ticket text in metric labels |
| `qualifier_latency_ms`, `drafter_latency_ms`, `drafter_cost_usd` | Model-step latency and reported estimated draft cost | Keep absent/not-run distinct from zero; attribute by pinned model and prompt version |
| `evidence_mode`, `policy_outcome`, `final_gate_outcome` | Gate outcomes per flow | Denominators come from attempted gate events; blocked/failed are explicit outcomes |
| `human_actions_total` | Count of approve/edit/write/handoff/reroute/close actions | Include action and desk; don't expose actor identity in aggregate metric labels |
| `simulated_send_total` | Simulated send outcomes, including final-gate block | Successful sends must reconcile to one durable receipt; duplicate send count remains zero |
| `send_disposition_total` | Successful sends by explicit human disposition: `leave_open` or `close` | Disposition is required, idempotent, and persisted with the send event/receipt; include terminal counts for sent-open, sent-closed, and closed-without-reply |
| `flow_duration_ms` | End-to-end elapsed time from accepted input to terminal or current pause | Track active processing and queue/human wait separately once timestamps are durable |

Never use ticket IDs, merchant IDs, raw text, draft content, source text or oracle fields as metric labels. LangGraph's checkpointer is for resumable execution; durable domain audit events remain application-owned. The initial processing path now emits separate graph-node measurements, with allowlisted cross-ticket SQLite aggregates. Optional Judge/Redraft and human reroute work are not yet split into atomic nodes. Per-thread snapshots remain diagnostic; SQLite holds the local aggregates.

### Metric storage and delivery

Use an application-owned append-only event table as the source of truth, with a transactional incremental aggregate projection. For local runs, SQLite is sufficient. Before running it in Docker, mount its database directory on a named volume (never store it only in the disposable container layer). Use the same repository interface with the planned PostgreSQL store (#31) when the API/database tier is implemented; avoid maintaining SQLite and PostgreSQL as competing production sources.

Minimum storage contract:

- `flow_events`: unique `event_id`, flow/thread correlation ID, event type, node ID, attempt, event time, node/business status, model/prompt/fixture versions and allowlisted numeric outcomes. No raw ticket, draft, source text, secrets or evaluator oracle.
- `metric_aggregates`: period, metric name, bounded dimensions and aggregate values (count, sum, numerator/denominator as appropriate). Do not use ticket or merchant IDs as dimensions.
- Insert each event and update its aggregate in one transaction. Enforce a unique stable event ID so retrying event delivery or replaying a checkpoint cannot increment a count twice. Advance the node attempt only for a genuine new execution attempt.
- Derive aggregates only from newly inserted events; provide a rebuild/reconciliation command that recomputes them from `flow_events` and detects divergence.
- Commit the application event before attempting Langfuse export. Langfuse delivery is asynchronous/best-effort and retryable with the same correlation and event IDs; its outage must not lose the event or block the ticket flow.

Send Langfuse an allowlisted observation/span per graph node with node name, status, duration, model/prompt/KB version, cost/token usage where available, and safe gate outcomes as metadata. Add evaluator or human quality judgments as Langfuse scores attached to the corresponding trace/observation; don't treat arbitrary metadata as numeric metric storage. Langfuse can aggregate trace volume, latency, cost and scores for dashboards, but the local/PostgreSQL event store remains authoritative for business counts, audit and idempotency.

For an SQLite container, mount a named volume at the database directory and configure WAL plus explicit backup/retention. SQLite is the local demo adapter, not a multi-replica shared store. Production deployment must use a shared transactional database such as PostgreSQL.

## Node 5: closed context plan

The plan is a pure function of desk, validated `intent`/`sub_intent`, transaction ID, and turn. `merchant_id` always comes from the typed ticket envelope and is supplied by the caller to the ledger adapter; it is never inferred from message text. Node 5 calls only read-only allowlisted sources.

| Desk | Sub-intent | Ledger | Approved knowledge | Notes |
|---|---|---:|---:|---|
| payments | `delayed_credit`, `missing_payment`, `status_inquiry`, `refund_status` | Required when a canonical transaction ID exists | Required | Missing/`UNDEFINED` ID leads to clarification; it does not change the desk |
| payments | `UNDEFINED` or `OTHER` | No | Required | Documentary answer only; no procedure-dependent claim |
| disputes | `unauthorised_fee`, `chargeback`, `duplicate_charge`, `amount_mismatch` | Required when a canonical transaction ID exists | Required | Missing ID leads to clarification; ambiguous candidates are never selected automatically |
| disputes | `UNDEFINED` or `OTHER` | No | Required | Generic documentary response only |
| technical_api | all | No | Required | Query is desk/sub-intent scoped |
| compliance | all | No | Required | Query is desk/sub-intent scoped; no legal conclusion beyond approved text |

The turn cap is three automated merchant turns. Turn 4 and later go to the Re-router before model/tool processing; the same `ticket_id` is retained, and the desk remains fixed unless a human changes it. Earlier conversation turns are loaded as context, subject to the configured input-size limit; truncation must preserve the latest turn and relevant prior facts or fall back to human handling.

## Node 8: evidence decision

1. `factual` only if every planned ledger lookup is exact, merchant-scoped and verified, and approved Text Search returns at least one source ID. Any amount/status in the draft must be grounded in those results.
2. `documentary` if no ledger fact is required and approved Text Search returns at least one source ID. The draft may state only what those sources support.
3. `clarification` for a missing payment ID, no result, multiple candidates, unavailable planned tool, or missing approved source when a safe question can resolve the gap. Never describe unavailable as not found.
4. `no_draft` for cross-merchant result, material evidence conflict, blocked source, or a state where a safe clarification cannot be determined. Send the ticket to human handling with the reason.

At tier 1, both tool stubs return `unavailable`, so payment-specific work is clarification and no factual payment claim is allowed. Documentary work without an available approved source is also clarification. The local tier-2 adapter is in `flow/tools.py`; source IDs and tool/version metadata are carried with the Evidence Decision and draft.

## Whole-flow and financial layer

Report accepted, processed, rerouted, reviewed, sent-open, sent-closed, closed-without-reply, failed and active-queue counts from durable events with explicit session/period and denominators. Report active handling time separately from queue wait. Compare median and p90 handling time, resolution/closure share and turns per ticket; turns per ticket is the counter-metric for any faster closure claim. Compare against the current human workflow at constant independently reviewed quality. Never collapse send disposition into one generic “sent” or “closed” metric.

Financial scenarios use only the assumptions in `02_sizing.xlsx` and clearly label assumed adoption, time saved, labor cost and volume. Realized value is not claimed from a synthetic demo. A pilot decision requires measured end-to-end time and quality, operational costs, and a reviewed residual-risk plan.
