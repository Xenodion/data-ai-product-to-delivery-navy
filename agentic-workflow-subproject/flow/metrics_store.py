"""Append-only local metric events with idempotent incremental aggregates."""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_NUMERIC_METRICS = {
    "qualifier_latency_ms",
    "drafter_latency_ms",
    "drafter_cost_usd",
    "flow_duration_ms",
}
_CATEGORICAL_METRICS = {
    "business_status",
    "evidence_mode",
    "policy_outcome",
    "final_gate_outcome",
    "human_action",
    "send_disposition",
}


class MetricsStore:
    """SQLite demo store. It contains allowlisted telemetry, never ticket text."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS flow_metric_events (
                    event_id TEXT PRIMARY KEY,
                    flow_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    safe_metrics_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS flow_metric_aggregates (
                    metric_name TEXT NOT NULL,
                    dimensions_json TEXT NOT NULL,
                    sample_count INTEGER NOT NULL DEFAULT 0,
                    total_value REAL NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (metric_name, dimensions_json)
                );
                """
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5.0)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=5000")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def record_node(
        self,
        *,
        event_id: str,
        flow_id: str,
        node_id: str,
        outcome: str,
        duration_ms: float,
        metrics: dict[str, Any],
    ) -> bool:
        """Insert one event and update its aggregates atomically; duplicate IDs are no-ops."""

        safe_metrics = {
            key: value
            for key, value in metrics.items()
            if key in _NUMERIC_METRICS | _CATEGORICAL_METRICS
            and isinstance(value, (str, int, float, bool))
        }
        dimensions = json.dumps(
            {"node_id": node_id, "outcome": outcome}, sort_keys=True, separators=(",", ":")
        )
        now = datetime.now(UTC).isoformat()
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO flow_metric_events "
                    "(event_id, flow_id, node_id, outcome, occurred_at, duration_ms, safe_metrics_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        event_id,
                        flow_id,
                        node_id,
                        outcome,
                        now,
                        duration_ms,
                        json.dumps(safe_metrics, sort_keys=True, separators=(",", ":")),
                    ),
                )
                if cursor.rowcount == 0:
                    return False
                self._increment(connection, "node_executions_total", dimensions, 1.0, now)
                self._increment(connection, "node_duration_ms", dimensions, duration_ms, now)
                for name, value in safe_metrics.items():
                    if name in _NUMERIC_METRICS and isinstance(value, (int, float)) and not isinstance(value, bool):
                        metric_dimensions = json.dumps(
                            {"node_id": node_id}, sort_keys=True, separators=(",", ":")
                        )
                        self._increment(connection, name, metric_dimensions, float(value), now)
                    elif name in _CATEGORICAL_METRICS:
                        metric_dimensions = json.dumps(
                            {"node_id": node_id, "value": str(value)},
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        self._increment(connection, f"{name}_total", metric_dimensions, 1.0, now)
                return True
        except sqlite3.Error:
            logger.exception("Local metrics write failed; workflow continues")
            return False

    @staticmethod
    def _increment(
        connection: sqlite3.Connection,
        name: str,
        dimensions: str,
        value: float,
        now: str,
    ) -> None:
        connection.execute(
            "INSERT INTO flow_metric_aggregates "
            "(metric_name, dimensions_json, sample_count, total_value, updated_at) "
            "VALUES (?, ?, 1, ?, ?) "
            "ON CONFLICT(metric_name, dimensions_json) DO UPDATE SET "
            "sample_count=sample_count+1, total_value=total_value+excluded.total_value, "
            "updated_at=excluded.updated_at",
            (name, dimensions, value, now),
        )

