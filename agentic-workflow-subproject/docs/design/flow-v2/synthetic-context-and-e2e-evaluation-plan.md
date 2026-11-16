# Flow v2: synthetic context and end-to-end evaluation plan

**Status:** design proposal, 9 November 2026. This plan must guide changes to tier-2 data, ticket state, persistence and staging evaluation. It does not claim the current fixtures are production-like or that end-to-end quality has been measured.

Related references: [dataset generation plan](synthetic-dataset-generation-plan.md), [flow task order](../../../specs/013-flow-v2/tasks.md), [runtime contract](../../../specs/005-010-demo-delivery/runtime-contract.md), [scoring protocol](../../scoring_protocol.md), [tool contracts](tools.md), [node table](node_table_v1.md), and the [Sessions 6–7 experiments and operations course](../../../../docs/project/S6_7_Experiments_Operation91126.pptx.pdf).

## 1. Decisions

1. Use **LangGraph as the reference orchestration framework** for the fixed, typed workflow: Python node functions, explicit transitions, checkpointed state and human pause/resume. Keep business authorization, event history and idempotent effects explicit in our application/database; framework checkpoints do not replace those contracts. Retain a minimal custom runner only as a comparison baseline if the prototype reveals a concrete fit problem.
2. Build SQL facts from a versioned synthetic scenario/evidence manifest, not from Qualifier predictions and not by guessing facts from ticket prose. The manifest and its expected labels are evaluator-only inputs; models receive only the ticket and the evidence selected by the normal flow.
3. Treat the existing ledger and KB as a tier-2 prototype. Audit and reconcile it against the contract before expanding it. Keep test tickets and their oracles out of prompt construction, retrieval ranking and policy tuning.
4. Build a separate, frozen 200-case end-to-end evaluation set for staging. Keep the existing Qualifier `test_natural` and `test_traps` roles and scoring protocol unchanged.
5. Separate ticket business state from node execution status. The database event log is authoritative; Langfuse is a derived, best-effort trace sink.
6. Use OpenRouter models, including the existing Chinese-provider models, only to draft linguistic variants of synthetic support documentation if useful. Code and reviewed scenario records define the facts, amounts, currencies, dates, statuses and metrics.

## 2. Current state and gaps

- `flow/build_synthetic_ledger.py` reads transaction-reference strings from `val`, `test_natural` and `test_traps`; it ignores targets, does not include `train`, and assigns deterministic example statuses and dates from each reference. This proves lookup wiring and merchant scoping, but it does not prove that a row's transaction amount, currency, refund/dispute state or source narrative matches the originating scenario.
- `flow/tools.py` builds a query-only SQLite view for parameterized, merchant-scoped lookup. This is suitable for local tool behavior; it is distinct from the PostgreSQL application store planned in #31.
- `flow/fixtures/knowledge.json` already holds desk/sub-intent, approval and validity metadata. Text Search uses token overlap. It is a deterministic lexical baseline; embeddings stay deferred to #43 until evaluation metrics justify them.
- `TicketRun.status` describes business states; the graph separately carries node outcomes and attempts. The local graph now guards reroutes by state and versions human-written replies. A durable per-node/domain history and cross-process recovery still require #31.
- The initial CI/dev graph slice is implemented and covered by flow tests: SQL and Text Search to simulated send, document-only search without SQL, final-gate block/review recovery, and a parallel-tool wait barrier. This is a deterministic regression slice, not the frozen 200-case staging dataset or complete restart/replay verification.
- The historical Qualifier score is not a full-flow score. The scoring protocol itself says end-to-end evaluation needs separate fixtures/oracles. S6–7 calls for a staging eval set of 200 plus a judge on each prompt, model or KB change, a gate before production, and four monitored layers.

## 3. Synthetic data design

### 3.1 Keep three datasets separate

