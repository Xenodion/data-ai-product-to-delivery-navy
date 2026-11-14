# Flow v2: task list

Updated 10 November 2026. Target: [diagram](../../docs/design/flow-v2/flow_v2.svg) (unchanged for now) and [node table](../../docs/design/flow-v2/node_table_v1.md). The target architecture was validated on 6 November 2026; [ADR 0001](../../docs/design/adr/0001-text-search-and-ticket-resolution.md) clarifies Text Search and send-time disposition. Issues hold implementation details; this file holds the order. HTTP behavior is specified in the [frontend API contract](../../docs/design/flow-v2/frontend-api-contract.md).

## Dev side

Tracker: #67. Each step leaves a flow that runs.

| Order | Work | Nodes | Issue | Priority |
|---|---|---|---|---|
| 1 | Measures, rules of nodes 5 and 8, turn limit | All | #54 | p0 (contract drafted in `docs/design/flow-v2/measures-and-gates.md`; implementation underway) |
| 2 | Ticket envelope and turns | 1, 3, 4 | #55 | p0 (typed envelope, in-memory sequence gate and field check drafted; persistent idempotency/error queue remain with API/storage) |
| 3 | Context plan and Evidence gate with stubs (tool tier 1) | 5, 8 | #56 | p0 (wired into the local flow; stub outcomes remain unavailable pending tier-2 tools) |
| 4 | Policy check and Final compliance gate | 10, 14 | #57 | p0 (shared rule module, draft check and final-text function implemented; send precondition remains for node 15) |
| 5 | Desk Drafter | 9 | #36 | p0 (mode-aware desk prompts, evidence-only input, citations and source versions wired; factual modes await evaluation) |
| 6 | Mini ledger, knowledge base and rules (tool tier 2) | 6, 7 | #35 | p0 (local SQL and deterministic lexical Text Search prototype wired; rename contracts/telemetry from legacy retrieval names, evaluate lexical relevance and scenario/evidence matching; embedding search deferred unless evaluation justifies it; see [synthetic data plans](../../docs/design/flow-v2/synthetic-context-and-e2e-evaluation-plan.md)) |
| 7 | Human actions and Send | R, 13, 15 | #58 | p0 (explicit required send disposition `leave_open` / `close`, distinct sent-open/sent-closed/closed-without-reply outcomes, receipt/event fields and terminal behavior implemented; end-to-end/idempotency acceptance remains) |
| 8 | Durable API and database with LangGraph orchestration | All | #31 | p0 (API requires disposition and persists it in the checkpointed run/receipt; legacy `sent_simulated` records load as sent-open; restart/idempotency and HTTP acceptance remain unverified) |
| 9 | Re-router and Validator workspaces, Overview | R, 13 | #37, #38 | p0 (workspace requires an explicit, initially unselected send disposition and shows distinct activity and overview counts; keyboard/screen-reader review, visual browser acceptance, full workflow acceptance and node-level metrics remain; see [frontend UX](../../docs/design/flow-v2/frontend-ux.md)) |
| 10 | Reproducible dataset injector over HTTP | 1 | #32 | p0 (bounded deterministic CSV selection, API-only ticket envelopes, stable session/idempotency manifest, append-only run log and gated same-ticket follow-ups implemented; one `val` ingress accepted and same-session replay returned the same flow ID; flow execution did not pass the Qualifier because its local endpoint was unavailable, so no Drafter, SQL or Text Search call occurred; multi-ticket/follow-up and locked final-split protocol remain; see [synthetic data plan](../../docs/design/flow-v2/synthetic-dataset-generation-plan.md)) |
| 11 | Local container demo | All | #39 | p0 (persistent volumes, health checks, restart and full end-to-end run) |
| 12 | Judge and Redraft loop, kept only if measured | 11, 12 | #59 | p1 |
| 13 | Override switch | All | #60 | p1 |
| 14 | Traces, audit log, labelled scoring and Langfuse prompt releases | 16 | #41, #42 | p1 (Qualifier and Drafter fetch production-labelled v1 prompts; exact release metadata is recorded; staging evaluation and promotion workflow remain) |
| 15 | Evaluation in CI, model routing, readiness | All | #19, #21, #22 | p1 |

Bonus: cloud deployment (#40), embedding retrieval (#43, reconsider only on measured lexical-search gap), confidence research (#45). Out of V1: Human-only queue, built only in the architecture.

### Newly clarified product behavior

- At the final human send action, require a deliberate choice: send and leave open, or send and close. This is a Support Agent decision, never inferred by the LLM.
- Preserve close-without-reply as a separate action requiring a reason. Persist and report sent-open, sent-closed, and closed-without-reply as distinct outcomes.
- Replace current product terminology “RAG” with “Text Search”; keep SQL and Text Search as separate tools with independently recorded results and a join barrier when both are selected.
- Leave `flow_v2.svg` unchanged for now. Schedule its label/lifecycle update after the API and state contracts are implemented and accepted.
- Add full-flow evaluation cases for the three closure outcomes and SQL-only, Text-Search-only, both-tools, and neither-tool paths.

**Implementation order for this decision:** (1) domain state, action/event and send receipt contracts implemented (#58); (2) API/checkpoint persistence and idempotency guard implemented (#31), acceptance remains; (3) required, unselected-by-default workspace choice and distinct dashboard/history labels implemented (#37/#38); (4) still to do: full-flow cases, restart/idempotency acceptance, and queue/overview reconciliation (#31/#39). A sent-closed ticket is terminal in V1; reopening needs a separately specified human action.

## AI Product side

Session 4, tracker #53:

| Deliverable | Issue |
|---|---|
| `04_architecture.md` | #47 |
| `evals/report_v0.md` | #48 |
| Eval set at 50 cases | #49 |
| `spec.md` v2 | #50 |
| `/prototype` | #51 |
| `governance.md`, Session 4 | #52 |

Sessions 5 to 8 and final oral, tracker #68:

| Session | Deliverable | Issue |
|---|---|---|
| S5 | `05_metrics.md` | #61 |
| S5 | Eval set v1, 200 cases | #62 |
| S6 | `06_ab_protocol.md` | #63 |
| S7 | `07_operations.md` | #64 |
| S8 | `08_launch_memo.md`, final spec and brief, `v1.0` | #65 |
| Final | Pitch and oral | #66 |
| All | Lecturer confirmations | #16 |

## Dependencies between the two sides

- #47 can start now: the target architecture is validated.
- #48 runs on the current flow; it does not wait for flow v2.
- #51 needs the policy check from #57.
- #50 follows #48.
- #61 uses the measures from #54.
