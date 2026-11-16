# NAVY Delivery Roadmap

## Current state and next steps

Updated 10 November 2026. Read this first, then `LAYOUT.md`. The repository root is the AI Product course deliverable and follows the course template; everything technical lives in this sub-project.

**State**
- `flow/` has a LangGraph prototype and API-backed support UI: the frontend now has a two-area console (Dashboard and Workspace), a collapsible left navigation, a directed animated workflow graph, queue tabs, and a three-column ticket review layout for the inbox, draft/actions, and ticket context/history. The bounded reproducible HTTP dataset injector accepted a single `val` ticket; replaying the same session returned the same flow ID. Its flow run could not connect to the local Qualifier (`127.0.0.1:8081`) and fell back to triage without a draft or context-tool call. It sends no labels or trap metadata; follow-up turns require a separate explicit reply manifest and wait for prior human handling. Multi-ticket/follow-up replay, API restart acceptance, working local inference, intermediate node metrics, full workflow acceptance, and full-flow evaluation remain outstanding. See [frontend UX](../docs/design/flow-v2/frontend-ux.md), [synthetic data plan](../docs/design/flow-v2/synthetic-dataset-generation-plan.md), [flow-v2 tasks](013-flow-v2/tasks.md) and the [frontend API contract](../docs/design/flow-v2/frontend-api-contract.md).
- Layout is frozen: `ml/` builds models, `flow/` uses them, `frontend/` shows them, and `.local/` holds everything generated. `tests/test_layout.py` enforces it.
- LangGraph is the selected orchestration library. The local prototype's default in-memory checkpointer is for exploration only; the API must use durable SQLite checkpointing and a separate domain event/ticket store.

**Next steps, in order**
1. Done 6 November 2026: the real flow with a valid Qualifier was rerun after the `ml/` and `.local/` moves, with the `l07` Airflow stack stopped. `flow.runner --n 1 --seed 9` wrote `.local/runs/20261106T125250Z.jsonl`: `qualifier.status` is `valid`, the Routing Node sent the ticket to `triage`, and a draft exists. Docker has 2.8 GiB and `l07` takes about 1.6 GiB idle, so stop that stack before starting the Qualifier (1.8 GiB).
2. Done 6 November 2026: repository reorganised around the course template and merged to `main`.
3. Done 6 November 2026: flow v2 target architecture validated, see [diagram](../docs/design/flow-v2/flow_v2.svg) and [node table](../docs/design/flow-v2/node_table_v1.md).
4. Follow the [flow v2 task list](013-flow-v2/tasks.md). Dev tracker #67, AI Product trackers #53 and #68. It replaces the order of the sections below where they differ. Immediate design implementation: add the required send disposition and distinct persisted outcomes (#58/#31), expose both choices in the workspace and metrics (#37/#38), then verify the full flow and restart/idempotency behavior (#31/#39). After the Qualifier is available, continue multi-ticket/follow-up injector replay (#32). API contract: [frontend-api-contract.md](../docs/design/flow-v2/frontend-api-contract.md).
5. Owner decision: remove the claim wording from `docs/design/copilot-workflow.md` and `docs/design/architecture.md` (#50). Until then, the 005-010 spec overrides them on this point.

Implementation/design update, 10 November 2026: LangGraph is the selected workflow orchestrator; LangChain supplies model integrations and structured-output support where used. The local API, SQL ledger, and deterministic lexical Text Search prototype exist, but restart and full-flow acceptance are still outstanding. Per [ADR 0001](../docs/design/adr/0001-text-search-and-ticket-resolution.md), current product language is SQL & Text Search; embeddings are deferred pending evidence of a lexical-search gap. The send disposition is now implemented in the domain contract, API, checkpoint state and workspace; acceptance and restart/idempotency recovery remain. See the [API contract](../docs/design/flow-v2/frontend-api-contract.md) and [task list](013-flow-v2/tasks.md).

Date: 3 November 2026; implementation/design update: 10 November 2026. Status: roadmap with partially implemented local prototype; each lot below is a target unless the current state above or the detailed task list says otherwise.

## Frame

Shared references: workflow `docs/design/copilot-workflow.md`, terminology `docs/design/terminology.md`, and architecture `docs/design/architecture.md`. Numbered course files contain the course deliverables; `specs/` contains future product implementation contracts and the delivery roadmap. The original V0 mock-up is retained; Features 007–009 describe one English-language V1 successor.

## Lots and dependencies

| Planned lot | Verifiable outcome | Dependencies | Plan focus |
|---|---|---|---|
| 004-routing-node | Same input yields the same Routing Node decisions and reasons; ambiguity isolated by dependency | Product specification and existing seven-field contract | State, desk/priority/payment/draft tables, reason codes, versioning, edge cases; see `specs/004-routing-node/` |
| 005-ticket-runtime | Injected ticket survives and is retrievable after reconnect/restart | 004 contracts | CPU GGUF serving, API, durable storage, async execution, idempotency, versions/errors; LangGraph orchestration |
| 006-grounded-drafting | Reply or clarification uses the correct synthetic context | 004, 005 interfaces | Tenant-scoped SQL fixtures and deterministic Text Search over approved passages, synthetic-only external Drafter Model, typed allowlisted read tools, checks/recovery |
| 007-agent-workspaces | One English-language V1 support experience resolves, reviews, corrects, reroutes, edits, and sends through gates | Product workflow; 004–006 interfaces | Two human workspaces, FIFO/wait, persistence, history, accessibility, UX acceptance |
| 008-live-overview | The same V1 experience shows injected flow/counts; a human node opens a real task | 005 events, 007 navigation | Python Demo Injector, Overview, queues, actual presence, defined ratios, drill-down/animation |
| 009-observable-deployment | The single V1 demo is accessible with correlated traces; costs and teardown verified | 005–008 | Dockerized Cloud Run service, static front hosting choice, Langfuse, configuration/secrets, smoke checks/teardown |
| 010-product-validation | Evidence-based final recommendation and S5–S8 deliverables | User feedback and validation plan; demo for measurements | Missing comparators, human measures, QA, metrics, A/B, monitoring/rollback, synthesis |

Instrumentation belongs in contracts and starts in 005; 009 does not bolt on traces at the end. Validation protocols are designed before new results are observed.

LangGraph is the selected orchestration runtime; LangChain supplies the Qualifier's OpenAI-compatible model adapter and structured-output layer. Langfuse is the prompt-version registry and trace sink. The backend remains authoritative for state and the Python `Routing Node` remains deterministic. Drafter tools must be explicitly allowlisted, scoped to approved synthetic data, and unable to perform sends or financial/state-changing actions.

Advanced urgency and multi-agent are SHOULD for the demo. Minimal Overview, wait times and oldest-first are MUST. Unknown costs and business parameters remain research choices in their relevant plans, not implicit approvals in this roadmap.

## Preparation and execution order

1. Use the agreed product decisions and course requirements documented in the root deliverables.
2. Specify 004, then establish state/event contracts before integration plans.
3. Detail 005–006 and freeze interfaces needed by the front end.
4. Specify 007 then 008 against those interfaces. Tasks can overlap only when dependencies are satisfied.
5. Detail and deliver 009 with cost configuration and teardown; publish synthetic demo only.
6. Run measurements and complete 010; revisit the pilot decision without equating demo completion with production approval.

Each lot has an independently verifiable outcome and clear dependencies. Product specifications define behavior; implementation plans select technology and hosting.
