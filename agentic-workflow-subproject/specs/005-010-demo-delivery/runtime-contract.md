# V1 runtime contract

Status: implementation contract, 6 November 2026. This refines the [integrated plan](plan.md) and [product specification](spec.md). The current `flow.contracts.TicketRun` is the processing result at the first human step; the API adds durable lifecycle state around it. Names below are the V1 wire names. The seven-field Qualifier label remains defined only in `ml/qualifier/src/dataset_build/schema.py`.

## Identity and ordering

- The server creates UUID ticket, event and session IDs and UTC timestamps. The active session is stored in PostgreSQL. Every ticket belongs to exactly one session; a reset creates a new session and marks the old one inactive.
- The injector supplies `source: {split, row_id}` for a frozen synthetic row, `merchant_id`, ticket `text`, and an idempotency key. It never supplies an expected label, route, draft or server timestamp. The API rejects an unknown split, non-synthetic merchant or empty text.
- The backend orders human queues by `received_at`, then ticket ID. `step_entered_at` records when the current human state began. A selected ticket remains selected in the browser while new tickets arrive.
- A request key is scoped to `(session_id, command_type, key)`. The server stores a canonical hash of the request body and the response. Repeating the same command and body returns the stored result without another event or model call. Reusing the key with a different body returns `409 idempotency_conflict`. Look up an existing key before checking whether its session is still active, so a reset retry returns the original reset response.

## Ticket states

| State | Entered by | Allowed next action |
|---|---|---|
| `pending` | Accepted ingress or controlled processing retry | Background loop starts processing |
| `processing` | Loop claims the next pending ticket | Commit the `process()` result, or return to `pending` after an interrupted attempt |
| `awaiting_reroute` | `process()` returns triage | Correct desk, or choose manual handling |
| `awaiting_validation` | A current draft exists on a known desk | Edit draft, approve and simulate send, or hand off to Re-router |
| `manual_handling` | No usable draft, or second desk correction | Add a human draft for validation, or close as manually handled |
| `sent` | Validated simulated send | Terminal |
| `closed_manual` | Human closes a manual case with a recorded reason | Terminal |

`TicketRun.status` covers only its three human states. The API state also covers ingress, processing and terminal states. `failed` is an error flag on a processing attempt, not a hidden queue: a provider failure that `process()` handles still reaches one of the three human states with its error and reason code visible. An unexpected process crash returns to `pending` with an attempt error and bounded retry count; after the configured limit it enters `manual_handling` with the failure exposed.

The loop has one consumer in one API process. It reserves the oldest pending ticket in a short database transaction, calls `process()` outside that transaction, then commits the result and events only if the ticket still belongs to the active session. On API startup, any `processing` row from an interrupted run becomes `pending`, with a recovery event. This design assumes exactly one API instance for V1; deployment must enforce that constraint until a multi-consumer protocol exists. A reset can occur during a model call: the old result is discarded when its session is no longer active.

`reroute()` is called only for a ticket in `awaiting_reroute` or after a Validator handoff. A first correction records the old draft as stale and performs one new draft attempt. A second correction enters `manual_handling`, as the flow function specifies. The initial `RoutingDecision` is immutable; current desk, correction count and draft versions are separate fields. Any edit creates a new draft version; the previous version remains in history. A human draft records `source: human` and actor, while model drafts retain model and prompt provenance.

## Commands and reads

All mutating requests require `X-Idempotency-Key` and a `session_id` in the body. A new command must target the active session; an exact retry may target the previous session. The server derives actor identity from its configured demo session, not from a trusted browser claim. `404` means an unknown ticket; `409 stale_session` means a ticket or new command belongs to an inactive session; `409 invalid_state` means its current state rejects the command; `422` means a malformed request.

| Endpoint | Request / result |
|---|---|
| `POST /sessions/reset` | Confirmed reset request and key; atomically deactivate current session, create a new one, append reset event and load the selected 3–4 seed scenarios once. Return new session ID and seed ticket IDs. |
| `GET /sessions/current` | Active session ID, creation time and seed set version. |
| `POST /tickets` | Synthetic source, merchant and text; return `202` with server ticket ID, `pending` state and session ID. Identical retry returns the original response. |
| `GET /tickets` | Session, state, source and cursor filters; ordered by receive time and ID; page size capped at 100. |
| `GET /tickets/{id}` | Current state, immutable input and initial decision, current desk, qualifier result, draft versions, error, timestamps and permitted actions. |
| `GET /tickets/{id}/events` | Append-only event page ordered by event sequence. |
| `GET /queues/{name}` | `reroute` or `validation`; only active-session eligible tickets, oldest first, with received and step times. |
| `POST /tickets/{id}/reroute` | Target desk and reason; call `reroute()`, persist new state and event. A same-desk or third correction is `409 invalid_state`. |
| `POST /tickets/{id}/handoff` | Validator records wrong-desk reason and moves ticket to `awaiting_reroute`; current draft becomes stale. |
| `POST /tickets/{id}/drafts` | Human text and edit reason; append a version for the current desk and enter `awaiting_validation`. Empty text is rejected. |
| `POST /tickets/{id}/send` | Current draft version and explicit `confirmed_unchanged` boolean; perform gates, append one simulated-send event and enter `sent`. Never contact a real delivery service. |
| `POST /tickets/{id}/retry` | Controlled retry for a visible transient failure; record reason and return to `pending`. A sent or inactive-session ticket cannot retry. |
| `POST /tickets/{id}/close-manual` | Human reason; close a `manual_handling` ticket without a simulated send. |
| `GET /metrics` | Explicit `session_id` or cumulative UTC period, seed inclusion, counts and denominators as defined below. |

