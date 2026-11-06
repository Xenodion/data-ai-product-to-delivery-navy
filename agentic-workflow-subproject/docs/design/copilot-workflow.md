# Keelpay Workflow and Demo Experience

Status: screens and behavior of the human steps; flow rules updated on 6 November 2026 to match [flow v2](flow-v2/node_table_v1.md), which prevails on any conflict. Read with [Product Specification](../../../spec.md) and [NAVY Reference Terminology](terminology.md). The original V0 mock-up illustrates a sample interface; it does not implement this flow.

## 1. Demo outcome

The audience watches synthetic tickets arrive, follows their processing, then takes the role of a Support Agent to correct a route, validate a draft, and send a simulated reply. Ticket content and merchant sends are fictitious; ingestion, calculations, queues, actions, and history work against real persistent backend state.

The front end has three distinct tabs: **Overview**, **Re-router**, and **Validator**. The two human nodes share the same tickets; Overview explains the process using their actual backend events.

The **Qualifier Model** returns seven fields and never selects a queue or invokes an action. The **Routing Node** deterministically picks a desk, or triage, and surfaces priority. For a routed ticket, the context plan calls the tools, the **Evidence gate** decides `factual`, `clarification` or `no_draft`, and the **Drafter Model** writes only from that evidence. The **Re-router** takes tickets the flow cannot route; the **Validator** reviews drafts.

An unclear ticket goes to the Re-router and no draft is prepared. High priority stays visible and never changes the path. When the Evidence gate returns `no_draft`, the ticket reaches the Validator with its context and no draft. A policy-blocked draft cannot be approved. Every model draft passes through the Validator; a person may also write and send from the Re-router or Validator, and that text goes through the Final compliance gate like any other. A merchant reply keeps the same `ticket_id` with `turn` raised by 1.

## 2. Re-router

**Purpose:** handle tickets the flow cannot route (`OTHER`, `UNDEFINED`, Qualifier failure, turn limit, spam). No draft is prepared while a ticket is here.

**Queue:** requester, subject, age, proposed desk or “To determine,” priority, and a short routing reason. Keep filters limited to priority, reason, and desk.

**Dossier:** original message, proposed desk/priority, the fields that informed the route, and a readable reason. Full JSON may be collapsed. Do not display invented confidence scores.

**Actions:** (1) correct and enrich with typed fields (desk, sub-intent, transaction id, amount, note), each marked `source=human`; (2) write the reply and send it; (3) close without reply, with a logged reason. Preserve the original model output and record the human correction separately.

Primary action: **Confirm and continue**. It re-enters the flow once at the context plan; the Qualifier does not rerun. A second correction means the person finishes. Spam and thank-you notes are closed here with a reason.

## 3. Validator

**Purpose:** review the draft with its evidence, validate the reply, and send it as a simulation.

**Queue:** drafts and `no_draft` tickets, showing desk, requester, subject, age, and priority. Show in-progress preparation separately.

**Dossier:** merchant message, earlier turns, evidence with the date of each fact, editable draft, and the remaining objections (policy, Judge). Explain the issue and required action; color alone is insufficient.

**History:** receipt, route, draft versions, Validator corrections, Re-router handoffs, errors, and simulated send. Keep details accessible without hiding the writing area.

Primary action: **Approve and send**. Other actions: edit inline, send back for one redraft, write the reply by hand, or send the ticket to the Re-router if the desk is wrong. Avoid a toolbar of technical actions.

### Send gates

| Situation | Behavior |
|---|---|
| Empty draft, active processing without stable version, already sent, or stale version | Block with a specific reason |
| Draft blocked by the Policy check | Cannot be approved; the person writes the reply |
| Draft unchanged | Targeted confirmation: “You have not edited this draft. Confirm you checked the facts and sources before sending it as written.” Do not require cosmetic edits |
| Draft edited | Validate the current version; editing alone does not prove quality |
| Validator approves | Save version, Validator, and one idempotent simulated-send event |

Every text, model or human, passes the Final compliance gate before sending. An unresolved draft cannot be sent.

## 4. Live Overview

**Purpose:** explain how the demo actually works, its bottlenecks, and trade-offs without requiring the audience to read traces.

Main flow: Demo Injector → Qualifier Model → Routing Node → context and evidence → Drafter Model → policy check → Validator → Sent. Re-router tickets leave the main flow until a person acts. Show priority, correction loops, validator outcomes, and errors. Queues are waiting tickets; processing counts are tickets actually in progress.

| Metric | Definition and display |
|---|---|
| Flow activity | Animate a backend transition; show waiting and in-progress counts by step |
| Tickets | Received, active, sent, failed; received is not the same as processed |
| Human presence | Recent sessions; distinguish connected, available, and busy only when implemented |
| Initial automatic assignment | Tickets automatically assigned a desk / tickets with an initial assignment decision; show period and denominator |
| Re-router | Desk corrections / tickets with an initial assignment; show the current queue and total corrections |
| Urgency | Open priority tickets, unclaimed, overdue; age of oldest |
| Preparation | Drafts in progress, ready, or failed; show step latency and queue wait separately |
| Validator | Drafts approved, corrected, clarified, or sent to Re-router; correction rate is not a quality score by itself |
| Incidents | Failed step, affected tickets, and recovery path; never hide the ticket |

Nodes and counters can open the relevant tickets, then their dossier. Animated events may be batched, but counts must remain exact. Do not show accuracy or “correct routing” without reference labels or review; a low reroute rate is not proof of correctness.

All tabs and queues use the same backend state. Langfuse observes technical spans and versions; it does not manage queues. UI values must not be reconstructed from potentially delayed traces. A synthetic demo session is labelled simulated and does not inflate the count of genuinely connected Support Agents.

