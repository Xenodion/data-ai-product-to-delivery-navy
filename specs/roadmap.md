# NAVY Delivery Roadmap

Date: 3 November 2026. Status: proposed product and delivery roadmap; implementation remains future work unless stated in the project documents.

## Frame

Shared references: AI Product decisions `docs/design/ai-product-decisions.md`, workflow `docs/design/copilot-workflow.md`, terminology `docs/design/terminology.md`, and architecture `docs/design/architecture.md`. Numbered course files contain the course deliverables; `specs/` contains future product implementation contracts and the delivery roadmap. The original V0 mock-up is retained; Features 007–009 describe one English-language V1 successor.

## Lots and dependencies

| Planned lot | Verifiable outcome | Dependencies | Plan focus |
|---|---|---|---|
| 004-routing-node | Same input yields the same Routing Node decisions and reasons; ambiguity isolated by dependency | Product specification and existing seven-field contract | State, desk/priority/payment/draft tables, reason codes, versioning, edge cases; see `specs/004-routing-node/` |
| 005-ticket-runtime | Injected ticket survives and is retrievable after reconnect/restart | 004 contracts | CPU GGUF serving, API, durable storage, async execution, idempotency, versions/errors; evaluate LangGraph/LangChain or plain Python for orchestration |
| 006-grounded-drafting | Reply or clarification uses the correct synthetic context | 004, 005 interfaces | Tenant-scoped fixtures, KB, candidates, synthetic-only external Drafter Model, typed allowlisted read tools, checks/recovery |
| 007-agent-workspaces | One English-language V1 support experience resolves, reviews, corrects, reroutes, edits, and sends through gates | Product workflow; 004–006 interfaces | Two human workspaces, FIFO/wait, persistence, history, accessibility, UX acceptance |
| 008-live-overview | The same V1 experience shows injected flow/counts; a human node opens a real task | 005 events, 007 navigation | Python Demo Injector, Overview, queues, actual presence, defined ratios, drill-down/animation |
| 009-observable-deployment | The single V1 demo is accessible with correlated traces; costs and teardown verified | 005–008 | Dockerized Cloud Run service, static front hosting choice, Langfuse, configuration/secrets, smoke checks/teardown |
| 010-product-validation | Evidence-based final recommendation and S5–S8 deliverables | User feedback and validation plan; demo for measurements | Missing comparators, human measures, QA, metrics, A/B, monitoring/rollback, synthesis |

Instrumentation belongs in contracts and starts in 005; 009 does not bolt on traces at the end. Validation protocols are designed before new results are observed.

LangGraph/LangChain are implementation candidates, not architecture requirements. Any workflow library coordinates the flow while the backend remains authoritative for state and the Python `Routing Node` remains deterministic. Drafter tools must be explicitly allowlisted, scoped to approved synthetic data, and unable to perform sends or financial/state-changing actions.

Advanced urgency and multi-agent are SHOULD for the demo. Minimal Overview, wait times and oldest-first are MUST. Unknown costs and business parameters remain research choices in their relevant plans, not implicit approvals in this roadmap.

## Preparation and execution order

1. Use the agreed product decisions and course requirements documented in the root deliverables.
2. Specify 004, then establish state/event contracts before integration plans.
3. Detail 005–006 and freeze interfaces needed by the front end.
4. Specify 007 then 008 against those interfaces. Tasks can overlap only when dependencies are satisfied.
5. Detail and deliver 009 with cost configuration and teardown; publish synthetic demo only.
6. Run measurements and complete 010; revisit the pilot decision without equating demo completion with production approval.

Each lot has an independently verifiable outcome and clear dependencies. Product specifications define behavior; implementation plans select technology and hosting.
