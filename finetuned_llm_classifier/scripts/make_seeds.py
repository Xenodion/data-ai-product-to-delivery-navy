"""Gate 1: write the 30 seed tickets and export them for a human read.

python scripts/make_seeds.py --dry-run        # render prompts, estimate the cost, call nothing
python scripts/make_seeds.py --limit 3        # canary: 3 paid calls
python scripts/make_seeds.py                  # all seeds not yet in the log (resumable)
"""

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os

import httpx
from dotenv import load_dotenv

from src.dataset_build.cards import Card, draw_cards, load_config
from src.dataset_build.generation_prompt import load_prompt_config, render_prompt
from src.dataset_build.openrouter import (
    Budget,
    Completion,
    RoleConfig,
    complete,
    estimate_call_cost,
    load_run_config,
)
from src.dataset_build.runner import TicketRecord, read_log, write_tickets

SEED_PROFILE = "seeds"
SEED_COUNT = 30
SEED_DRAW = 20261031
ROLE = "seed_writer"
RUN_DIR = PROJECT_ROOT / "data" / "runs"
LOG_PATH = RUN_DIR / "seeds.jsonl"
REVIEW_PATH = PROJECT_ROOT / "data" / "seeds" / "seeds_review.md"

logger = logging.getLogger("make_seeds")


def export_review(cards: list[Card], records: list[TicketRecord]) -> None:
    """Markdown file to read: for each seed, what was asked, the ticket, and the automatic verdict."""
    by_id = {record.card_id: record for record in records}
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Seeds to review (gate 1)",
        "",
        "For each seed: is the ticket realistic, and does it carry exactly the label?",
        "",
    ]
    for card in cards:
        record = by_id.get(card.card_id)
        if record is None:
            continue
        lines += [
            f"## {card.card_id}  [{record.status}{': ' + ', '.join(record.reasons) if record.reasons else ''}]",
            f"- label: `{card.label.model_dump_json()}`",
            f"- traps: {', '.join(card.traps) or 'none'} | {card.language} | {card.channel} | {card.length} | noise: {', '.join(card.noise) or 'none'}",
            "",
            "```text",
            record.ticket or record.body,
            "```",
            "",
        ]
    REVIEW_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=SEED_COUNT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cards = draw_cards(load_config(), SEED_PROFILE, SEED_COUNT, SEED_DRAW)
    run_config, prompt_config = load_run_config(), load_prompt_config()
    role = run_config.roles[ROLE]
    todo = [
        card
        for card in cards
        if card.card_id not in {r.card_id for r in read_log(LOG_PATH)}
    ][: args.limit]

    if args.dry_run:
        estimate = sum(
            estimate_call_cost(role, *render_prompt(card, prompt_config))
            for card in todo
        )
        logger.info(
            "dry run: %d calls to %s, estimated upper bound %.4f USD, nothing sent",
            len(todo),
            role.model,
            estimate,
        )
        return

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key or api_key.startswith("your-"):
        raise SystemExit("OPENROUTER_API_KEY is missing from the sub-project .env")
    budget = (
        Budget.from_logs(run_config.budget_usd, RUN_DIR)
        if RUN_DIR.exists()
        else Budget(run_config.budget_usd)
    )

    with httpx.Client() as client:

        def call(role_config: RoleConfig, system: str, user: str) -> Completion:
            return complete(client, run_config, role_config, api_key, system, user)

        write_tickets(todo, ROLE, run_config, prompt_config, LOG_PATH, budget, call)
    records = read_log(LOG_PATH)
    export_review(cards, records)
    ok = sum(record.status == "ok" for record in records)
    logger.info(
        "%d/%d seeds pass the automatic checks; read %s", ok, len(records), REVIEW_PATH
    )


if __name__ == "__main__":
    main()