| Dataset | Role | May be visible to nodes/models? | Use |
|---|---|---|---|
| Ticket input | Frozen authored ticket text and envelope | Yes, under normal flow rules | Replay input |
| Synthetic context | Approved ledger facts and approved/versioned document passages | Only through the typed SQL/Text Search outputs selected by the Context Plan | Simulated world/source of truth |
| Evaluation oracle | Expected route, fields, evidence outcome, citations, gates, permitted terminal states and rubric | Never | Scoring only, joined by `case_id` in the evaluator |

No expected label, oracle field or fixture-generation metadata is copied into a Qualifier, Router or Drafter prompt. Runtime tool access must not accept an oracle path or expected label. Evaluation output records the ticket/input hash, fixture version and oracle version so a run is reproducible.

### 3.2 Authoritative scenario manifest

Create a deterministic, reviewed manifest for end-to-end cases. Prefer data captured from the authored scenario card at ticket-generation time. For already-frozen tickets whose source scenario is unavailable, create a mapping only through explicit offline reconciliation and review; record that provenance and do not silently infer the truth from the Qualifier output.

Minimum fields per case:

- `case_id`, `split`, `row_id`, `ticket_sha256`, `merchant_id`, `language`, `channel`, `tags`;
- scenario-owned transaction rows: canonical `transaction_id`, merchant scope, amount in minor units, currency, payment/refund/dispute states as applicable, timestamps, source ID and source version;
- intended KB source IDs/versions, desk and sub-intent eligibility, approval status, effective dates, and language;
- evaluator-only expected label/route, field-match expectations, expected evidence mode, allowed sources, required gate outcomes, expected human actions and allowed final states;
- `fixture_version`, `oracle_version`, deterministic seed and provenance/reviewer fields.

Use explicit scenario constructors for exact match, no record, malformed/unverified reference, duplicate/candidate selection, wrong merchant, amount mismatch, currency mismatch, stale source and unavailable tool. Do not manufacture ambiguity by accidentally duplicating IDs. Every foreign-merchant record must remain inaccessible in the result payload; it exists only to verify the isolation gate.

Do not copy every number or identifier mentioned in a ticket into the ledger. The case manifest distinguishes user-reported claims from ledger-verified facts. A mismatch case intentionally preserves the difference and source provenance. Metrics such as counts, latency, cost, gate rate and sendability are computed from run/event data; they are not generated as fixture facts by an LLM.

### 3.3 Ledger and document contracts

Ledger rows should minimally model `merchant_id`, canonical `transaction_id`, `amount_minor`, `currency`, relevant business states, `updated_at`, `source_id`, `source_version` and synthetic provenance. Keep read-only access, parameterized queries, merchant scoping, bounded results and explicit unavailable/ambiguous/missing outcomes.

KB documents should carry `source_id`, `version`, `desk`, `sub_intents`, `language`, `status`, `valid_from`, `valid_until`, `owner/reviewer`, `policy_version` and the approved text. Include positive and negative fixtures: eligible, wrong desk, wrong sub-intent, unapproved, expired, future-dated, stale-version and prompt-injection text. Only eligible approved passages may reach the Drafter; every factual or procedural claim must cite an allowed source ID/version.

OpenRouter may draft wording variants from an approved fact sheet and a fixed policy template. A human approves each document before it becomes eligible. LLM output must never assign a transaction state, invent a metric, choose a merchant, set an approval flag or determine an expected evaluation result. Preserve model/provider, prompt version and reviewer in fixture provenance.

### 3.4 Matching the existing ticket variables

Cover the current seven-field schema and its taxonomy: `intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`. Context fixtures should also exercise all four desks and each supported sub-intent, but must not pretend that urgency or sentiment are ledger facts. For each intent/sub-intent, state whether ledger facts are required, which document families can be retrieved, and which fields a source can actually support.

Freeze split roles from the scoring protocol: `train` is not scored; `val` is for development; `test_natural` supplies headline Qualifier metrics; `test_traps` supplies per-trap diagnosis only. Any fixture generation or repair on test cases is an offline, versioned staging activity, never a reason to change the Qualifier or claim a new model score. The 200-case flow set is a separate product/harness evaluation population with explicit case design and oracle.

## 4. Full-flow evaluation dataset

