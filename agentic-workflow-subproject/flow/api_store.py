"""SQLite domain state for the local frontend API.

LangGraph checkpoints are stored separately by its SQLite checkpointer. This
repository keeps the queryable business projection and idempotency records.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from pydantic import BaseModel


class IdempotencyConflict(ValueError):
    """An idempotency key was reused with a different canonical request."""


class VersionConflict(ValueError):
    """The caller's expected ticket version is stale."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class ApiStore:
    """Durable ticket projection, lifecycle events, jobs, and request keys."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS api_tickets (
                    ticket_id TEXT NOT NULL,
                    turn INTEGER NOT NULL,
                    flow_id TEXT NOT NULL UNIQUE,
                    thread_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    desk TEXT,
                    priority TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    ticket_json TEXT NOT NULL,
                    run_json TEXT,
                    error_code TEXT,
                    PRIMARY KEY (ticket_id, turn)
                );
                CREATE INDEX IF NOT EXISTS api_tickets_status_created
                    ON api_tickets(status, created_at);
                CREATE TABLE IF NOT EXISTS api_idempotency (
                    scope TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (scope, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS api_lifecycle_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    turn INTEGER NOT NULL,
                    event_index INTEGER NOT NULL,
                    ticket_version INTEGER NOT NULL,
                    node_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    duration_ms REAL,
                    safe_error_code TEXT,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(ticket_id, turn) REFERENCES api_tickets(ticket_id, turn),
                    UNIQUE(ticket_id, turn, event_index)
                );
                CREATE TABLE IF NOT EXISTS api_jobs (
                    flow_id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    turn INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    command_json TEXT,
                    FOREIGN KEY(ticket_id, turn) REFERENCES api_tickets(ticket_id, turn)
                );
                """
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=15.0)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=15000")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_idempotent(self, scope: str, key: str, request_sha256: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT request_sha256, response_json FROM api_idempotency "
                "WHERE scope=? AND idempotency_key=?", (scope, key),
            ).fetchone()
        if row is None:
            return None
        if row["request_sha256"] != request_sha256:
            raise IdempotencyConflict("idempotency key belongs to a different request")
        return json.loads(row["response_json"])

    def save_idempotent(self, scope: str, key: str, request_sha256: str, response: Any) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO api_idempotency(scope,idempotency_key,request_sha256,response_json,created_at) "
                "VALUES(?,?,?,?,?)",
                (scope, key, request_sha256, _json(response), _now()),
            )
            row = connection.execute(
                "SELECT request_sha256 FROM api_idempotency WHERE scope=? AND idempotency_key=?",
                (scope, key),
            ).fetchone()
            if row["request_sha256"] != request_sha256:
                raise IdempotencyConflict("idempotency key belongs to a different request")

    def reserve_action(
        self, *, scope: str, key: str, request_sha256: str, ticket_id: str, turn: int,
        expected_version: int, status: str, run: Any, command: Any,
    ) -> tuple[dict[str, Any], bool]:
        """Atomically reserve a version, persist a resumable command, and its idempotency reply."""
        now = _now()
        payload = _json(run)
        with self._connection() as connection:
            prior = connection.execute(
                "SELECT request_sha256,response_json FROM api_idempotency WHERE scope=? AND idempotency_key=?",
                (scope, key),
            ).fetchone()
            if prior:
                if prior["request_sha256"] != request_sha256:
                    raise IdempotencyConflict("idempotency key belongs to a different request")
                return json.loads(prior["response_json"]), False
            new_version = expected_version + 1
            cursor = connection.execute(
                "UPDATE api_tickets SET status=?,run_json=?,error_code=NULL,updated_at=?,version=? "
                "WHERE ticket_id=? AND turn=? AND version=?",
                (status, payload, now, new_version, ticket_id, turn, expected_version),
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM api_tickets WHERE ticket_id=? AND turn=?", (ticket_id, turn)
                ).fetchone()
                if exists is None:
                    raise KeyError((ticket_id, turn))
                raise VersionConflict("ticket version changed")
            connection.execute(
                "UPDATE api_jobs SET status='queued',attempts=attempts+1,updated_at=?,command_json=? "
                "WHERE ticket_id=? AND turn=?",
                (now, _json(command), ticket_id, turn),
            )
            response = {"ticket_id": ticket_id, "turn": turn, "status": "processing", "version": new_version}
            connection.execute(
                "INSERT INTO api_idempotency(scope,idempotency_key,request_sha256,response_json,created_at) "
                "VALUES(?,?,?,?,?)",
                (scope, key, request_sha256, _json(response), now),
            )
            return response, True

    def insert_ticket(
        self, *, ticket_id: str, turn: int, flow_id: str, thread_id: str,
        ticket: Any, status: str = "queued",
    ) -> bool:
        now = _now()
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO api_tickets "
                "(ticket_id,turn,flow_id,thread_id,status,created_at,updated_at,ticket_json) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (ticket_id, turn, flow_id, thread_id, status, now, now, _json(ticket)),
            )
            if cursor.rowcount:
                connection.execute(
                    "INSERT INTO api_jobs(flow_id,ticket_id,turn,status,updated_at) VALUES(?,?,?,?,?)",
                    (flow_id, ticket_id, turn, "queued", now),
                )
            return cursor.rowcount == 1

    def ticket(self, ticket_id: str, turn: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM api_tickets WHERE ticket_id=? AND turn=?", (ticket_id, turn)
            ).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["ticket"] = json.loads(result.pop("ticket_json"))
            result["run"] = json.loads(result.pop("run_json")) if result["run_json"] else None
            return result

    def ticket_by_flow(self, flow_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT ticket_id,turn FROM api_tickets WHERE flow_id=?", (flow_id,)
            ).fetchone()
        return self.ticket(row["ticket_id"], row["turn"]) if row else None

    def previous_run(self, ticket_id: str, turn: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT run_json FROM api_tickets WHERE ticket_id=? AND turn=?",
                (ticket_id, turn - 1),
            ).fetchone()
        return json.loads(row["run_json"]) if row and row["run_json"] else None

    def history(self, ticket_id: str, before_turn: int) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT turn,status,desk,priority,created_at,updated_at,ticket_json,run_json "
                "FROM api_tickets WHERE ticket_id=? AND turn<? ORDER BY turn",
                (ticket_id, before_turn),
            ).fetchall()
        history = []
        for row in rows:
            status = "sent_open" if row["status"] == "sent_simulated" else row["status"]
            run = json.loads(row["run_json"]) if row["run_json"] else None
            if isinstance(run, dict) and run.get("status") == "sent_simulated":
                run["status"] = "sent_open"
                run.setdefault("send_disposition", "leave_open")
                receipt = run.get("send_receipt")
                if isinstance(receipt, dict):
                    receipt.setdefault("disposition", "leave_open")
                for item in run.get("send_receipts", ()):
                    if isinstance(item, dict):
                        item.setdefault("disposition", "leave_open")
            history.append(
                {"turn": row["turn"], "status": status, "desk": row["desk"],
                 "priority": row["priority"], "created_at": row["created_at"],
                 "updated_at": row["updated_at"], "ticket": json.loads(row["ticket_json"]),
                 "run": run}
            )
        return history

    def update_ticket(
        self, ticket_id: str, turn: int, expected_version: int, *, status: str,
        run: Any | None = None, error_code: str | None = None,
        job_status: str | None = None, job_command: Any | None = None,
    ) -> int:
        now = _now()
        payload = _json(run) if run is not None else None
        with self._connection() as connection:
            new_version = expected_version + 1
            cursor = connection.execute(
                "UPDATE api_tickets SET status=?,run_json=COALESCE(?,run_json),error_code=?, "
                "updated_at=?,version=? WHERE ticket_id=? AND turn=? AND version=?",
                (status, payload, error_code, now, new_version, ticket_id, turn, expected_version),
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM api_tickets WHERE ticket_id=? AND turn=?", (ticket_id, turn)
                ).fetchone()
                if exists is None:
                    raise KeyError((ticket_id, turn))
                raise VersionConflict("ticket version changed")
            connection.execute(
                "UPDATE api_jobs SET status=?,attempts=attempts+1,updated_at=?,command_json=? "
                "WHERE ticket_id=? AND turn=?",
                (job_status or status, now, _json(job_command) if job_status == "queued" and job_command is not None else None, ticket_id, turn),
            )
        return new_version

    def list_tickets(
        self, statuses: tuple[str, ...] | None = None, *, limit: int | None = None,
        after: tuple[str, str, int] | None = None,
    ) -> list[dict[str, Any]]:
        with self._connection() as connection:
            clauses: list[str] = []
            params: list[Any] = []
            if statuses:
                clauses.append("status IN (" + ",".join("?" for _ in statuses) + ")")
                params.extend(statuses)
            if after:
                clauses.append("(created_at,ticket_id,turn)>(?,?,?)")
                params.extend(after)
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            limit_clause = " LIMIT ?" if limit is not None else ""
            if limit is not None:
                params.append(limit)
            rows = connection.execute(
                "SELECT ticket_id,turn FROM api_tickets" + where
                + " ORDER BY created_at,ticket_id,turn" + limit_clause,
                params,
            ).fetchall()
        return [self.ticket(row["ticket_id"], row["turn"]) for row in rows]

    def record_node_events(
        self, ticket_id: str, turn: int, version: int, start_index: int,
        events: list[dict[str, Any]],
    ) -> None:
        now = _now()
        with self._connection() as connection:
            for event in events:
                connection.execute(
                    "INSERT INTO api_lifecycle_events "
                    "(ticket_id,turn,event_index,ticket_version,node_id,status,occurred_at,duration_ms,safe_error_code,details_json) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(ticket_id,turn,event_index) DO NOTHING",
                    (ticket_id, turn, start_index, version, event["node_id"], event["status"],
                     event.get("occurred_at", now), event.get("duration_ms"),
                     event.get("safe_error_code"), _json(event.get("details", {}))),
                )
                start_index += 1

    def events(self, ticket_id: str, turn: int) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT node_id,status,occurred_at,duration_ms,safe_error_code,details_json "
                "FROM api_lifecycle_events WHERE ticket_id=? AND turn=? ORDER BY event_id",
                (ticket_id, turn),
            ).fetchall()
        return [
            {**dict(row), "details": json.loads(row["details_json"])} for row in rows
        ]

    def claim_jobs(self) -> list[dict[str, Any]]:
        """Claim queued jobs once; startup recovery is handled separately."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT flow_id,ticket_id,turn,command_json FROM api_jobs WHERE status='queued' ORDER BY updated_at"
            ).fetchall()
            for row in rows:
                connection.execute(
                    "UPDATE api_jobs SET status='processing',updated_at=? WHERE flow_id=?",
                    (_now(), row["flow_id"]),
                )
        jobs = [dict(row) for row in rows]
        for job in jobs:
            job["command"] = json.loads(job.pop("command_json")) if job.get("command_json") else None
        return jobs

    def requeue_interrupted_jobs(self) -> None:
        """Requeue work left processing by a previous process, once at startup."""
        with self._connection() as connection:
            connection.execute(
                "UPDATE api_jobs SET status='queued',updated_at=? WHERE status='processing'",
                (_now(),),
            )

    def mark_job(self, flow_id: str, status: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE api_jobs SET status=?,updated_at=?, "
                "command_json=CASE WHEN ? IN ('queued','processing') THEN command_json ELSE NULL END "
                "WHERE flow_id=?",
                (status, _now(), status, flow_id),
            )

    def mark_ticket_processing(self, ticket_id: str, turn: int) -> None:
        """Expose queued work as processing without invalidating the UI's version token."""
        with self._connection() as connection:
            connection.execute(
                "UPDATE api_tickets SET status='processing' "
                "WHERE ticket_id=? AND turn=? AND status!='error'",
                (ticket_id, turn),
            )
