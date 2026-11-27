"""Demo operator: inject seeded `val` tickets, then play the support human until done.

It uses only the public API, exactly like the UI, with the actor `demo-agent`, so the dashboard and
Langfuse fill with complete synthetic histories before a presentation. The re-routing choice uses
the ticket's reference desk from `val.csv`, standing in for the human's own judgement; it is sent as
a human action and never reaches the Qualifier. With `--llm`, an LLM plays the human where a person
must write: replies to tickets with no usable draft (human-only topics) and fixes of blocked drafts.
Every model call costs (Vertex time, OpenRouter).

    uv run python -m flow.demo_agent --limit 10 --seed 1 --llm
"""

import argparse
import csv
import hashlib
import logging
import os
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any

import httpx
from dotenv import load_dotenv

from flow.contracts import load_config
from flow.inject_dataset import (
    ROOT,
    SPLITS,
    TERMINAL_STATUSES,
    _request_json,
    inject,
    select_rows,
)
from flow.router import _CONTRACT_DESK
from ml.qualifier.src.scoring import desk_of, parse_output

logger = logging.getLogger(__name__)

# (item, draft text or None) -> reply text written as the human
Writer = Callable[[dict[str, Any], str | None], str]

HUMAN_PROMPT = (
    "You are an experienced Keelpay support agent (B2B payments) answering a merchant by email. "
    "Write the reply yourself, in the same language as the merchant's message. Be short, polite and "
    "concrete: acknowledge the issue, say what you checked or what the specialist team will do, and ask "
    "for any missing reference. Never promise a refund, an unfreeze, a fee waiver or a deadline, never "
    "quote an amount or a date, never give legal advice. Sign as 'Keelpay Support'. Return only the email body: no subject line, no Markdown."
)

ACTOR = "demo-agent"
QUEUES = ("validator", "re-router")
# ponytail: one fixed English reply when no draft can be approved; per-language texts if a demo needs them
FALLBACK_REPLY = (
    "Hello,\n\nThank you for your message. We have reviewed your request and a specialist is "
    "following it up; we will come back to you shortly.\n\nKind regards,\nKeelpay Support"
)


def ticket_id_of(row: dict[str, str]) -> str:
    """Ticket id as the injector submits it: bare card id for world rows, `val-<card>` for deck rows."""
    return row["card_id"] if "opened_at" in row else f"val-{row['card_id']}"


def desks_for(rows: list[dict[str, str]]) -> dict[str, str]:
    """Reference desk per ticket id. World rows carry no label: it comes from `val.csv` by card id."""
    targets: dict[str, str] = {}
    if any("target" not in row for row in rows):
        with SPLITS["val"].open(encoding="utf-8", newline="") as handle:
            targets = {row["card_id"]: row["target"] for row in csv.DictReader(handle)}
    return {
        ticket_id_of(row): _CONTRACT_DESK.get(desk_of(parse_output(row.get("target") or targets[row["card_id"]])), "payments")
        if (row.get("target") or row["card_id"] in targets) else "payments"
        for row in rows
    }


def reference_desks(limit: int, seed: int, world: Path | None = None) -> dict[str, str]:
    """Reference desk per injected ticket id, from the same seeded selection as the injector."""
    return desks_for(select_rows("val", limit, seed, world))