Create **200 frozen cases** for staging, consistent with the S6–7 release-path exercise and the planned #62 eval set. Each case has an input record and a separately stored oracle record. Balance and report counts by desk/sub-intent, language, channel, evidence mode, priority, and safety tag; do not claim an unweighted aggregate alone.

Required scenario families:

1. Successful factual/documentary path with valid citations and source versions.
2. Clarification and no-draft paths: absent, malformed, unverified and ambiguous references; no matching row; insufficient or stale evidence.
3. Isolation and adversarial paths: wrong-merchant record, foreign identifier, conflicting references, unapproved/expired/wrong-desk KB results, injected instructions in ticket/document text.
4. Gate paths: unsupported figure, price/fee commitment, refund promise, legal advice, policy-check exception, hard foreign-merchant block, human override with/without reason, edit after approval, human-written response.
5. Human/process paths: route correction, second correction/manual handling, handoff, close-manual, explicit approval, successful simulated send, duplicate retry, conflicting idempotency key, terminal-state mutation attempt, turn limit.
6. Reliability paths: Qualifier invalid/unavailable, Drafter timeout/error, SQL/retrieval timeout or corrupt fixture, restart/recovery, trace sink unavailable.

For every case, store expected node path and transitions, expected tool calls and scope, evidence/source IDs and versions, citation expectations, gate outcomes, permitted human actions, allowed final states, and the invariant checks. Do not require one exact generated sentence where several safe responses satisfy the rubric; score claims, citations, unsupported facts, policy, language and actionability separately. Use a different model/judge from the Drafter only in staging; keep the deterministic gates as hard checks.

Run two modes:

- **CI/dev:** deterministic fake model adapters and controlled tool fixtures; test all transitions, error branches, state/event consistency and safety invariants without API cost.
- **Staging:** pinned real Qualifier/Drafter versions, frozen 200-case set and versioned judge/rubric on every model, prompt or KB change; drafts only, no external send. Record cost, latency, provider/model versions and fixture/oracle hashes.

## 5. Assertions, metrics and release gates

### Gate 1: developer environment

- Fixture schema validates; generation is deterministic for a fixed manifest/seed; expected/oracle files are not imported by serving code.
- Unit and contract checks cover every deterministic node, all allowed/forbidden transitions, schema parsing, citation/source versions, amount/currency normalization, merchant scoping and idempotency semantics.
- Full-path integration checks use fake adapters and include every required scenario family. No network calls or billable models are needed.
- Hard invariants: foreign-merchant data never appears in evidence/drafts; blocked final text cannot send; a sent ticket is terminal; a send key creates at most one send; every model/KB claim is source-constrained; all event sequences and current snapshots reconcile.

### Gate 2: staging

- Run all 200 frozen cases after every Qualifier/Drafter prompt, model, SQL fixture, retrieval or KB change that can affect outputs.
- Require zero critical safety escapes (foreign data exposed, hard block bypass, duplicate send, expected oracle leaked, sent state mutated); no unexplained missing cases or denominators.
- Review source correctness, citation fidelity, no-hit/clarification rates, sendable rate, policy blocks, human-only handling, per-desk/language/trap slices, p50/p95 latency, provider/tool error rate and estimated cost.
- Set numeric thresholds, owners, read dates and decision actions before the first staging score; do not invent thresholds after inspecting results. Any red row blocks production promotion until reviewed.
- Test the rollback/override with the named people who can trigger it before any production stage.

The S6–7 course's four monitoring layers should each have a metric, threshold, clock and owner: infrastructure (latency, errors, cost, retrieval no-hit); model quality (human-reviewed sample, agreement/sendability); product guardrails (human-only drafts, policy blocks, escalation and language/desk gaps); business (the approved business outcomes, only when measured on suitable traffic). The 200-case replay is a release regression gate, not an A/B test and not proof of business impact. Any live causal claim needs a separately sized, pre-registered comparison design and harm threshold.

## 6. Per-node state, events and decorators

Keep one typed ticket snapshot with separate dimensions:

