"""HTTP API for the local flow demo. Run with ``uvicorn flow.api:app``."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import random
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langfuse import get_client
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict, Field

from flow.api_store import ApiStore, IdempotencyConflict, VersionConflict
from flow.contracts import Desk, SendDisposition, Ticket, TicketRun, load_config
from flow.langgraph_app import build_ticket_graph, initial_state
from flow.metrics_store import MetricsStore
from flow.policy import can_approve_model_draft
from flow.runner import build_deps
from flow.world_profile import merchant_context, merchant_threads, ticket_thread

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent


class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "edit_draft", "write_reply", "handoff_to_rerouter", "reroute", "close_manual"]
    actor: str = Field(min_length=1, max_length=120)
    text: str | None = Field(default=None, max_length=12000)
    reason: str | None = Field(default=None, max_length=2000)
    desk: Desk | None = None
    draft_version: int | None = None


class SendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor: str = Field(min_length=1, max_length=120)
    disposition: SendDisposition
    override_reason: str | None = Field(default=None, max_length=2000)


def _digest(value: Any) -> str:
    raw = value.model_dump_json(exclude_none=False) if isinstance(value, BaseModel) else json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def _allowed_actions(run: TicketRun) -> list[str]:
    if run.status == "awaiting_validation":
        actions = ["write_reply", "handoff_to_rerouter"]
        current = next((draft for draft in reversed(run.drafts) if not draft.stale), None)
        if run.final_author == "human" and run.final_text and run.final_text.strip():
            actions.append("approve")
        elif current and run.policy_check and can_approve_model_draft(current, run.policy_check):
            actions.append("approve")
        if any(not draft.stale for draft in run.drafts):
            actions.append("edit_draft")
        return actions
    if run.status == "ready_to_send":
        return ["send"]
    if run.status == "awaiting_reroute":
        return ["reroute", "write_reply"]
    if run.status == "manual_handling":
        return ["close_manual"]
    return []


def _snapshot(store: ApiStore, row: dict[str, Any], graph: Any | None = None) -> dict[str, Any]:
    graph_state = _get_graph_snapshot(graph, row["thread_id"]) if graph is not None else {}
    run_data = graph_state.get("ticket_run") or row.get("run")
    run = TicketRun.model_validate(run_data) if run_data else None
    lifecycle = graph_state.get("lifecycle_events")
    if lifecycle is None:
        lifecycle = store.events(row["ticket_id"], row["turn"])
    else:
        lifecycle = [
            {"node_id": event.get("node_id", "unknown"),
             "status": event.get("outcome", "completed"),
             "duration_ms": event.get("duration_ms"), "occurred_at": None}
            for event in lifecycle
        ]
    status = (
        "error" if row["status"] == "error"
        else "processing" if row["status"] == "processing"
        else run.status if run else row["status"]
    )
    if run is None and graph_state and row["status"] != "error":
        status = "processing"
    result: dict[str, Any] = {
        "ticket_id": row["ticket_id"], "turn": row["turn"], "flow_id": row["flow_id"],
        "version": row["version"], "status": status, "desk": row["desk"],
        "priority": row["priority"], "created_at": row["created_at"],
        "updated_at": row["updated_at"], "error_code": row["error_code"],
        "ticket": row["ticket"], "events": lifecycle,
        "current_node": (list(_get_graph_state(graph, row["thread_id"]).next or [None])[0]
                         if graph is not None and status == "processing" else None),
        "prior_turns": store.history(row["ticket_id"], row["turn"]),
        "allowed_actions": [],
    }
    if run:
        result.update({
            "status": status,
            "desk": run.desk,
            "priority": run.decision.priority,
            "reason_codes": list(run.reason_codes),
            "qualifier": run.qualifier.model_dump(mode="json"),
            "context_plan": run.context_plan.model_dump(mode="json") if run.context_plan else None,
            "evidence": run.evidence_decision.model_dump(mode="json") if run.evidence_decision else None,
            "drafts": [draft.model_dump(mode="json") for draft in run.drafts],
            "policy_check": run.policy_check.model_dump(mode="json") if run.policy_check else None,
            "final_policy_check": run.final_policy_check.model_dump(mode="json") if run.final_policy_check else None,
            "final_text": run.final_text,
            "send_disposition": run.send_disposition,
            "allowed_actions": [] if status in {"error", "processing"} else _allowed_actions(run),
            "human_actions": [event.model_dump(mode="json") for event in run.human_actions],
            "send_receipt": run.send_receipt.model_dump(mode="json") if run.send_receipt else None,
        })
    return result


def _get_graph_state(graph: Any, thread_id: str) -> Any:
    return graph.get_state(_thread_config(thread_id))


def _get_graph_snapshot(graph: Any, thread_id: str) -> dict[str, Any]:
    return dict(_get_graph_state(graph, thread_id).values or {})


def _save_result(store: ApiStore, graph: Any, row: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    current = store.ticket(row["ticket_id"], row["turn"])
    if current is None:
        raise KeyError((row["ticket_id"], row["turn"]))
    graph_state = state or _get_graph_snapshot(graph, row["thread_id"])
    run_data = graph_state.get("ticket_run")
    if run_data is None:
        status = "processing"
        run = None
    else:
        run = TicketRun.model_validate(run_data)
        status = run.status
    old_events = store.events(row["ticket_id"], row["turn"])
    graph_events = graph_state.get("lifecycle_events", [])
    new_events = graph_events[len(old_events):] if len(graph_events) >= len(old_events) else graph_events
    safe_events = [
        {"node_id": item.get("node_id", "unknown"), "status": item.get("outcome", "completed"),
         "duration_ms": item.get("duration_ms"), "details": {}}
        for item in new_events
    ]
    error_code = "ACTION_REJECTED" if graph_state.get("action_error") or graph_state.get("send_error") else None
    version = store.update_ticket(
        row["ticket_id"], row["turn"], current["version"], status=status, run=run,
        error_code=error_code,
    )
    if safe_events:
        store.record_node_events(
            row["ticket_id"], row["turn"], version, len(old_events), safe_events,
        )
    store.mark_job(row["flow_id"], status)
    return store.ticket(row["ticket_id"], row["turn"])


def _execute_job(app: FastAPI, flow_id: str, resume: dict[str, Any] | None = None) -> None:
    store: ApiStore = app.state.store
    graph = app.state.graph
    row = store.ticket_by_flow(flow_id)
    if row is None:
        return
    store.mark_job(flow_id, "processing")
    store.mark_ticket_processing(row["ticket_id"], row["turn"])
    try:
        if resume is not None:
            current_graph_state = _get_graph_snapshot(graph, row["thread_id"])
            if _command_already_applied(current_graph_state, resume, row["updated_at"]):
                state = current_graph_state
            else:
                state = graph.invoke(Command(resume=resume), _thread_config(row["thread_id"]))
        else:
            saved_graph = _get_graph_state(graph, row["thread_id"])
            if saved_graph.values:
                state = (
                    graph.invoke(None, _thread_config(row["thread_id"]))
                    if saved_graph.next else dict(saved_graph.values)
                )
            else:
                prior = store.previous_run(row["ticket_id"], row["turn"])
                initial = initial_state(
                    Ticket.model_validate(row["ticket"]),
                    TicketRun.model_validate(prior) if prior else None,
                )
                initial["flow_id"] = row["flow_id"]
                state = graph.invoke(initial, _thread_config(row["thread_id"]))
        saved = _save_result(store, graph, row, state)
        logger.info("flow %s reached %s", flow_id, saved["status"])
    except Exception:
        logger.exception("flow %s failed", flow_id)
        current = store.ticket(row["ticket_id"], row["turn"])
        if current:
            try:
                store.update_ticket(
                    row["ticket_id"], row["turn"], current["version"],
                    status="error", error_code="FLOW_EXECUTION_FAILED",
                )
            except Exception:
                logger.exception("failed to persist flow failure for %s", flow_id)
        store.mark_job(flow_id, "error")


def _queue_job(app: FastAPI, flow_id: str, resume: dict[str, Any] | None = None) -> None:
    app.state.executor.submit(_execute_job, app, flow_id, resume)


def _command_already_applied(state: dict[str, Any], command: dict[str, Any], submitted_at: str) -> bool:
    """Recognize a graph checkpoint written after a command but before DB projection."""
    run_data = state.get("ticket_run")
    if not run_data:
        return False
    run = TicketRun.model_validate(run_data)
    event_action = {
        "edit": "edit", "write": "write", "approve": "approve", "handoff": "handoff",
        "reroute": "reroute", "close": "close",
    }.get(command.get("action"))
    if command.get("action") == "send":
        if (
            run.send_key == command.get("idempotency_key")
            and run.send_disposition == command.get("disposition")
        ):
            return True
        event_action = "send_blocked"
    if event_action is None:
        return False
    submitted = datetime.fromisoformat(submitted_at)
    for event in reversed(run.human_actions):
        if event.created_at < submitted:
            break
        if event.action != event_action or event.actor != command.get("actor"):
            continue
        if event_action == "send_blocked" and event.send_disposition != command.get("disposition"):
            continue
        if event_action in {"edit", "write"} and command.get("text"):
            expected = hashlib.sha256(command["text"].encode("utf-8")).hexdigest()
            if event.text_sha256 != expected:
                continue
        return True
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(ROOT / ".env")
    config = load_config()
    if config.api_worker_count != 1:
        raise RuntimeError("api.worker_count must remain 1 with the synchronous SQLite LangGraph checkpointer")
    database_path = Path(config.api_db_path)
    if not database_path.is_absolute():
        database_path = ROOT / database_path
    store = ApiStore(database_path)
    # The checkpoint database is separate from the business projection by design.
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError as exc:
        raise RuntimeError("Install the langgraph-checkpoint-sqlite dependency to run the durable API") from exc
    checkpoint_path = Path(config.api_checkpoint_db_path)
    if not checkpoint_path.is_absolute():
        checkpoint_path = ROOT / checkpoint_path
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")
    saver_context = SqliteSaver.from_conn_string(str(checkpoint_path))
    checkpointer = saver_context.__enter__()
    checkpointer.setup()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        saver_context.__exit__(None, None, None)
        raise RuntimeError("OPENROUTER_API_KEY is required for API flow execution")
    drafter_client = httpx.Client(headers={"Authorization": f"Bearer {api_key}"})
    deps = build_deps(drafter_client, config)
    app.state.store = store
    app.state.graph = build_ticket_graph(deps, checkpointer=checkpointer)
    # Sync SqliteSaver is intended for lightweight serialized graph execution.
    app.state.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="flow-api")
    app.state.dependencies = deps
    app.state.metrics = MetricsStore((ROOT / config.metrics_db_path).resolve()) if config.metrics_enabled else None
    # Requeue only once at process startup, then atomically claim each queued job.
    store.requeue_interrupted_jobs()
    for job in store.claim_jobs():
        _queue_job(app, job["flow_id"], job["command"])
    try:
        yield
    finally:
        app.state.executor.shutdown(wait=True, cancel_futures=False)
        drafter_client.close()
        saver_context.__exit__(None, None, None)
        try:
            get_client().flush()
        except Exception as exc:  # a tracing failure must not break shutdown
            logger.error("Langfuse flush failed: %s", exc)


app = FastAPI(title="NAVY Ticket Flow API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(load_config().api_cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Idempotency-Key", "If-Match"],
)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready(request: Request) -> dict[str, str]:
    if not hasattr(request.app.state, "graph"):
        raise HTTPException(status_code=503, detail={"code": "FLOW_NOT_READY"})
    return {"status": "ready", "persistence": "sqlite", "orchestrator": "langgraph"}


@app.post("/api/v1/tickets", status_code=202)
def submit_ticket(
    ticket: Ticket,
    request: Request,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=200),
) -> dict[str, Any]:
    store: ApiStore = request.app.state.store
    digest = _digest(ticket)
    scope = f"ingress:{ticket.ticket_id}:{ticket.turn}"
    try:
        replay = store.get_idempotent(scope, idempotency_key, digest)
    except IdempotencyConflict as exc:
        raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from exc
    if replay is not None:
        response.status_code = 202
        return replay
    if ticket.turn > 1 and store.previous_run(ticket.ticket_id, ticket.turn) is None:
        raise HTTPException(409, detail={"code": "PREVIOUS_TURN_REQUIRED"})
    if ticket.turn > 1:
        prior_run_data = store.previous_run(ticket.ticket_id, ticket.turn)
        prior_run = TicketRun.model_validate(prior_run_data)
        if prior_run.status in {"sent_closed", "closed_manual"}:
            raise HTTPException(409, detail={"code": "TICKET_CLOSED"})
        if prior_run.status != "sent_open":
            raise HTTPException(409, detail={"code": "PREVIOUS_TURN_NOT_RESOLVED"})
    flow_id = str(uuid4())
    ticket_key = hashlib.sha256(ticket.ticket_id.encode("utf-8")).hexdigest()[:24]
    thread_id = f"ticket:{ticket_key}:{ticket.turn}"
    inserted = store.insert_ticket(
        ticket_id=ticket.ticket_id, turn=ticket.turn, flow_id=flow_id,
        thread_id=thread_id, ticket=ticket,
    )
    if not inserted:
        current = store.ticket(ticket.ticket_id, ticket.turn)
        if current is None or current["ticket"] != ticket.model_dump(mode="json"):
            raise HTTPException(409, detail={"code": "TICKET_TURN_CONFLICT"})
        flow_id = current["flow_id"]
    result = {
        "ticket_id": ticket.ticket_id, "turn": ticket.turn, "flow_id": flow_id,
        "status": "queued", "status_url": f"/api/v1/tickets/{ticket.ticket_id}/turns/{ticket.turn}",
    }
    store.save_idempotent(scope, idempotency_key, digest, result)
    if inserted:
        _queue_job(request.app, flow_id)
    return result


@app.get("/api/v1/tickets/{ticket_id}/turns/{turn}")
def get_ticket(ticket_id: str, turn: int, request: Request) -> dict[str, Any]:
    store: ApiStore = request.app.state.store
    row = store.ticket(ticket_id, turn)
    if row is None:
        raise HTTPException(404, detail={"code": "TICKET_NOT_FOUND"})
    return _snapshot(store, row, request.app.state.graph)


@app.get("/api/v1/queues/{queue_name}")
def get_queue(
    queue_name: Literal["re-router", "validator", "errors"], request: Request,
    limit: int = Query(50, ge=1), cursor: str | None = None,
) -> dict[str, Any]:
    limit = min(limit, load_config().api_max_page_size)
    statuses = {
        "re-router": ("awaiting_reroute",),
        "validator": ("awaiting_validation", "ready_to_send", "manual_handling"),
        "errors": ("error",),
    }[queue_name]
    after = None
    if cursor:
        try:
            decoded = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
            after = (str(decoded[0]), str(decoded[1]), int(decoded[2]))
        except (ValueError, TypeError, IndexError, json.JSONDecodeError) as exc:
            raise HTTPException(400, detail={"code": "INVALID_CURSOR"}) from exc
    store: ApiStore = request.app.state.store
    rows = store.list_tickets(statuses, limit=limit + 1, after=after)
    has_more = len(rows) > limit
    visible = rows[:limit]
    next_cursor = None
    if has_more and visible:
        last = visible[-1]
        encoded = json.dumps([last["created_at"], last["ticket_id"], last["turn"]], separators=(",", ":"))
        next_cursor = base64.urlsafe_b64encode(encoded.encode("utf-8")).decode("ascii").rstrip("=")
    return {"items": [_snapshot(store, row, request.app.state.graph) for row in visible], "count": len(visible), "next_cursor": next_cursor}


def _human_command(action: ActionRequest) -> dict[str, Any]:
    mapping = {"edit_draft": "edit", "write_reply": "write", "handoff_to_rerouter": "handoff", "close_manual": "close"}
    command: dict[str, Any] = {"action": mapping.get(action.action, action.action), "actor": action.actor}
    if action.text is not None:
        command["text"] = action.text
    if action.reason is not None:
        command["reason"] = action.reason
    if action.desk is not None:
        command["desk"] = action.desk
    return command


def _mutate(
    ticket_id: str, turn: int, request: Request, key: str, if_match: str,
    payload: BaseModel, command: dict[str, Any],
) -> dict[str, Any]:
    store: ApiStore = request.app.state.store
    scope = f"action:{ticket_id}:{turn}:{key}"
    digest = _digest(payload)
    try:
        replay = store.get_idempotent(scope, key, digest)
    except IdempotencyConflict as exc:
        raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from exc
    if replay is not None:
        return replay
    row = store.ticket(ticket_id, turn)
    if row is None:
        raise HTTPException(404, detail={"code": "TICKET_NOT_FOUND"})
    if row["status"] == "processing":
        try:
            replay = store.get_idempotent(scope, key, digest)
        except IdempotencyConflict as exc:
            raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from exc
        if replay is not None:
            return replay
        raise HTTPException(409, detail={"code": "FLOW_BUSY"})
    try:
        expected = int(if_match.strip('"'))
    except ValueError as exc:
        raise HTTPException(400, detail={"code": "INVALID_IF_MATCH"}) from exc
    if expected != row["version"]:
        try:
            replay = store.get_idempotent(scope, key, digest)
        except IdempotencyConflict as exc:
            raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from exc
        if replay is not None:
            return replay
        raise HTTPException(409, detail={"code": "STALE_TICKET_VERSION", "current_version": row["version"]})
    run = TicketRun.model_validate(row["run"]) if row.get("run") else None
    if run is None or command["action"] not in _allowed_actions(run):
        raise HTTPException(409, detail={"code": "ACTION_NOT_ALLOWED"})
    if command["action"] == "edit" and payload.model_dump().get("draft_version") != next(
        (draft.version for draft in reversed(run.drafts) if not draft.stale), None
    ):
        raise HTTPException(409, detail={"code": "STALE_DRAFT_VERSION"})
    if command["action"] == "edit" and not command.get("text", "").strip():
        raise HTTPException(422, detail={"code": "REPLY_TEXT_REQUIRED"})
    if command["action"] == "write" and not command.get("text", "").strip():
        raise HTTPException(422, detail={"code": "REPLY_TEXT_REQUIRED"})
    if command["action"] == "reroute" and not command.get("desk"):
        raise HTTPException(422, detail={"code": "DESK_REQUIRED"})
    if command["action"] in {"handoff", "reroute", "close"} and not command.get("reason", "").strip():
        raise HTTPException(422, detail={"code": "REASON_REQUIRED"})
    if command["action"] == "send":
        if run.status != "ready_to_send":
            raise HTTPException(409, detail={"code": "ACTION_NOT_ALLOWED"})
    # Optimistically reserve the next version before scheduling one command.
    try:
        accepted, created = store.reserve_action(
            scope=scope, key=key, request_sha256=digest,
            ticket_id=ticket_id, turn=turn, expected_version=expected,
            status=run.status, run=run, command=command,
        )
    except IdempotencyConflict as exc:
        raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from exc
    except VersionConflict as exc:
        try:
            replay = store.get_idempotent(scope, key, digest)
        except IdempotencyConflict as conflict:
            raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT"}) from conflict
        if replay is not None:
            return replay
        raise HTTPException(409, detail={"code": "STALE_TICKET_VERSION"}) from exc
    if not created:
        return accepted
    row["version"] = accepted["version"]
    row["run"] = run.model_dump(mode="json")
    _queue_job(request.app, row["flow_id"], command)
    return accepted


@app.post("/api/v1/tickets/{ticket_id}/turns/{turn}/actions", status_code=202)
def ticket_action(
    ticket_id: str, turn: int, action: ActionRequest, request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=200),
    if_match: str = Header(alias="If-Match"),
) -> dict[str, Any]:
    return _mutate(ticket_id, turn, request, idempotency_key, if_match, action, _human_command(action))


@app.post("/api/v1/tickets/{ticket_id}/turns/{turn}/send", status_code=202)
def send_ticket(
    ticket_id: str, turn: int, payload: SendRequest, request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=200),
    if_match: str = Header(alias="If-Match"),
) -> dict[str, Any]:
    command = {
        "action": "send", "actor": payload.actor,
        "idempotency_key": idempotency_key, "disposition": payload.disposition,
    }
    if payload.override_reason is not None:
        command["override_reason"] = payload.override_reason
    return _mutate(ticket_id, turn, request, idempotency_key, if_match, payload, command)


@app.get("/api/v1/merchants/{merchant_id}/context")
def get_merchant_context(merchant_id: str) -> dict[str, Any]:
    """Merchant profile and history for the front end; not an input of the flow."""
    config = load_config()
    if not config.world_database_path:
        raise HTTPException(status_code=503, detail={"code": "WORLD_NOT_CONFIGURED"})
    context = merchant_context(config, merchant_id)
    if context is None:
        raise HTTPException(status_code=404, detail={"code": "MERCHANT_NOT_FOUND"})
    return context


@app.get("/api/v1/merchants/{merchant_id}/threads")
def get_merchant_threads(merchant_id: str) -> dict[str, Any]:
    """The merchant's conversations as a mailbox list, for the front end only."""
    config = load_config()
    if not config.world_database_path:
        raise HTTPException(status_code=503, detail={"code": "WORLD_NOT_CONFIGURED"})
    threads = merchant_threads(config, merchant_id)
    if threads is None:
        raise HTTPException(status_code=404, detail={"code": "MERCHANT_NOT_FOUND"})
    return {"threads": threads}


