# Product Specification — NAVY / Keelpay Support Copilot

**Status: agreed functional target; not implemented.** Behavioral reference: [Workflow and demo experience](docs/design/copilot-workflow.md). Canonical actor and component names: [NAVY Reference Terminology](docs/design/terminology.md). Routing Node implementation contract and cases: [Feature 004](specs/004-routing-node/spec.md). Delivery work is organized in `specs/roadmap.md`.

## 1. Problem and decision

Keelpay is a fictional B2B fintech scenario with about 36,000 monthly tickets. The copilot helps qualify tickets, assign known requests using deterministic rules, find facts for the correct merchant, and prepare a verifiable reply. **GO** to build and evaluate a functional demo using entirely synthetic data; **CONDITIONAL GO** for a Keelpay pilot after quality, safety, value, and governance are validated. No production deployment has been approved or delivered.

## 2. Actors and flow

`Demo Injector` → `Qualifier Model` → `Routing Node` → `Drafter Model` → **Validator** → explicit simulated send. Drafting proceeds even when the initial desk may need correction. The **Re-router** corrects that desk and triggers a fresh draft; Validator sends routing problems there when found.

The only human workflow nodes are **Re-router** and **Validator**. There is no pre-draft qualification hold. The `Routing Node` is deterministic Python, never a model. The component order and relationships are canonical; see [architecture](docs/design/architecture.md).

## 3. Input and Qualifier Model contract

Input: `{ticket_id, merchant_id, text, created_at}`. The injector supplies IDs and timestamps; they are not inferred from text.

The `Qualifier Model` follows the existing schema at `agentic-workflow-subproject/src/dataset_build/schema.py`, with exactly seven string values:

```json
{"intent":"payment_status","sub_intent":"delayed_credit","transaction_id":"TX-992100","amount":"4850.00","currency":"EUR","urgency":"high","sentiment":"negative"}
```

Taxonomy, empty fields, and sentinels are defined in `agentic-workflow-subproject/docs/label_definitions.md`. `UNDEFINED` does not mean “send everything to triage”: each Python decision uses only fields required for that decision. The current contract has neither a confidence score nor a `critical` urgency value. Any change requires a versioned migration, compatibility plan, and re-evaluation. Historical model/artifact names are preserved.

## 4. Product decision rules

- `intent=UNDEFINED`, `OTHER`, invalid output, or model unavailability: create Re-router work while the Drafter Model still attempts a draft from the ticket. An unknown sub-intent may be corrected there if it changes the desk.
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
2. **Re-router**: desk-correction queue sorted oldest first; right dossier with ticket, proposed desk/priority, reasons, and correction action. Drafting continues in parallel.
3. **Validator**: generated drafts, details, sources, history, editor, and explicit approval/send action.

Each ticket shows age since receipt and time in its current step. Rerouting does not reset total age. Default order is global FIFO, oldest to newest. Any priority-first mode must be explicit and sort by age within priority. Waiting time and FIFO are MUST; advanced urgency handling and multi-agent are SHOULD. New arrivals never overwrite the open ticket or edits. All views use one persistent backend state. Langfuse is not the authoritative queue store.

## 7. Environments and data boundaries

| Environment | Allowed | Not allowed / status |
|---|---|---|
| Benchmark | Versioned synthetic corpus and reproducible evaluation | Does not prove the full product or UX |
| Course demo | Static front end, Cloud Run CPU backend, synthetic ledger/KB, external `Drafter Model` API and Langfuse for non-critical synthetic data only; simulated sending | No real tickets, browser-held service secrets, or financial action |
| Fictional production | Data, models, and traces confined to Keelpay cloud under the scenario's internal policy | Not built or approved; no external API with real tickets |

## 8. Target acceptance criteria

- Validate the seven-field contract at inference boundary; model errors do not lose tickets.
- Decision cases follow the simple Routing Node tree; unclear assignments go to Re-router while drafting continues, and draft problems go to Validator.
- Merchant isolation, injection/send idempotency, persistence across reconnect, errors, and recovery are verifiable.
- Views use the same backend state; arrivals, queues, times, and order reflect persisted tickets.
- No send without a human action and no unsupported fact; ticket history covers qualification, routing, drafts, and actions.
- Correlated Langfuse traces include available versions, latency, and errors; no real data reaches demo observability.
- Measure product outcomes at constant QA and compare against a baseline; do not infer rare-risk or UX outcomes from 20 fixtures.

## 9. Evidence limits and deliverables

D-q4 is a Qualifier Model candidate measured on a historical benchmark. That benchmark does not validate the complete `Routing Node`, `Drafter Model`, interface, or time saved. Integration, user tasks, and production remain outstanding; the prompted base model (B3) was compared and does not meet the routing bars. Do not rewrite historical prototypes or measurements as target behavior.