## 5. Shared interface behavior

Use the persistent left list/right dossier as the V1 design hypothesis, not a frozen layout. During the single V1 design pass, compare the few relevant layout choices against readability, primary-action reachability, payment comparison, and editing on short viewports. Do not maintain multiple prototype variants; record the chosen layout and the evidence behind it.

New tickets update counts and show a discreet arrival indicator. They must not change the selected ticket, move the list under the pointer, or overwrite a draft. **Default work-queue order is oldest received first.** Show age since receipt and time in the current step; a reroute never resets total age. New entries join their chronological place without disturbing the open dossier.

Advanced urgency management is **SHOULD for the demo**: dedicated filter/queue, alerts, and escalation. If “Urgent first” exists, label it explicitly and sort by priority, then age within each level; do not call that global FIFO. Known priority stays visible even if advanced controls are not delivered. Production handling requirements remain to be defined and evaluated; omitting them from the demo does not validate them.

Tabs preserve navigation context. Corrections and drafts persist server-side; reloading does not reset the demo. If a new preparation becomes available while an agent is editing, offer it without replacing human work. Concurrent Support Agents must not overwrite each other's version or send the same reply twice.

## 6. Routing Node and human-node flow

The compact tree and provisional C0–C3 groups are in [`error-consequences.md`](../../specs/004-routing-node/error-consequences.md). The Routing Node uses only the intent/sub-intent and urgency dimensions from the Qualifier Model for this decision. It assigns a desk or triage and surfaces priority. Unknown output or intent sends the ticket to the Re-router, with no draft. No confidence score is assumed.

The Validator reviews draft quality. A desk issue goes to the Re-router; a person's correction re-enters the flow once and returns the ticket to the Validator with a new draft. Priority stays visible throughout and never changes the path.

## 7. Navigation, persistence, and ownership

Clicking a **Re-router** node opens its oldest eligible desk-correction task; clicking a **Validator** node opens its oldest eligible generated draft. The backend atomically claims the task using the active queue mode. A specific list-row click opens that ticket. If already claimed, offer the next available task and do not overwrite a human edit.

The backend persists tickets, decisions, claims, drafts, event history, and simulated sends. Browser-local state may preserve layout/navigation only; it is not authoritative. Refresh/reconnect restores the same ticket and saved draft version. Failures remain visible and retryable/manual, never silently discarded.

For the first demo, one identified Support Agent session is sufficient. Multi-agent concurrency and recovery after disconnect are SHOULD. If not implemented, label the mode single-agent; do not invent a multi-agent presence count.

## 8. Backend/API and observability contracts

The static frontend calls a Python backend on Cloud Run. The backend owns auth/session, ticket state, atomic claims, deterministic decisions, inference, lookup/retrieval, drafts, send gates, history, and overview aggregates. Choose persistence and async execution in the runtime plan; in-process memory is not durable proof. The Python Demo Injector posts synthetic tickets with an idempotency key and configurable cadence.

Minimum events: received; Qualifier Model start/finish/failure; initial Routing Node decision; Re-router task/correction; Drafter Model start/finish/failure; draft version; Validator approval/correction/clarification/handoff; claim/release; send check; simulated send. Events carry ticket ID, server timestamp, actor, and relevant component/rule/prompt version.

Langfuse traces each ticket with spans, versions, latency, retries/errors, available Drafter Model token/cost, and correlated human actions. Do not send real tickets or personal data to external demo traces. Langfuse is not the queue store. Tracing delay/failure must not corrupt operational state.

## 9. Target demo test cases

- Clear French/English tickets assign to the expected desk and produce a source-backed draft.
- Unknown or invalid intent goes to the Re-router with no draft; unknown sub-intent does not block routing.
- Unknown sentiment does not block routing and yields neutral tone.
- Validator detects a wrong desk and sends the ticket to Re-router; one correction produces a fresh draft that returns to Validator.
- Multi-intent requests are not silently split or collapsed into a single factual answer.
- Urgency is visible in Overview, Re-router, and Validator and never changes the path.
- A merchant reply with `turn` 2 keeps the desk and loads the earlier turn.
- A policy-blocked draft cannot be approved; human text with another merchant's identifier is hard-blocked.
- Malformed cross-merchant ID never exposes another merchant's record.
- Retrieval/Drafter Model errors leave a visible retry/manual state and ticket history.
- Unchanged draft requires the targeted confirmation; edited draft remains tied to its version.
- A correction re-enters once; a second one means the person finishes; a stale draft cannot be sent.
- Duplicate injector request does not create a duplicate ticket; duplicate send does not send twice.
- New arrivals do not replace an open ticket or discard edits; waiting time and FIFO remain correct after reroute/reload.
- Overview nodes navigate to the correct actual queue and task; counts use the same backend state as queues.
- Missing Langfuse trace is visible as observability failure and does not remove the ticket.

## 10. Scope

| MUST for demo | SHOULD for demo | Out of scope |
|---|---|---|
| Real Qualifier Model inference and deterministic Routing Node; reasons displayed | Multiple concurrent Support Agents and presence detail | Financial writes, refunds, unfreezing |
| Synthetic lookup/KB and external synthetic-only Drafter Model | Detailed ratio visualizations/drill-down | Automatic multi-intent split |
| Persistent tickets, queues, history, waiting time, oldest-first | Advanced urgency queue, alerts, escalation | Production architecture/compliance approval |
| Three tabs, shared backend state, task navigation | Advanced animations/incidents | Real ticket data sent to external services |
| Human review and explicit simulated send gates | Version comparison and cost detail | Autonomous sending |
| Correlated Langfuse traces and visible error states | Multi-agent disconnect recovery | — |
