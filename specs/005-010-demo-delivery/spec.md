# Integrated demo delivery specification (features 005–010)

Status: planning baseline, updated 5 November 2026. No runtime or deployment is implied. The [flow script](../012-flow-script/spec.md) comes first and proves the real chain locally; the runtime below wraps its functions. Read with [roadmap](../roadmap.md), [routing specification](../004-routing-node/spec.md), [architecture](../../docs/design/architecture.md), [workflow](../../docs/design/copilot-workflow.md), and [confidence study](../011-confidence-signals/spec.md). Those references remain authoritative; this document defines integration boundaries and acceptance for the remaining delivery. Feature 004 remains a separate detailed specification.

## Outcome and scope

A presenter injects synthetic dataset tickets, sees real processing and queues, corrects a route where needed, reviews a grounded draft and explicitly triggers a simulated send. Run locally first, then demonstrate a cloud deployment if feasibility, cost and access permit. Never send a real message or use real customer data. The original V0 remains historical.

P0 means necessary for the local end-to-end demonstration; P1 means important for a robust cloud demonstration; P2 means an optional enhancement. These are delivery priorities, not business urgency. Course deadlines may override ordering.

## Cross-cutting contracts

- A server-created ticket ID, demo session ID, source split and row reference correlate work. The seven-string Qualifier contract remains unchanged. Expected labels stay out of model and routing inputs and are accessible only to evaluation.
- The backend owns persistent ticket state, queues, versioned drafts, human actions and append-only events. The demo has one presenter, so V1 has no claims, leases or optimistic versions; on this point this specification overrides the claim wording in the workflow and architecture references. Idempotency protects duplicate ingress and simulated sends. Queue order is oldest received first; show ticket age and step age. New arrivals never replace the selected task.
- Stages and event names follow the architecture reference; failed, pending and human-wait states remain distinguishable. Record actor, timestamp, versions, decision reasons, error and correlation identifiers. UI counters derive from backend state/events, not traces.
- Qualifier failures create a Re-router task while the Drafter still attempts a generic draft, as the root specification requires. Routing remains pure, deterministic and versioned. Unknown desk creates a Re-router task while safe drafting continues; priority alone does not block preparation. A first desk correction invalidates dependent work and triggers one re-preparation; a second goes to manual triage.
- Human approval is required for every simulated send. Block stale, empty, processing or already-sent drafts; unchanged drafts require explicit confirmation. Duplicate send commands yield one send event. Synthetic fixtures and external services must be clearly marked.

## 005 — Ticket runtime, injector and Qualifier

**Stories.** A presenter selects a frozen split, a ticket or reproducible sequence and cadence; an operator can retrieve a ticket after a restart. The backend accepts an idempotent ingress request, validates and processes it asynchronously and exposes state, history, queue reads and human commands.

**Requirements.** Injector supports immediate injection and bounded replay, configurable 30- or 60-second cadence (and other configured intervals), explicit endpoint, session, repeatable selection and safe stop; never mutate frozen data. Start/reset loads 3–4 predetermined synthetic examples at useful human-workflow stages; seeded states must be clearly identified and internally consistent. A confirmed demo reset stops injection, removes the current tickets from human work queues and restores these examples. It does not delete the source dataset or cumulative metric history. Record a reset event and session boundary, and prevent pre-reset in-flight jobs from repopulating the new queues. Seed examples are counted as received once per load, identified as seeds in metrics. A local test adapter permits deterministic integration tests, while the real D-q4 adapter validates raw output strictly, records model/prompt versions and exposes timeouts or malformed JSON without coercion. Model artifact location and serving interface must be reproducible; don't assume Vertex registration means a running endpoint. A persistent local store and deployable external store are required; choose technologies in the implementation plan. Container configuration is externalized and secrets never enter the front or images.

**Acceptance.** Restart preserves ticket and history; retries cannot duplicate ingress; malformed/unavailable inference remains visible and recoverable; a real synthetic ticket reaches a routing decision and draft through the actual Qualifier. Reset during injection/processing restores the seed queue once, prevents stale work resurfacing and leaves cumulative events and metrics intact; repeated reset commands are idempotent. Record CPU memory, cold start and latency before selecting a deployment shape. Mock-only integration does not satisfy this final check.

## 006 — Grounded drafting and tools

**Stories.** The Drafter prepares a response or clarification using only available authorized synthetic context; the Validator sees source references and missing facts. The presenter can exercise no-result, ambiguous-payment and tool-failure cases.

