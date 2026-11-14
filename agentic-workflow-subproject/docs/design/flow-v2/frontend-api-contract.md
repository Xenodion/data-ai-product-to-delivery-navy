# Frontend API contract

Status: implementation contract for #31, aligned to the current LangGraph prototype and [ADR 0001](../adr/0001-text-search-and-ticket-resolution.md). The API is the only frontend integration boundary; the browser never calls model, SQL, Text Search, LangGraph, or metrics internals directly.

## Runtime guarantees

- Every accepted ticket is keyed by `(ticket_id, turn)` and has a stable `flow_id` / LangGraph `thread_id`.
- Ticket state, node lifecycle, human actions, draft versions, send receipts, and idempotency records survive API/container restarts. SQLite is the local demo store; replacing it with PostgreSQL must not change the HTTP contract.
- Ingress and each mutating human command require an `Idempotency-Key`. Replaying the same key and payload returns the original result; reusing it with a different payload returns `409 IDEMPOTENCY_CONFLICT`.
- Long model work is accepted asynchronously. `POST /tickets` returns `202`; clients poll ticket state. No browser request waits for the full flow.
- SQL ledger and deterministic lexical Text Search are separate tools. When both are selected by the Context Plan they run concurrently and the Evidence Gate waits for both results (or timeout/error result) before proceeding. Embedding retrieval is not part of V1.
- The response exposes business status and safe node lifecycle metadata, never internal prompts, secrets, model request bodies, or raw hidden chain-of-thought.
- Sending remains an explicit simulated action, guarded by current approval, final compliance result, draft version, and one-time idempotency. The Support Agent must explicitly select `leave_open` or `close`; this human disposition is stored with the send outcome. Closing without a reply remains a separate `close_manual` action with a reason.

## HTTP conventions

Base path `/api/v1`; JSON UTF-8; timestamps ISO-8601 UTC. Errors use:

```json
{"error":{"code":"ACTION_NOT_ALLOWED","message":"Action is not allowed in the current state","retryable":false}}
```

Expected statuses: `400` invalid envelope/command, `404` unknown ticket, `409` stale version/state or idempotency conflict, `422` schema validation, `202` accepted asynchronous work, `200` reads/actions completed, `503` service dependency unavailable. `GET /health/live` is process liveness; `GET /health/ready` reports required dependencies without exposing credentials.

## Endpoints

### `POST /api/v1/tickets`

Headers: `Idempotency-Key: <opaque client key>`.

```json
{
  "ticket_id":"case-001", "turn":1, "merchant_id":"merchant-001",
  "body":"I need help with ...", "created_at":"2026-11-09T10:00:00Z",
  "channel":"formal_email", "subject":null, "language":"en",
  "attachments":[]
}
```

Returns `202` with `{ "ticket_id", "turn", "flow_id", "status":"processing", "status_url":"/api/v1/tickets/case-001/turns/1" }`. A repeated `(ticket_id, turn)` with the same canonical payload is idempotent; a different payload is `409 TICKET_TURN_CONFLICT`. A new merchant reply increments `turn`; prior turns are returned as history and remain immutable.

### `GET /api/v1/tickets/{ticket_id}/turns/{turn}`

Returns the current business snapshot, prior ticket turns, status, desk, priority, reason codes, qualifier fields, context plan, independently attributed SQL/Text Search evidence and source versions, draft versions/staleness, policy findings, allowed actions, timestamps, and lifecycle events `{node_id,status,occurred_at,duration_ms,safe_error_code}`. Text exposure is subject to the local demo access policy; production auth/tenant scoping is required before real data.

### `GET /api/v1/queues/{re-router|validator|errors}`

Returns cursor-paginated ticket summaries, oldest first, with `ticket_id`, `turn`, `status`, `desk`, `priority`, `reason_codes`, `created_at`, and current version. The current prototype includes the full ticket snapshot in each row for the single-user local demo; multi-user deployments must split queue summaries from authorized case detail. Page size is bounded by server config.

### `POST /api/v1/tickets/{ticket_id}/turns/{turn}/actions`

Headers: `Idempotency-Key`, `If-Match: <ticket_version>` (optimistic concurrency). One typed action per request:

```json
{"action":"edit_draft","actor":"reviewer-1","draft_version":2,"text":"...","reason":"clarified date"}
```

Supported actions map to graph capabilities: `approve`, `edit_draft`, `write_reply`, `handoff_to_rerouter`, `reroute`, `close_manual`. `reroute` accepts a permitted `desk`; close/handoff/reroute require a reason where the action contract says so. A stale version is `409 STALE_TICKET_VERSION`; invalid state/policy is `409 ACTION_NOT_ALLOWED` or `422 POLICY_BLOCKED`. Success returns the refreshed ticket snapshot and next status.

### `POST /api/v1/tickets/{ticket_id}/turns/{turn}/send`

Explicit simulated send only. Requires the approved current draft/final text, matching `If-Match`, successful final policy gate, actor, a required `disposition` (`leave_open` or `close`), and `Idempotency-Key`. Example: `{"actor":"reviewer-1","disposition":"leave_open"}`. Returns a durable simulated receipt with the disposition and updated state. `leave_open` yields sent-open; `close` yields sent-closed. It does not deliver externally. Replaying the same idempotency key and payload returns the original disposition; conflicting payloads are rejected. Only a sent-open ticket can accept its next merchant turn; sent-closed and manually closed tickets reject new turns in V1.

### `GET /api/v1/overview`

Returns durable counts by business status and queue, processing/error counts, sends by disposition (`leave_open` / `close`), manual closures without a reply, oldest wait, and ratios with numerator and denominator. Metrics are derived from persisted domain events/current ticket state, not in-memory counters.

## Graph state and UI updates

Business status is stored independently from the current node. The API maps LangGraph interrupts to explicit `awaiting_validation`, `awaiting_reroute`, or `send_confirmation` states; clients do not submit raw LangGraph `Command` objects. Initial delivery uses polling; Server-Sent Events may be added later without changing these resources. Every state transition and node attempt is append-only with a safe error code, actor where applicable, and timestamp. SQL and Text Search completion events remain distinct even though the graph currently has one aggregate `tools` node. Sent-open, sent-closed, and manually closed without a reply are distinct outcomes.

## Delivery order / acceptance

1. Done: freeze Pydantic request/response schemas and transition mapping.
2. In progress: durable SQLite domain repository and LangGraph SQLite checkpointing; unique constraints cover ticket-turn and request idempotency. API dependency lock, migrations, and restart acceptance remain.
3. In progress: service layer and API endpoints; human and send interrupts resume using the persisted graph thread. Crash recovery requeues persisted jobs and commands; this still needs restart tests.
4. Implemented but not yet acceptance-verified: required send disposition in the request and checkpointed ticket/receipt. Next exercise send-open, send-close, close-without-reply, duplicate ingress/action/send, restart, optimistic version conflict, policy block, independent SQL/Text Search barrier, and queue/overview reconciliation through HTTP-level full-flow cases.
5. Connect frontend to the API, replacing sample-only data; implement workspaces and overview after API behavior stabilizes.

No real customer data, external send, or production deployment is in scope for this local demo contract.
