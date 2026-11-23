# Product Specification — NAVY / Keelpay Support Copilot

**Status: final, v3 (23 November 2026). Built and running locally on synthetic data, except the items marked *open* in §8; not re-measured end to end since the guardrails were added. v2 (13 November 2026): three lines from the S4 eval (`evals/report_v0.md`), marked *(v2)* and listed in §10. v3: status of each acceptance criterion (§8), launch, monitoring and rollback (§11), changes listed in §12.** Behavioral reference: [Workflow and demo experience](agentic-workflow-subproject/docs/design/copilot-workflow.md). Canonical actor and component names: [NAVY Reference Terminology](agentic-workflow-subproject/docs/design/terminology.md). Routing Node implementation contract and cases: [Feature 004](agentic-workflow-subproject/specs/004-routing-node/spec.md). Delivery work is organized in `specs/roadmap.md`.

## 1. Problem and decision

Keelpay is a fictional B2B fintech scenario with about 36,000 monthly tickets. The copilot helps qualify tickets, assign known requests using deterministic rules, find facts for the correct merchant, and prepare a verifiable reply. **GO** to build and evaluate a functional demo using entirely synthetic data; **CONDITIONAL GO** for a Keelpay pilot after quality, safety, value, and governance are validated. No production deployment has been approved or delivered.

## 2. Actors and flow

`Demo Injector` → `Qualifier Model` → `Routing Node` → `Drafter Model` → **Validator** → explicit simulated send. *(v2)* A ticket the Routing Node cannot assign goes to the **Re-router with no draft**; the draft is written once a person confirms the desk, as in flow v2 (`copilot-workflow.md`). The **Re-router** corrects the desk and triggers the draft; Validator sends routing problems there when found.

The only human workflow nodes are **Re-router** and **Validator**. *(v2)* The only pre-draft hold is the Re-router, for tickets the Routing Node cannot assign; a routed ticket is drafted without waiting. The `Routing Node` is deterministic Python, never a model. The component order and relationships are canonical; see [architecture](agentic-workflow-subproject/docs/design/architecture.md).

## 3. Input and Qualifier Model contract

Input: `{ticket_id, merchant_id, text, created_at}`. The injector supplies IDs and timestamps; they are not inferred from text.

The `Qualifier Model` follows the existing schema at `agentic-workflow-subproject/ml/qualifier/src/dataset_build/schema.py`, with exactly seven string values:

```json
{"intent":"payment_status","sub_intent":"delayed_credit","transaction_id":"TX-992100","amount":"4850.00","currency":"EUR","urgency":"high","sentiment":"negative"}
```

*(v2)* **Field check before routing** (node 3): the contract is unchanged, but an output that breaks it on one field is repaired into it instead of being rejected whole — a malformed `transaction_id` (for example `TX-712O44`) becomes `UNDEFINED`; a valid `intent` with a `sub_intent` that belongs to another intent keeps its intent for routing and shows the sub-intent as `UNDEFINED`. A missing key, an unknown intent or non-JSON output is still invalid and goes to the Re-router. On the S4 eval, 6 of 50 outputs were rejected whole, two of them urgent disputes (`evals/report_v0.md`, miss 1).

*(v3)* **As built:** the runtime constrains the Qualifier to the contract with structured output (JSON schema, strict) over the llama.cpp endpoint (`flow/qualifier.py`), so a malformed field can no longer be produced; an answer that still fails validation is neither retried nor repaired and goes to the Re-router. Field check (node 3, `flow/field_check.py`) then marks each reference `verified` or `unverified` against the merchant's text and never blocks the desk. Constrained decoding changes the evaluated system: the historical D-q4 benchmark does not measure it.

Taxonomy, empty fields, and sentinels are defined in `agentic-workflow-subproject/docs/label_definitions.md`. `UNDEFINED` does not mean “send everything to triage”: each Python decision uses only fields required for that decision. The current contract has neither a confidence score nor a `critical` urgency value. Any change requires a versioned migration, compatibility plan, and re-evaluation. Historical model/artifact names are preserved.

## 4. Product decision rules