@app.get("/api/v1/world/tickets/{ticket_id}/thread")
def get_world_thread(ticket_id: str) -> dict[str, Any]:
    """One conversation with every message, for the front end only."""
    config = load_config()
    if not config.world_database_path:
        raise HTTPException(status_code=503, detail={"code": "WORLD_NOT_CONFIGURED"})
    thread = ticket_thread(config, ticket_id)
    if thread is None:
        raise HTTPException(status_code=404, detail={"code": "THREAD_NOT_FOUND"})
    return thread


@app.get("/api/v1/overview")
def get_overview(request: Request) -> dict[str, Any]:
    rows = request.app.state.store.list_tickets()
    counts: dict[str, int] = {}
    for row in rows:
        status = "sent_open" if row["status"] == "sent_simulated" else row["status"]
        counts[status] = counts.get(status, 0) + 1
    waiting = [row for row in rows if row["status"] in {"awaiting_validation", "awaiting_reroute", "manual_handling", "ready_to_send"}]
    oldest = min((datetime.fromisoformat(row["created_at"]) for row in waiting), default=None)
    oldest_seconds = max(0, (datetime.now(UTC) - oldest).total_seconds()) if oldest else 0
    sent_open = counts.get("sent_open", 0)
    sent_closed = counts.get("sent_closed", 0)
    return {
        "total": len(rows), "by_status": counts,
        "queues": {"re-router": counts.get("awaiting_reroute", 0),
                   "validator": sum(counts.get(key, 0) for key in ("awaiting_validation", "ready_to_send", "manual_handling")),
                   "errors": counts.get("error", 0)},
        "simulated_sends": sent_open + sent_closed,
        "send_dispositions": {
            "leave_open": sent_open,
            "close": sent_closed,
            "closed_without_reply": counts.get("closed_manual", 0),
        },
        "oldest_waiting_seconds": round(oldest_seconds, 1),
        "ratios": {"human_review_rate": {"numerator": len(waiting), "denominator": len(rows)}},
    }


