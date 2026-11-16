"""Write the history threads: ``python -m flow.world.threads.generate`` (stub unless --live).

One call per thread. Accepted threads go to an append-only log that the database build ingests;
every call is logged with its cost in a folder that holds nothing else.
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
from collections.abc import Callable
from pathlib import Path

import httpx
from dotenv import load_dotenv

from flow.world.config import DEFAULT_CONFIG_PATH, PROJECT_ROOT, WorldConfig, load_world_config
from flow.world.deck import load_deck
from flow.world.threads.checks import check_thread
from flow.world.threads.plan import ThreadPlan, plan_threads
from flow.world.validate import STAMP_FORMAT
from ml.qualifier.src.dataset_build.openrouter import (
    Budget,
    BudgetExhaustedError,
    Completion,
    estimate_call_cost,
    load_run_config,
    parse_json_object,
)
from ml.qualifier.src.dataset_build.openrouter import complete as live_complete

LOGGER = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).with_name("prompt.txt")
ACCEPTED_FILE = "accepted.jsonl"
CALLS_FILE = "calls.jsonl"
ATTEMPTS = 2  # one try and one retry before the fallback thread
Complete = Callable[[str, str], Completion]
Estimate = Callable[[str, str], float]


def render_user(plan: ThreadPlan) -> str:
    """The only inputs of the model: opening text, desk, sub-intent, facts, guidance and plan."""
    lines = [
        f"Language: {plan.language}. Channel: {plan.channel}.",
        f"Desk: {plan.desk}. Topic: {plan.sub_intent}.",
        "Facts:",
        *[f"- {fact}" for fact in plan.facts],
        f"Approved guidance: {plan.policy or 'none'}",
        "Merchant's first message:",
        plan.opening,
    ]
    ending = (
        "ends waiting for the merchant (question or request)"
        if plan.state == "open_awaiting_merchant"
        else "ends closed (answer, no question)"
    )
    lines.append(f"Write these messages, the thread {ending}:")
    lines += [f"- turn {m.turn_index}: {m.author_kind}" for m in plan.messages]
    return "\n".join(lines)


def stub_complete(system: str, user: str) -> Completion:
    """Zero-cost stand-in: a valid, figure-free answer for every turn asked."""
    turns = [int(n) for n in re.findall(r"- turn (\d+):", user)]
    closed = "ends closed" in user
    messages = []
    for position, turn in enumerate(turns):
        text = "Thank you for your message." if turn % 2 else "We are looking into this."
        if position == len(turns) - 1:
            text = "This is now resolved." if closed else "Could you send us more details?"
        messages.append({"turn_index": turn, "body": text})
    return Completion(
        content=json.dumps({"messages": messages}),
        prompt_tokens=0,
        completion_tokens=0,
        cost_usd=0.0,
    )


def fallback_thread(plan: ThreadPlan, config: WorldConfig) -> dict[int, str]:
    """Minimal replacement: one agent reply built from the guidance, a question if it must wait."""
    reply = plan.policy or "Thank you for your message; we are reviewing it."
    if plan.state == "open_awaiting_merchant":
        reply = f"{reply} {config.threads.fallback_question.get(plan.language, '?')}"
    return {2: reply}


def _record(plan: ThreadPlan, bodies: dict[int, str], source: str, resolution: str, sha: str) -> dict:
    steps = {m.turn_index: m for m in plan.messages}
    stamp = {turn: steps[turn].sent_at.strftime(STAMP_FORMAT) for turn in bodies}
    last = stamp[max(bodies)]
    return {
        "ticket_id": plan.ticket_id,
        "source": source,
        "prompt_sha256": sha,
        "messages": [
            {
                "turn_index": turn,
                "author_kind": steps[turn].author_kind,
                "sent_at": stamp[turn],
                "body": bodies[turn].strip(),
            }
            for turn in sorted(bodies)
        ],
        "outcome": (
            {"desk": plan.desk, "resolution": resolution, "closed_at": last}
            if plan.state == "closed"
            else None
        ),
    }


def _append(path: Path, entry: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def _try_thread(
    plan: ThreadPlan, config: WorldConfig, system: str, call: Complete, budget: Budget,
    estimate: Estimate, calls_path: Path,
) -> dict[int, str] | None:
    """Written messages of one thread that pass the checks, or None after the retries."""
    user = render_user(plan)
    for attempt in range(1, ATTEMPTS + 1):
        budget.ensure(estimate(system, user))
        completion = call(system, user)
        budget.add(completion.cost_usd)
        bodies: dict[int, str] | None = None
        try:
            data = parse_json_object(completion.content)
            bodies = {int(m["turn_index"]): str(m["body"]) for m in data["messages"]}  # type: ignore[index]
            problems = check_thread(plan, bodies, config.threads.max_chars)
        except (KeyError, TypeError, ValueError) as error:  # JSONDecodeError is a ValueError
            problems = [f"unreadable answer: {type(error).__name__}"]
        _append(
            calls_path,
            {
                "ticket_id": plan.ticket_id,
                "attempt": attempt,
                "cost_usd": completion.cost_usd,
                "prompt_tokens": completion.prompt_tokens,
                "completion_tokens": completion.completion_tokens,
                "problems": problems,
            },
        )
        if not problems and bodies is not None:
            return bodies
    return None


def write_threads(
    plans: list[ThreadPlan], config: WorldConfig, system: str, call: Complete, budget: Budget,
    estimate: Estimate, calls_dir: Path, thread_dir: Path,
) -> dict[str, float]:
    """Generate, check, retry once, fall back; append accepted threads and every call."""
    thread_dir.mkdir(parents=True, exist_ok=True)
    calls_dir.mkdir(parents=True, exist_ok=True)
    accepted_path = thread_dir / ACCEPTED_FILE
    done = (
        {json.loads(line)["ticket_id"] for line in accepted_path.read_text("utf-8").splitlines()}
        if accepted_path.exists()
        else set()
    )
    counts = {"llm": 0, "fallback": 0, "skipped": 0}
    sha = hashlib.sha256(system.encode()).hexdigest()
    for plan in plans:
        if plan.ticket_id in done:
            counts["skipped"] += 1
            continue
        bodies = _try_thread(plan, config, system, call, budget, estimate, calls_dir / CALLS_FILE)
        source = "llm" if bodies is not None else "fallback"
        written = bodies if bodies is not None else fallback_thread(plan, config)
        _append(accepted_path, _record(plan, written, source, config.threads.resolution, sha))
        counts[source] += 1
    return {**counts, "spent_usd": round(budget.spent_usd, 4)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--limit", type=int, required=True, help="threads to write in this run")
    parser.add_argument("--live", action="store_true", help="call OpenRouter (paid)")
    parser.add_argument("--pilot", action="store_true", help="use the pilot cap")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = load_world_config(arguments.config)
    deck_dir = config.resolve(config.paths.deck_dir)
    deck = {t.card_id: t for t in load_deck(deck_dir, config.text_newline)}
    database = config.resolve(config.paths.database_path)
    conn = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    plans = list(plan_threads(conn, deck, config))[: arguments.limit]
    conn.close()
    system = PROMPT_PATH.read_text(encoding="utf-8")
    root = config.resolve(config.paths.artifacts_dir) / "threads"
    cap = config.budget.pilot_cap_usd if arguments.pilot else config.budget.cap_usd
    if not arguments.live:
        stub = PROJECT_ROOT / ".local" / "world" / "threads_stub"
        counts = write_threads(
            plans, config, system, stub_complete, Budget(cap), lambda s, u: 0.0, stub / "calls", stub
        )
        LOGGER.info("stub threads: %s", counts)
        return
    load_dotenv(PROJECT_ROOT / ".env")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is required for --live")
    run = load_run_config()
    role = run.roles[config.threads.role].model_copy(update={"max_tokens": config.threads.max_tokens})
    calls_dir = config.resolve(config.budget.calls_dir)
    with httpx.Client() as client:
        try:
            counts = write_threads(
                plans, config, system,
                lambda s, u: live_complete(client, run, role, key, s, u),
                Budget.from_logs(cap, calls_dir),
                lambda s, u: estimate_call_cost(role, s, u),
                calls_dir, root,
            )
        except BudgetExhaustedError as error:
            raise SystemExit(f"stopped: {error}") from error
    LOGGER.info("threads: %s", counts)


if __name__ == "__main__":
    main()