The minimum JSON shapes are:

```text
POST /tickets
{"session_id":"uuid","merchant_id":"synthetic-merchant","text":"...","source":{"split":"val","row_id":"..."}}
202 {"ticket_id":"uuid","session_id":"uuid","state":"pending","received_at":"UTC timestamp"}

POST /tickets/{id}/send
{"session_id":"uuid","draft_version":1,"confirmed_unchanged":true}
200 {"ticket_id":"uuid","state":"sent","send_id":"uuid","sent_at":"UTC timestamp"}
```

All ticket reads use `state`, `session_id`, `ticket_id`, `received_at`, `step_entered_at`, `is_seed`, `source`, `merchant_id`, `text`, `current_desk`, `priority`, `reason_codes`, `qualifier`, `initial_decision`, `drafts`, `current_error` and `permitted_actions`. A list response may omit the large text and nested result fields; a detail response includes them. Cursor pages return `items` and `next_cursor` (`null` at the end). Error responses have `error.code`, `error.message` and `correlation_id`; no stack trace is sent to the browser.

`send` requires `awaiting_validation`, a nonempty current draft on the current desk, no stale flag, and an explicit human approval. If the draft was not edited by a human, `confirmed_unchanged` must be true. The server stores a unique simulated send per ticket. A repeated send with the same request key returns the original result; a new request after send returns `409 invalid_state`. Handoff invalidates approval and makes every prior draft stale. There are no claims, leases or optimistic version checks in this single-presenter V1.

## Events and transactions

Every event has `event_id`, monotonic per-ticket `sequence`, `ticket_id` (nullable for session reset), `session_id`, `type`, `occurred_at`, `actor_type` (`system`, `model`, `presenter`), `correlation_id` and a typed `payload` object. Session-level events use a separate monotonic session sequence. Version fields in the payload identify model, prompt and routing policy when relevant. Append events in the same transaction as state transitions and idempotency records. Never place API secrets or expected labels in events.

Minimum event types: `ticket_received`, `processing_started`, `processing_recovered`, `qualifier_finished`, `qualifier_failed`, `route_decided`, `draft_created`, `draft_failed`, `reroute_requested`, `desk_corrected`, `draft_edited`, `validation_approved`, `send_checked`, `simulated_sent`, `retry_requested`, `ticket_closed_manual`, `session_reset`. The full `process()` result is persisted together with its terminal processing events; `processing_started` is persisted before the external calls. A provider error records a failure event and its public error category, without swallowing the ticket.

PostgreSQL minimum tables: `sessions`, `tickets`, `ticket_events`, `drafts`, `idempotency_requests`, `simulated_sends`. Use unique constraints on `(session_id, command_type, key)`, `(ticket_id, event_sequence)` and `simulated_sends.ticket_id`. Store raw Qualifier output and validated fields on the ticket, with the model version; store draft versions separately. Keep dataset references on tickets for evaluation-only joins, never in model prompts as labels.

## Metrics and reset invariants

- `received`: distinct `ticket_received` events. Seeds count once and carry `is_seed=true`; clients can request counts with or without seeds.
- `processed`: distinct tickets whose first `process()` outcome committed, including an `awaiting_reroute` or `manual_handling` outcome. A crashed or discarded attempt does not count.
- `auto_assignment`: initial decisions with a known desk divided by all committed initial routing decisions. It measures automatic assignment, not correctness.
- `reroute_handoff`: distinct tickets with a `reroute_requested` event. `desk_corrected`: distinct tickets with at least one correction; report the number of correction events separately.
- `sent`: distinct `simulated_sent` events. `active`: tickets in the active session excluding `sent` and `closed_manual`. Queue counts derive from current active-session state. Failures are tickets with a current unresolved error, with the error category shown.
- Each ratio returns numerator, denominator, period, session scope and `includes_seeds`; a zero denominator gives a null ratio. Wait age uses current time minus `step_entered_at`; processing latency uses stage timestamps, never queue wait.

Reset does not delete tickets, events or cumulative metrics. It deactivates the prior session and removes its tickets from active queues by session scope. The seed set is a versioned fixture selected before implementation; each seed has an internally consistent state and event history. A repeated reset with the same key returns the same session and seeds. An in-flight old-session result cannot create a new-session ticket, event or queue entry.

## Acceptance examples

1. Duplicate ingress with the same key and body returns one ticket and one `ticket_received`; a changed body returns `409`.
2. Restart after `processing_started` recovers the pending ticket and commits at most one first outcome.
3. Reset while `process()` is waiting on a model preserves old history, loads seeds once and discards the stale result.
4. A Qualifier failure reaches Re-router with a visible generic draft attempt; a Drafter failure reaches manual handling with an error.
5. First correction creates one new draft attempt; second correction enters manual handling; a third is rejected.
6. A stale or empty draft cannot send. An unchanged model draft needs explicit confirmation. Two requests with one send key create one simulated send.