**Requirements.** V1 calls the Drafter directly from the ticket and available synthetic context; agentic preparation, SQL tools and document RAG are V2 enhancements, not prerequisites for a working V1. If facts are unavailable, use a generic answer or clarification; do not present invented payment details as verified. Use an external model only with synthetic data, configurable provider, bounded timeout/cost and server-side secret. Preserve draft/source versions. V2 provides a merchant-scoped read-only synthetic ledger and versioned approved KB. Typed allowlisted lookup/retrieval tools have scoped input/output, timeouts, errors and trace correlation. Never select an ambiguous payment automatically or accept cross-merchant results. No unsupported payment assertion, refund promise or financial write; absent or failed context produces clarification or manual recovery as appropriate. Do not present unsupported claims as sourced. Simple retrieval precedes embedding-based RAG; compare its benefit before adding it.

**Acceptance.** V1 generates a reviewable response without tools; missing facts prompt clarification, provider failure permits controlled retry or manual writing, and one correction produces a fresh draft while retaining the old version. For V2, demonstrate exact, ambiguous, missing and wrong-merchant lookups; relevant source IDs appear in the workspace; source/tool failure is visible and cannot silently create a factual claim.

## 007 — Human workspaces

**Stories.** A Support Agent opens an eligible Re-router or Validator task, examines the original ticket and decision, and performs a server-checked action. Re-router corrects desk; Validator edits and approves a draft or hands a wrong desk back for correction. The visual direction is a sober, functional workspace inspired by Databricks and GCP, with clear navigation and readable tables rather than decorative effects.

**Acceptance.** Both queues and dossier reflect one backend state, expose wait time, reason, priority, context and history, and handle empty, stale, failed and processing states clearly. Every send gate above is enforced server-side. A keyboard user can navigate and understand the primary flows; color is not the sole status cue.

## 008 — Live overview

**Stories.** The presenter observes actual arrivals, processing, queues, corrections and simulated sends and opens a relevant task from its human node. Overview, Re-router and Validator are three tabs of one experience.

**Acceptance.** Received, active, sent and failed counts and step/queue counts reconcile to defined backend transitions for a stated period. Show current work queues separately from cumulative processed, automatic assignment and reroute metrics. Reset removes work from current queues but retains cumulative event-based metrics; seeded tickets count as received and are identifiable. Label period, numerator and denominator, including whether seeded examples are included. Show queue wait separately from processing latency, oldest waiting ticket, corrections and failures. No unverified accuracy or fabricated agent presence. Refresh/reconnect retains correct counts; no eligible task yields an explicit empty state.

## 009 — Containerization and deployment

**Requirements.** Provide reproducible local container startup, persistent volume, health checks, configuration example and teardown. Front may be static on GitHub Pages or Cloudflare Pages; candidate backend is Cloud Run with external durable storage and CPU model serving. Static hosting cannot run the Python API. Compare actual artifact size, memory, cold start, concurrency, request timeouts and costs before selection; record the decision and fallback. Injector may run locally against the cloud endpoint. Deployment uses synthetic data, restricted credentials, correct CORS and server-side secrets; define access control, budget cap and cleanup before creating billable resources.

**Acceptance.** Clean-machine documented local startup and end-to-end smoke test succeed, including restart. A cloud milestone is complete only after public URL/access, persistence across instance restarts, real inference, human workflow, trace behavior and teardown are verified; document actual cost and residual services. An unverified configuration is not a deployment.

## 010 — Observability, evaluation and course validation

**Requirements.** Instrument stages, versions, latency, errors and human outcomes from the first runtime slice. Langfuse receives correlated synthetic-only traces; its outage must not lose tickets or control queues. Live scoring joins model output and routing decisions to held-out reference labels by immutable dataset reference, with dataset/model/policy versions and session deduplication; no references enter inference. Publish counts, denominators, split, timestamp and missing-label cases. Historical Qualifier scores are not integrated-policy accuracy; report them separately. Human corrections are workload signals, not ground truth. Draft evaluation must separately document source support and human review, with no unsupported automatic quality claim.

**Acceptance.** A replay with known labels yields reproducible per-field and routing metrics including silent-error and urgent wrong-desk counts and denominators; unavailable labels are excluded and visible. An intentionally failed stage appears in monitoring; simulated sends and reroutes reconcile with backend events. A trace outage leaves processing recoverable. Include course requirements, 100-case CI evaluation, readiness checklist and oral in the backlog without asserting lecturer approval or inventing evidence.

## Delivery sequence and decisions

1. Deliver the [flow script](../012-flow-script/spec.md): real D-q4, routing and direct Drafter, locally, with no database.
2. Freeze minimal API/state/event contracts and synthetic fixtures, then wrap the flow functions in the API and storage.
3. Complete human workspaces and grounded drafting; test correction, failure and restart paths.
4. Validate container startup and feasibility/cost; deploy only after environment and budget are known.
5. Complete trace and labelled scoring views, course evidence and optional retrieval improvements.

Open decisions: exact API/event schemas; CPU model artifact distribution; Drafter provider and budget; static host and access control; cloud project, spending cap and teardown owner; evaluation label independence and course requirements, including model cascade/cache. Do not infer confidence from the seven-field contract or silently alter the established workflow to satisfy an unconfirmed course interpretation.