```text
business_status: pending | processing | awaiting_reroute | awaiting_validation |
                 manual_handling | ready_to_send | sent_open | sent_closed | closed_manual
current_node: node_1 ... node_15
node_runs[node_id]: pending | running | succeeded | skipped | waiting_human | failed | blocked
```

Each node run also carries attempt, start/end time, duration, safe error code, output/version references and correlation ID. Append a `node_started` and terminal/wait event and update the snapshot transactionally. A human wait is an explicit resumable state, not a failed execution. Validate legal business transitions in the orchestrator/API; `sent_closed` and `closed_manual` are terminal in V1; `sent_open` can accept a later merchant turn. This directly prevents the state-reset and history-loss issues raised in the #58 review.


Implement those boundaries through LangGraph nodes, edges/conditional edges, typed state and a checkpointer. Use interrupts for resumable human decisions. Persist the authoritative business event log, human edits and external-effect/idempotency records in the application database; checkpoints support workflow recovery but do not substitute for transactional domain records. Keep node functions small and side effects behind typed tools/services. Test framework replay semantics explicitly so a resumed node cannot duplicate a send or other external effect.

Decorators may add OpenTelemetry/Langfuse spans around node/tool calls, but must not silently mutate business state. Configure traces to emit allowlisted metadata only (node ID, business/node status, model/prompt/KB versions, source IDs, latency/cost, policy outcome); do not capture raw ticket, full `TicketRun`, draft body, secrets or oracle. Backend events remain authoritative if the trace sink is down.

### 6.1 LLMOps and graph tooling options

- **LangGraph Studio / local graph visualization:** use during development to inspect graph structure, state and runs; confirm which features work with the selected local/server setup before depending on them.
- **LangSmith:** optional for hosted graph development/deployment, trace inspection and dataset-based offline/online evaluations. Treat account, deployment, data-region, retention and cost constraints as an explicit decision; do not make a hosted service a runtime dependency by default.
- **Langfuse + OpenTelemetry:** keep as the proposed observability path if it fits the project’s stack. Avoid sending duplicate or sensitive payloads; compare the actual tracing/evaluation needs with LangSmith before enabling both.
- **Evaluation harness:** keep deterministic full-flow CI and the frozen staging set as project-owned gates. LangSmith evaluation UI/SDK may be an optional reporting/comparison surface, not the only source of release decisions.

This provides visible, industry-standard graph and LLMOps options while keeping the workflow portable and its business invariants under project control.

## 7. Implementation sequence

1. Review and accept this plan; freeze the case/evidence/oracle schema and hard invariants.
2. Audit the current #35 JSON fixtures and builder against the schema; mark retained, replaced and newly required fixtures. Do not add fields by copying labels into serving inputs.
3. Build a deterministic manifest-driven fixture builder and reconcile the first development slice; review document approvals and source versions.
4. Fix the #58 review findings: reject mutations from terminal states, persist human replies as explicit versions, keep actions/events across turns, and configure safe trace capture.
5. Initial LangGraph prototype delivered for Intake through Policy Check plus human review/send interrupts; continue with atomic human rerouting, replay/restart semantics, and a comparison against the minimal custom baseline. Select graph visualization/tracing options with local run, privacy and cost constraints recorded.
6. Implement typed node lifecycle/event contracts and database transitions in #31; make business events, drafts, idempotency and simulated sends atomic and durable alongside framework checkpoints.
7. Build the 200-case full-flow oracle/evaluator; run mocked CI suite first, then pinned staging replay and gate review.
8. Extend Langfuse/OpenTelemetry spans and four-layer dashboard only after safe event/state contracts exist; verify outage behavior and run the staging rollback drill.

## 8. Course alignment and limitations

The S6–7 material says the frozen eval set is the release regression signal, a staging set of 200 plus judge is run on model/prompt/KB changes, and the non-model harness (steps, gates, traces and switch) is owned and tested. It also requires four monitoring layers with thresholds, clocks and named owners; drift review for data, concept, knowledge and model; an incident response; and a tested rollback before production. This proposal applies those principles to the current synthetic demo. It does not claim randomized business impact, real-customer performance, semantic legal safety, or production readiness.