def llm_writer() -> Writer | None:
    """LLM playing the human writer (Drafter model on OpenRouter); None without an API key.

    One LLM text per ticket and turn: if the final gate refuses it, later attempts fall back to the
    fixed reply, so a refused text never loops on paid calls.
    """
    load_dotenv(ROOT / ".env")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    cfg = load_config()
    written: set[tuple[str, int]] = set()
    lock = Lock()

    def write(item: dict[str, Any], draft: str | None) -> str:
        slot = (item["ticket_id"], item["turn"])
        with lock:
            if slot in written:
                return draft or FALLBACK_REPLY
            written.add(slot)
        ticket = item.get("ticket") or {}
        user = f"Desk: {item.get('desk') or 'unknown'}\nSubject: {ticket.get('subject') or ''}\n\nMerchant message:\n{ticket.get('body', '')}"
        if draft:
            user += f"\n\nA colleague's draft, blocked by our policy check. Rewrite it safely:\n{draft}"
        try:
            response = httpx.post(
                cfg.drafter_url, headers={"Authorization": f"Bearer {key}"}, timeout=60,
                json={"model": cfg.drafter_model, "temperature": 0.4,
                      "messages": [{"role": "system", "content": HUMAN_PROMPT}, {"role": "user", "content": user}]},
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"].strip()
            return text or draft or FALLBACK_REPLY
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            logger.error("LLM human writer failed for %s: %s; using the fixed reply", item["ticket_id"], exc)
            return draft or FALLBACK_REPLY

    return write


def choose_action(item: dict[str, Any], desks: dict[str, str],
                  writer: Writer | None = None) -> tuple[str, dict[str, Any]] | None:
    """Pick the human action for one queue item; None when there is nothing to do yet."""
    allowed = item.get("allowed_actions") or []
    if "send" in allowed:
        return "send", {"actor": ACTOR, "disposition": "close"}
    if "approve" in allowed:
        return "actions", {"action": "approve", "actor": ACTOR}
    if "reroute" in allowed:
        desk = desks.get(item["ticket_id"], "payments")
        if desk == "triage":
            desk = "payments"
        return "actions", {"action": "reroute", "actor": ACTOR, "desk": desk, "reason": "demo-agent re-route"}
    if "close_manual" in allowed:
        return "actions", {"action": "close_manual", "actor": ACTOR, "reason": "demo-agent handled manually"}
    if "edit_draft" in allowed:
        draft = next(d for d in reversed(item["drafts"]) if not d["stale"])
        text = writer(item, draft["text"]) if writer else draft["text"]
        return "actions", {"action": "edit_draft", "actor": ACTOR, "text": text, "draft_version": draft["version"]}
    if "write_reply" in allowed:
        text = writer(item, None) if writer else FALLBACK_REPLY
        return "actions", {"action": "write_reply", "actor": ACTOR, "text": text}
    return None


def act(api: str, session_id: str, item: dict[str, Any], desks: dict[str, str],
        writer: Writer | None = None) -> str | None:
    choice = choose_action(item, desks, writer)
    if choice is None:
        return None
    route, payload = choice
    ticket_id, turn, version = item["ticket_id"], item["turn"], item["version"]
    key = hashlib.sha256(f"{session_id}:{ticket_id}:{turn}:{version}:{route}".encode()).hexdigest()[:40]
    _request_json(
        f"{api}/api/v1/tickets/{ticket_id}/turns/{turn}/{route}", method="POST", payload=payload,
        headers={"Idempotency-Key": f"demo-{key}", "If-Match": f'"{version}"'},
    )
    return payload.get("action", "send")


def operate(api: str, session_id: str, ticket_ids: set[str], desks: dict[str, str],
            cadence: float, timeout: float, writer: Writer | None = None) -> int:
    """Poll the queues and act until every injected ticket is terminal (or in error)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pending = 0
        for ticket_id in sorted(ticket_ids):
            try:
                item = _request_json(f"{api}/api/v1/tickets/{ticket_id}/turns/1")
            except RuntimeError as exc:
                if "HTTP 404" in str(exc):  # injection of this ticket failed: nothing to operate
                    continue
                raise
            if item["status"] in TERMINAL_STATUSES or item["status"] == "error":
                continue
            pending += 1
            try:
                done = act(api, session_id, item, desks, writer)
            except RuntimeError as exc:  # stale version or busy flow: retry on the next poll
                print(f"  {ticket_id}: retry later ({exc})", file=sys.stderr)
                continue
            if done:
                print(f"  {ticket_id}: {done}", flush=True)
                time.sleep(cadence)
        if pending == 0:
            print("all tickets resolved")
            return 0
        time.sleep(cadence)
    print("timeout: some tickets are still open", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, required=True, help="tickets to inject from val.csv")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--world", type=Path, help="draw the dev tickets (with their merchants) from this world database")
    parser.add_argument("--workers", type=int, default=1, help="parallel fake reviewers, each owning a slice of the tickets")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--cadence", type=float, default=3.0, help="seconds between human actions")
    parser.add_argument("--timeout", type=float, default=3600, help="give up after this many seconds")
    parser.add_argument("--llm", action="store_true", help="an LLM writes the human replies (needs OPENROUTER_API_KEY)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.limit < 1 or args.workers < 1:
        parser.error("--limit and --workers must be positive")
    api = args.api.rstrip("/")
    session_id = f"demo-agent-{'world' if args.world else 'val'}-seed-{args.seed}-n-{args.limit}"
    status = inject(
        split="val", limit=args.limit, seed=args.seed, api=api, session_id=session_id, followups={},
        log_path=ROOT / ".local" / "runs" / "demo-agent.jsonl", wait_timeout=args.timeout,
        allow_locked_split=False, submit=True, world=args.world,
    )
    if status:
        print("some injections failed; operating on the tickets that were accepted", file=sys.stderr)
    writer = llm_writer() if args.llm else None
    if args.llm and writer is None:
        parser.error("--llm needs OPENROUTER_API_KEY in .env")
    desks = reference_desks(args.limit, args.seed, args.world)
    ids = sorted(desks)
    slices = [set(ids[index::args.workers]) for index in range(args.workers)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = pool.map(lambda part: operate(api, session_id, part, desks, args.cadence, args.timeout, writer), slices)
        return max(results)


if __name__ == "__main__":
    raise SystemExit(main())
