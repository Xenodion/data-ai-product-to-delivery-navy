"""Ask the (new) judge again for the tickets the previous judge rejected, in the production logs.

python scripts/rejudge.py --dry-run     # how many tickets would be judged again
python scripts/rejudge.py               # judge them; a new log line supersedes the old one
"""

import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from dotenv import load_dotenv

from src.dataset_build.cards import load_config
from src.dataset_build.export import SPLITS
from src.dataset_build.openrouter import (
    Budget,
    Completion,
    RoleConfig,
    complete,
    load_run_config,
)
from src.dataset_build.production import log_paths
from src.dataset_build.review import load_definitions, read_reviews, rejudge_rejected
from src.dataset_build.runner import read_log
from src.dataset_build.splits import SplitSizes, draw_pool

POOL_SEED = 20261031
RUN_DIR = PROJECT_ROOT / "data" / "runs"
logger = logging.getLogger("rejudge")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    card_config, run_config = load_config(), load_run_config()
    cards = {
        c.card_id: c
        for c in draw_pool(card_config, SplitSizes(**card_config.splits), POOL_SEED)
    }

    todo = {}
    for split in SPLITS:
        tickets_log, reviews_log = log_paths(RUN_DIR, split)
        latest = {r.card_id: r for r in read_reviews(reviews_log)}
        todo[split] = [
            (cards[t.card_id], t)
            for t in read_log(tickets_log)
            if (r := latest.get(t.card_id))
            and r.final == "rejected"
            and r.judge_verdict == "reject"
        ]
        logger.info(
            "%-13s %d judge rejections to look at again", split, len(todo[split])
        )
    if args.dry_run:
        return

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key or api_key.startswith("your-"):
        raise SystemExit("OPENROUTER_API_KEY is missing from the sub-project .env")
    budget = Budget.from_logs(run_config.budget_usd, RUN_DIR)
    definitions = load_definitions()
    with httpx.Client() as client:

        def call(role: RoleConfig, system: str, user: str) -> Completion:
            return complete(client, run_config, role, api_key, system, user)

        for split, items in todo.items():
            if items:
                done = rejudge_rejected(
                    items,
                    run_config,
                    log_paths(RUN_DIR, split)[1],
                    budget,
                    call,
                    definitions,
                )
                logger.info(
                    "%-13s recovered %d of %d (spent %.4f USD in total)",
                    split,
                    sum(r.final == "accepted" for r in done),
                    len(done),
                    budget.spent_usd,
                )


if __name__ == "__main__":
    main()
