"""Submit a bounded, reproducible slice of the frozen ticket CSVs to the local HTTP API.

The serving request contains only the ticket envelope. Dataset targets and annotations are
used neither to select a flow path nor copied to the API. Locked test splits require an
explicit opt-in and should only be replayed as a declared final evaluation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sqlite3
import sys
import time
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "dataset"
SPLITS = {
    "val": DATA_DIR / "val.csv",
    "test_natural": DATA_DIR / "test_natural.csv",
    "test_traps": DATA_DIR / "test_traps.csv",
}
LOCKED_SPLITS = {"test_natural", "test_traps"}
WORLD_ROLE_BY_SPLIT = {"val": "dev", "test_natural": "current"}
TERMINAL_STATUSES = {"sent_open", "sent_closed", "closed_manual"}


def _stable_time(card_id: str, turn: int, session_started_at: datetime) -> str:
    """Create a recent stable envelope timestamp from the immutable session manifest."""
    digest = hashlib.sha256(f"{card_id}:{turn}".encode()).digest()
    age_seconds = int.from_bytes(digest[:2], "big") % 900
    created = session_started_at - timedelta(seconds=age_seconds)
    return created.isoformat().replace("+00:00", "Z")


def _idempotency_key(session_id: str, card_id: str, turn: int) -> str:
    value = hashlib.sha256(f"{session_id}:{card_id}:{turn}".encode()).hexdigest()
    return f"dataset-{value}"


def read_world_rows(world: Path, split: str) -> list[dict[str, str]]:
    """First-contact tickets of the world database, in the deck row shape plus world fields."""
    role = WORLD_ROLE_BY_SPLIT.get(split)
    if role is None:
        raise ValueError(f"the world database has no {split} tickets")
    connection = sqlite3.connect(f"file:{world.as_posix()}?mode=ro", uri=True)
    try:
        cursor = connection.execute(
            "SELECT t.ticket_id, m.body, t.channel, t.language, t.merchant_id, t.opened_at "
            "FROM tickets t JOIN messages m ON m.ticket_id = t.ticket_id AND m.turn_index = 1 "
            "WHERE t.role = ? ORDER BY t.ticket_id",
            (role,),
        )
        keys = ("card_id", "ticket", "channel", "language", "merchant_id", "opened_at")
        return [dict(zip(keys, row, strict=True)) for row in cursor]
    finally:
        connection.close()


def select_rows(
    split: str, limit: int, seed: int, world: Path | None = None
) -> list[dict[str, str]]:
    path = SPLITS[split]
    if world is not None:
        rows = read_world_rows(world, split)
    else:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"dataset split is empty: {world or path}")
    if limit > len(rows):
        raise ValueError(f"--limit {limit} exceeds {split} size ({len(rows)})")
    selected = random.Random(seed).sample(rows, limit)
    return sorted(selected, key=lambda row: row["card_id"])


def _merchant_id() -> str:
    with (Path(__file__).parent / "config.toml").open("rb") as handle:
        merchant_id = tomllib.load(handle).get("merchant_id")
    if not isinstance(merchant_id, str) or not merchant_id.strip():
        raise ValueError("flow/config.toml must define a non-empty merchant_id")
    return merchant_id


def read_followups(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("follow-up file must be a JSON object: card_id -> list of reply strings")
    result: dict[str, list[str]] = {}
    for card_id, turns in payload.items():
        if not isinstance(card_id, str) or not isinstance(turns, list):
            raise ValueError("follow-up entries must map card IDs to lists")
        if any(not isinstance(body, str) or not body.strip() for body in turns):
            raise ValueError(f"follow-up bodies for {card_id} must be non-empty strings")
        result[card_id] = [body.strip() for body in turns]
    return result


def build_envelope(
    row: dict[str, str], split: str, merchant_id: str, turn: int,
    session_started_at: datetime, body: str | None = None,
) -> dict[str, Any]:
    """Project only user-visible ticket fields into the API request.

    A world row carries its own merchant and opening date; its ticket id is the bare card id.
    """
    world_row = "opened_at" in row
    created_at = (
        (datetime.fromisoformat(row["opened_at"]) + timedelta(hours=turn - 1))
        .astimezone(UTC).isoformat().replace("+00:00", "Z")
        if world_row
        else _stable_time(row["card_id"], turn, session_started_at)
    )
    return {
        "ticket_id": row["card_id"] if world_row else f"{split}-{row['card_id']}",
        "merchant_id": row.get("merchant_id") or merchant_id,
        "body": body if body is not None else row["ticket"],
        "created_at": created_at,
        "turn": turn,
        "channel": row.get("channel") or "formal_email",
        "subject": None,
        "language": row.get("language") or None,
        "attachments": [],
    }


def _write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _session_start(log_path: Path, session_id: str, split: str, seed: int, limit: int) -> datetime:
    """Persist a session's seed metadata once so safe replays reuse identical requests."""
    session_key = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:20]
    manifest_path = log_path.parent / f"dataset-injector-{session_key}.session.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    expected = {"session_id": session_id, "split": split, "seed": seed, "limit": limit}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if any(manifest.get(key) != value for key, value in expected.items()):
            raise ValueError("session ID already exists with different split, seed, or limit")
        return datetime.fromisoformat(manifest["started_at"])
    manifest = {**expected, "started_at": datetime.now(UTC).isoformat()}
    try:
        with manifest_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(manifest, sort_keys=True) + "\n")
    except FileExistsError:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if any(manifest.get(key) != value for key, value in expected.items()):
            raise ValueError("session ID already exists with different split, seed, or limit")
    return datetime.fromisoformat(manifest["started_at"])


def _request_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None,
                  headers: dict[str, str] | None = None, timeout: float = 20) -> dict[str, Any]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc


def _submit(api: str, envelope: dict[str, Any], key: str) -> dict[str, Any]:
    return _request_json(
        f"{api}/api/v1/tickets", method="POST", payload=envelope,
        headers={"Idempotency-Key": key},
    )


def _wait_for_terminal(api: str, ticket_id: str, turn: int, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"{api}/api/v1/tickets/{ticket_id}/turns/{turn}"
    while time.monotonic() < deadline:
        snapshot = _request_json(url, timeout=min(20, max(1, deadline - time.monotonic())))
        if snapshot.get("status") in TERMINAL_STATUSES:
            return snapshot
        if snapshot.get("status") == "error":
            raise RuntimeError(f"ticket {ticket_id} turn {turn} reached error: {snapshot.get('error_code')}")
        time.sleep(1)
    raise TimeoutError(f"ticket {ticket_id} turn {turn} did not reach a terminal state within {timeout:g}s")


def inject(
    *, split: str, limit: int, seed: int, api: str, session_id: str,
    followups: dict[str, list[str]], log_path: Path, wait_timeout: float,
    allow_locked_split: bool, submit: bool, world: Path | None = None,
) -> int:
    if split in LOCKED_SPLITS and not allow_locked_split:
        raise ValueError(f"{split} is locked; pass --allow-locked-split only for a declared final replay")
    rows = select_rows(split, limit, seed, world)
    merchant_id = _merchant_id()
    session_started_at = (
        _session_start(log_path, session_id, split, seed, limit)
        if submit else datetime.now(UTC)
    )
    envelopes = [(row, build_envelope(row, split, merchant_id, 1, session_started_at)) for row in rows]
    print(f"session={session_id} split={split} seed={seed} selected={len(rows)} api={api}")
    print(f"follow-up cases in slice: {sum(row['card_id'] in followups for row in rows)}")
    print("mode=submit" if submit else "mode=dry-run (no HTTP requests)")
    if not submit:
        for row, envelope in envelopes:
            print(f"  {envelope['ticket_id']} turn=1 body_sha256={hashlib.sha256(envelope['body'].encode()).hexdigest()[:12]}")
        return 0

    failures = 0
    for row, first in envelopes:
        ticket_id = first["ticket_id"]
        cases = [(1, first)] + [
            (turn, build_envelope(row, split, merchant_id, turn, session_started_at, body))
            for turn, body in enumerate(followups.get(row["card_id"], []), start=2)
        ]
        for turn, envelope in cases:
                key = _idempotency_key(session_id, row["card_id"], turn)
                record: dict[str, Any] = {
                    "session_id": session_id, "split": split, "seed": seed,
                    "card_id": row["card_id"], "ticket_id": ticket_id, "turn": turn,
                    "request_sha256": hashlib.sha256(json.dumps(envelope, sort_keys=True).encode()).hexdigest(),
                    "idempotency_key_sha256": hashlib.sha256(key.encode()).hexdigest(),
                    "started_at": datetime.now(UTC).isoformat(),
                }
                try:
                    accepted = _submit(api, envelope, key)
                    record["accepted"] = accepted
                    if turn < len(cases):
                        previous = _wait_for_terminal(api, ticket_id, turn, wait_timeout)
                        record["previous_turn_terminal_status"] = previous["status"]
                        if previous["status"] != "sent_open":
                            record["followups_skipped"] = len(cases) - turn
                            record["skip_reason"] = "PREVIOUS_TURN_CLOSED"
                            record["completed_at"] = datetime.now(UTC).isoformat()
                            _write_record(log_path, record)
                            print(f"  {ticket_id} turn={turn + 1}: skipped (previous turn was closed)")
                            break
                    record["completed_at"] = datetime.now(UTC).isoformat()
                    _write_record(log_path, record)
                    print(f"  {ticket_id} turn={turn}: accepted ({accepted.get('status', 'unknown')})")
                except (URLError, RuntimeError, TimeoutError) as exc:
                    failures += 1
                    record["error"] = f"{type(exc).__name__}: {exc}"
                    record["completed_at"] = datetime.now(UTC).isoformat()
                    _write_record(log_path, record)
                    print(f"  {ticket_id} turn={turn}: failed ({type(exc).__name__})", file=sys.stderr)
                    break
    print(f"session complete: failures={failures}; append-only log: {log_path}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=tuple(SPLITS), default="val")
    parser.add_argument("--limit", type=int, required=True, help="positive maximum tickets in this bounded session")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session-id", help="stable idempotency namespace; defaults to split-seed-limit")
    parser.add_argument("--followups", type=Path, help="JSON mapping card_id to customer reply strings")
    parser.add_argument("--wait-timeout", type=float, default=1800, help="wait for prior send/manual-close before next turn")
    parser.add_argument("--world", type=Path, help="draw dev (val) or current (test_natural) tickets from this world database")
    parser.add_argument("--allow-locked-split", action="store_true")
    parser.add_argument("--log", type=Path, default=ROOT / ".local" / "runs" / "dataset-injector.jsonl")
    parser.add_argument("--submit", action="store_true", help="send HTTP requests; without this flag, only preview")
    args = parser.parse_args()
    if args.limit < 1 or args.wait_timeout <= 0:
        parser.error("--limit and --wait-timeout must be positive")
    session_id = args.session_id or f"{args.split}-seed-{args.seed}-n-{args.limit}"
    try:
        return inject(
            split=args.split, limit=args.limit, seed=args.seed, api=args.api.rstrip("/"),
            session_id=session_id, followups=read_followups(args.followups),
            log_path=args.log, wait_timeout=args.wait_timeout,
            allow_locked_split=args.allow_locked_split, submit=args.submit, world=args.world,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
