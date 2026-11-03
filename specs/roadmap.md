# NAVY Delivery Roadmap

Date: 3 November 2026. Status: proposed decomposition. Features 003 and 004 have written specs/plans; later rows are future work, not execution-ready plans.

## Frame

Shared references: root constitution `.specify/memory/constitution.md`, AI Product decisions `docs/design/ai-product-decisions.md`, workflow `docs/design/copilot-workflow.md`, terminology `docs/design/terminology.md`, and dated audit `audit/2026-11-03-audit-coherence.md`. Numbered course files remain submission deliverables; features organize their correction and product build. One local V0 baseline is retained; Features 007–009 deliver one English-language V1 successor, not parallel mock-up variants. Feature 002 is a historical build record only.

## Lots and dependencies

| Planned lot | Verifiable outcome | Dependencies | Plan focus |
|---|---|---|---|
| 003-ai-product-alignment | Coherent deliverables, explicit assumptions, aligned governance, identified evidence gaps | Audit and user decisions | Deliverable corrections, financial model, research evidence, traceability matrix |
| 004-routing-node | Same input yields the same Routing Node decisions and reasons; ambiguity isolated by dependency | 003, existing seven-field contract | State, desk/priority/payment/draft tables, reason codes, versioning, edge cases; see `specs/004-routing-node/` |
| 005-ticket-runtime | Injected ticket survives and is retrievable after reconnect/restart | 004 contracts | CPU GGUF serving, API, durable storage, async execution, idempotency, versions/errors; evaluate LangGraph/LangChain or plain Python for orchestration |
| 006-grounded-drafting | Reply or clarification uses the correct synthetic context | 004, 005 interfaces | Tenant-scoped fixtures, KB, candidates, synthetic-only external Drafter Model, typed allowlisted read tools, checks/recovery |
| 007-agent-workspaces | One English-language V1 support experience resolves, reviews, corrects, reroutes, edits, and sends through gates | 003 user-flow decisions; 004–006 interfaces | Two human workspaces, FIFO/wait, persistence, history, accessibility, feedback-informed UX acceptance |
| 008-live-overview | The same V1 experience shows injected flow/counts; a human node opens a real task | 005 events, 007 navigation | Python Demo Injector, Overview, queues, actual presence, defined ratios, drill-down/animation |
| 009-observable-deployment | The single V1 demo is accessible with correlated traces; costs and teardown verified | 005–008 | Dockerized Cloud Run service, static front hosting choice, Langfuse, configuration/secrets, smoke checks/teardown |
| 010-product-validation | Evidence-based final recommendation and S5–S8 deliverables | 003 protocols; demo for measurements | Missing comparators, human measures, QA, metrics, A/B, monitoring/rollback, synthesis |

Instrumentation belongs in contracts and starts in 005; 009 does not bolt on traces at the end. Validation protocols are designed before new results are observed.

LangGraph/LangChain are implementation candidates, not architecture requirements. Any workflow library coordinates the flow while the backend remains authoritative for state and the Python `Routing Node` remains deterministic. Drafter tools must be explicitly allowlisted, scoped to approved synthetic data, and unable to perform sends or financial/state-changing actions.

Advanced urgency and multi-agent are SHOULD for the demo. Minimal Overview, wait times and oldest-first are MUST. Unknown costs and business parameters remain research choices in their relevant plans, not implicit approvals in this roadmap.

## Preparation and execution order

1. Close AI Product choices and execute 003; check course requirements that are actually available.
2. Specify 004, then establish state/event contracts before integration plans.
3. Detail 005–006 and freeze interfaces needed by the front end.
4. Specify 007 then 008 against those interfaces. Tasks can overlap only when dependencies are satisfied.
5. Detail and deliver 009 with cost configuration and teardown; publish synthetic demo only.
6. Run measurements and complete 010; revisit the pilot decision without equating demo completion with production approval.

For each lot: specify → clarify where needed → plan/research/contracts → tasks → analyze → implement → validate. Specs focus on outcomes; stack/hosting choices belong in plans. Reduce the number of lots if they do not provide independently verifiable outcomes; do not create one feature per deliverable.

## Local Spec Kit use

The root has scripts/templates reused from the local installation and a constitution for the shared product. The nested LLMOps installation remains intact. The root feature pointer targets 003; work from the repository root. Local PowerShell resolve/setup-plan scripts have run for the active feature. This does not claim new slash commands are installed in the current client.

Conventions follow the [official existing-project adoption guide](https://github.com/github/spec-kit/blob/main/docs/guides/existing-projects.md). Do not force-reset the repository and overwrite adaptations or Feature 002 history.
