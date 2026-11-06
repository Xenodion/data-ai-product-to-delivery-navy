"""Feeds validation tickets to the flow and appends each finished run to a JSONL file."""

import argparse
import csv
import logging
import os
import random
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

import httpx
from dotenv import load_dotenv
from langfuse import get_client

from flow.contracts import FlowConfig, FlowDeps, Ticket, TicketRun, load_config
from flow.drafter import write_draft
from flow.pipeline import process
from flow.qualifier import qualify
from ml.qualifier.src.local_paths import RUNS_DIR

logger = logging.getLogger(__name__)

VAL_PATH = Path(__file__).parent.parent / "data" / "dataset" / "val.csv"


def select_tickets(path: Path, n: int, seed: int, merchant_id: str) -> list[Ticket]:
    """Pick ``n`` tickets repeatably. Only the ID and the text leave the file, never the labels."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [(row["card_id"], row["ticket"]) for row in csv.DictReader(handle)]
    chosen = random.Random(seed).sample(rows, n)
    return [
        Ticket(ticket_id=card_id, merchant_id=merchant_id, text=text, created_at=datetime.now(UTC))
        for card_id, text in chosen
    ]


def run_tickets(
    tickets: list[Ticket],
    deps: FlowDeps,
    output: Path,
    every_seconds: float = 0.0,
    step: Callable[[Ticket, FlowDeps], TicketRun] = process,
) -> None:
    """Process tickets in order, flushing each line so that a crash keeps finished tickets."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as handle:
        for index, ticket in enumerate(tickets):
            if index and every_seconds:
                time.sleep(every_seconds)
            run = step(ticket, deps)
            handle.write(run.model_dump_json() + "\n")
            handle.flush()
            logger.info("%s -> %s (%s)", ticket.ticket_id, run.status, run.desk)


def build_deps(
    qualifier_client: httpx.Client, drafter_client: httpx.Client, config: FlowConfig
) -> FlowDeps:
    return FlowDeps(
        qualify=partial(qualify, client=qualifier_client, config=config),
        draft=partial(write_draft, client=drafter_client, config=config),
        policy_version=config.policy_version,
    )


def _flush_traces() -> None:
    """Traces are best effort: a Langfuse failure must not fail a finished run."""
    try:
        get_client().flush()
    except Exception as exc:  # noqa: BLE001 - the SDK raises transport-specific errors
        logger.error("Langfuse flush failed: %s", exc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--every", type=float, default=0.0, help="seconds between tickets")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv(Path(__file__).parent.parent / ".env")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY is missing")
        return 1

    config = load_config()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = RUNS_DIR / f"{run_id}.jsonl"
    # Separate clients: the local Qualifier never receives the OpenRouter key.
    with (
        httpx.Client() as qualifier_client,
        httpx.Client(headers={"Authorization": f"Bearer {api_key}"}) as drafter_client,
    ):
        try:
            run_tickets(
                select_tickets(VAL_PATH, args.n, args.seed, config.merchant_id),
                build_deps(qualifier_client, drafter_client, config),
                output,
                args.every,
            )
        finally:
            _flush_traces()
    logger.info("Run written to %s", output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