DEMO_MAX_COUNT = 20


class DemoInjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int = Field(ge=1, le=DEMO_MAX_COUNT)
    auto_handle: bool = False


def _demo_enabled() -> bool:
    return os.environ.get("NAVY_DEMO_MODE") == "1"


@app.get("/api/v1/demo")
def demo_status() -> dict[str, Any]:
    return {"enabled": _demo_enabled(), "max_count": DEMO_MAX_COUNT}


@app.post("/api/v1/demo/inject", status_code=202)
def demo_inject(body: DemoInjectRequest, request: Request, background: BackgroundTasks) -> dict[str, Any]:
    """Demo only: submit fresh `val` tickets (never the locked test splits); optionally play the human."""
    if not _demo_enabled():
        raise HTTPException(404, detail={"code": "DEMO_MODE_OFF"})
    import csv

    from flow import demo_agent
    from flow.inject_dataset import SPLITS, _merchant_id, build_envelope

    store: ApiStore = request.app.state.store
    with SPLITS["val"].open(encoding="utf-8", newline="") as handle:
        fresh = [row for row in csv.DictReader(handle) if store.ticket(f"val-{row['card_id']}", 1) is None]
    if len(fresh) < body.count:
        raise HTTPException(409, detail={"code": "DEMO_TICKETS_EXHAUSTED", "remaining": len(fresh)})
    # seeded by what is already injected: deterministic for a given state, different on each click
    rows = random.Random(len(store.list_tickets())).sample(fresh, body.count)
    now = datetime.now(UTC)
    merchant_id = _merchant_id()
    ids = []
    for row in rows:
        ticket = Ticket.model_validate(build_envelope(row, "val", merchant_id, 1, now))
        submit_ticket(ticket, request, Response(), f"demo-{ticket.ticket_id}")
        ids.append(ticket.ticket_id)
    if body.auto_handle:
        background.add_task(
            demo_agent.operate, str(request.base_url).rstrip("/"), f"demo-ui-{uuid4().hex[:8]}",
            set(ids), demo_agent.desks_for(rows), 3.0, 1800.0,
        )
    return {"injected": ids, "auto_handle": body.auto_handle}


# Container image: serve the built front end from the same origin. Mounted last so that it never
# shadows an API route; unset in local development, where Vite serves the front end.
_STATIC_DIR = os.environ.get("NAVY_STATIC_DIR")
if _STATIC_DIR:
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="front")