- `intent=UNDEFINED`, `OTHER`, invalid output, or model unavailability: create Re-router work. *(v2)* No draft is written until a person confirms the desk; the S4 eval drafted all 13 tickets sent to the Re-router (`evals/report_v0.md`, miss 3). An unknown sub-intent may be corrected there if it changes the desk.
- Known intents: `payment_status` → payments; `dispute` → disputes; `technical_api` → technical/API; `compliance` → compliance. Do not automatically split multi-intent tickets.
- The Routing Node does not perform payment matching. Payment lookup and source-grounding remain separate downstream capabilities; their details do not create another human node in the route.
- `sentiment=UNDEFINED` uses a neutral tone and does not block routing. `urgency=UNDEFINED` is shown as unknown; rules may still detect an explicit signal from the text or authorized context.
- Priority is independent of assignment. It surfaces urgency and supports handling; it does not block draft preparation. Business signals, deadlines, and escalation remain to be configured and validated.
- `Lookup Node` is read-only and scoped to `merchant_id`. `Retrieval Node` is limited to approved synthetic sources. A factual reply requires its supporting facts and sources; otherwise prepare a clarification or require manual handling.
- A Re-router desk correction invalidates the old draft and triggers a fresh draft for the corrected desk. Preserve each correction, reason, and version.

## 5. Review and send gates

The `Validator` handles every generated draft, including clarifications. Draft problems are handled after generation; they do not create a pre-draft stop. A wrong desk goes to the `Re-router` and produces a new draft. The Validator approves and confirms the simulated send. A stale, empty, processing, or already-sent draft cannot be sent. Sending is explicit, idempotent, and simulated: no ledger writes, refunds/unfreezes, or real merchant messages.

## 6. Demo interface

1. **Overview**: event-driven animated flow, real queue/processing/error counts, waiting times, priorities, ratios with periods and denominators, and real/simulated presence distinguished. Re-router and Validator nodes open their space with an available task.
2. **Re-router**: desk-correction queue sorted oldest first; right dossier with ticket, proposed desk/priority, reasons, and correction action. *(v2)* The draft starts once the desk is confirmed.
3. **Validator**: generated drafts, details, sources, history, editor, and explicit approval/send action.

Each ticket shows age since receipt and time in its current step. Rerouting does not reset total age. Default order is global FIFO, oldest to newest. Any priority-first mode must be explicit and sort by age within priority. Waiting time and FIFO are MUST; advanced urgency handling and multi-agent are SHOULD. New arrivals never overwrite the open ticket or edits. All views use one persistent backend state. Langfuse is not the authoritative queue store.

## 7. Environments and data boundaries

| Environment | Allowed | Not allowed / status |
|---|---|---|
| Benchmark | Versioned synthetic corpus and reproducible evaluation | Does not prove the full product or UX |
| Course demo | *(v3)* API and front end in local containers (`flow/deploy/compose.demo.yml`), Qualifier on CPU locally or on a Vertex AI endpoint for the demo only (#73), synthetic ledger/KB, external `Drafter Model` API and Langfuse Cloud for non-critical synthetic data only; simulated sending. No hosted API: Cloud Run is not available on the school project (#74, 16 November 2026) | No real tickets, browser-held service secrets, or financial action |
| Fictional production | Data, models, and traces confined to Keelpay cloud under the scenario's internal policy | Not built or approved; no external API with real tickets |

## 8. Acceptance criteria

*(v3)* Status on `main`, 23 November 2026, after each criterion: **met** (built and measured), **built** (wired and tested, not measured end to end), or **open**.

- Validate the seven-field contract at inference boundary; model errors do not lose tickets. — **built**: structured output, Field check, invalid or unavailable answers to the Re-router.
- Decision cases follow the simple Routing Node tree; unclear assignments go to Re-router with no draft *(v2)*, and draft problems go to Validator. — **built** (v2 line 3: no draft before a person confirms the desk).
- *(v2)* The Qualifier is accepted on the hand-written eval-set (`evals/eval_set_v1.csv`), not only on the synthetic test sets: valid outputs at least 98.5 % (scoring protocol) and abstention (`UNDEFINED`) only on tickets labelled `UNDEFINED`. Dispute requests written without the word "chargeback", in French and English, are added to its training and evaluation data. On the S4 eval it abstained on 4 tickets with a clear desk (`evals/report_v0.md`, miss 2). — **open**: no retraining since; the eval-set v1 replay of the constrained Qualifier is condition 1 of `08_launch_memo.md` §3.
- Merchant isolation, injection/send idempotency, persistence across reconnect, errors, and recovery are verifiable. — **built** locally (merchant-scoped tools, API idempotency keys, SQLite state and LangGraph checkpoints); a multi-replica store is out of the demo scope.
- Views use the same backend state; arrivals, queues, times, and order reflect persisted tickets. — **built**: Overview, Re-routing and Ticket review read the API.
- No send without a human action and no unsupported fact; ticket history covers qualification, routing, drafts, and actions. — **built**: Evidence gate, Policy check, Final compliance gate before every simulated send, lifecycle events.
- Correlated Langfuse traces include available versions, latency, and errors; no real data reaches demo observability. — **built** in code (spans, prompt versions); one trace per ticket from the deployed run not yet captured (#41).
- Measure product outcomes at constant QA and compare against a baseline; do not infer rare-risk or UX outcomes from 20 fixtures. — **open by design**: measured only in the pilot, by the pre-registered A/B (`06_ab_protocol.md`).

## 9. Evidence limits and deliverables

D-q4 is a Qualifier Model candidate measured on a historical benchmark. That benchmark does not validate the complete `Routing Node`, `Drafter Model`, interface, or time saved. Integration, user tasks, and production remain outstanding; the prompted base model (B3) was compared and does not meet the routing bars. Do not rewrite historical prototypes or measurements as target behavior.

## 10. Changes in v2 (13 November 2026)

Each miss of the S4 eval (`evals/report_v0.md` §2) is a line of this spec:

| Miss | Component | Spec line |
|---|---|---|
| 1 · Qualifier output rejected whole (6 of 50) | Qualifier | §3: field check before routing — repair one bad field instead of rejecting the output |
| 2 · Qualifier abstains on clear tickets (4 of 50) | Qualifier | §8: acceptance on the hand-written eval-set; dispute vocabulary without "chargeback" added to training and evaluation |
| 3 · Drafts written on Re-router tickets (13 of 13) | Flow (`flow/pipeline.py`) | §2, §4, §6, §8: no draft until a person confirms the desk, aligned with flow v2 |

## 11. Launch, monitoring and rollback (v3)

- **Launch:** demo GO, delivered; Keelpay pilot CONDITIONAL GO on four conditions; no rollout before the A/B reads (`08_launch_memo.md`). The pilot is the pre-registered A/B: one copilot-off baseline week, six crossover weeks, primary read once, 6 % minimum detectable effect (`06_ab_protocol.md`).
- **Monitoring:** four layers with thresholds — service latency, drift without labels (PSI of the Qualifier outputs and language, invalid and `UNDEFINED` shares), a labelled audit of 200 tickets a week read over four weeks, business metrics monthly (`07_operations.md` §2, `evals/07_monitoring.ipynb`). No ticket or draft text in monitoring.
- **Rollback plan.** Three things roll back separately: the prompt (Langfuse `production` label to the previous version, minutes), the Qualifier model (previous version in `flow/config.toml` or the Registry alias, under an hour), and the copilot level with `copilot_mode`: Judge off, L1 drafting off, L2 routing off, L3 copilot off (manual queue).
- **Rollback criteria, any one is enough:** one uncaught serious error reaching a merchant → L1 on that desk (Head of Compliance); serious errors above the pessimistic value of a category → L3 (Head of Compliance); a second urgent ticket in a wrong desk within four weeks → L2 for urgent tickets (Head of Support); a confirmed layer-2 alarm → previous model or prompt (Head of Support); the harm threshold of `governance.md` Session 5 → L1 on that segment (Head of Support); timeouts above 5 % of an hour → L1 for new tickets (NAVY). Tickets in flight keep their state and total age; return only after the cause is named and the fix passes the eval-set replay (`07_operations.md` §4).
- **Open:** `copilot_mode` is not built (#60). It is required before the pilot, and tested before every demo: the eval-set at L1 produces no draft, the manual queue works at L3.

## 12. Changes in v3 (23 November 2026)

| Section | Change |
|---|---|
| Status | from "target; not implemented" to built locally, with what is open |
| §3 | the v2 field repair is replaced in the build by constrained structured output plus a non-blocking Field check; no repair, no retry |
| §7 | demo hosting follows the 16 November decision: no hosted API, Qualifier on a Vertex AI endpoint for the demo only |
| §8 | status of every acceptance criterion |
| §11 | launch, monitoring and the rollback plan, from `06`–`08` |
