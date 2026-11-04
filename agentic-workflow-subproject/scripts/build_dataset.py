"""Build the dataset split by split, in growing batches, then export the CSVs and the quarantines.

python scripts/build_dataset.py --dry-run                       # plan and cost estimate, nothing sent
python scripts/build_dataset.py --split train --max-batches 1   # first batch of one split
python scripts/build_dataset.py --split all                     # everything not yet produced (resumable)
python scripts/build_dataset.py --export-only                   # rebuild the CSVs from the logs

A stop rule that trips ends the run with a message: diagnose, then resume (--ignore-stop-rules only after a decision).
"""

import argparse
import logging
import math
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from dotenv import load_dotenv

from src.dataset_build.cards import load_config
from src.dataset_build.export import SPLITS, export_dataset
from src.dataset_build.generation_prompt import load_prompt_config
from src.dataset_build.openrouter import (
    Budget,
    Completion,
    RoleConfig,
    complete,
    load_run_config,
)
from src.dataset_build.production import (
    ProductionStoppedError,
    run_split,
    split_reserves,
)
from src.dataset_build.review import load_definitions
from src.dataset_build.splits import SplitSizes, draw_pool, split_pool

POOL_SEED = 20261031
RUN_DIR = PROJECT_ROOT / "data" / "runs"
OUT_DIR = PROJECT_ROOT / "data" / "dataset"
logger = logging.getLogger("build_dataset")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-batches", type=int, default=None)
    parser.add_argument("--ignore-stop-rules", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    card_config, run_config, prompt_config = (
        load_config(),
        load_run_config(),
        load_prompt_config(),
    )
    sizes = SplitSizes(**card_config.splits)
    pool = draw_pool(card_config, sizes, POOL_SEED)
    splits = split_pool(pool, sizes, POOL_SEED)
    reserves = split_reserves(pool, splits, run_config)
    cards_by_id = {card.card_id: card for card in pool}
    names = list(SPLITS) if args.split == "all" else [args.split]
    min_per_trap = {"test_traps": sizes.min_per_trap}

    if args.dry_run:
        settings = run_config.production
        total = 0.0
        for name in names:
            attempts = math.ceil(settings.attempts_factor * len(splits[name]))
            cost = attempts * settings.cost_per_ticket_estimate
            total += cost
            writer = run_config.roles[settings.writer_role[name]].model
            logger.info(
                "%-13s target %4d | up to %4d attempts | reserve %4d | writer %s | about %.2f USD",
                name,
                len(splits[name]),
                attempts,
                len(reserves[name]),
                writer,
                cost,
            )
        logger.info(
            "estimated upper bound for the selection: %.2f USD (budget %.2f, spent so far %.2f)",
            total,
            run_config.budget_usd,
            Budget.from_logs(run_config.budget_usd, RUN_DIR).spent_usd
            if RUN_DIR.exists()
            else 0.0,
        )
        return

    if not args.export_only:
        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key or api_key.startswith("your-"):
            raise SystemExit("OPENROUTER_API_KEY is missing from the sub-project .env")
        budget = (
            Budget.from_logs(run_config.budget_usd, RUN_DIR)
            if RUN_DIR.exists()
            else Budget(run_config.budget_usd)
        )
        definitions = load_definitions()
        with httpx.Client() as client:

            def call(role: RoleConfig, system: str, user: str) -> Completion:
                return complete(client, run_config, role, api_key, system, user)

            for name in names:
                try:
                    status = run_split(
                        name, splits[name], reserves[name], min_per_trap.get(name, 0), run_config, prompt_config,
                        definitions, budget, call, RUN_DIR, args.max_batches, args.ignore_stop_rules,
                    )  # fmt: skip
                except ProductionStoppedError as stop:
                    logger.error("STOP RULE: %s", stop)
                    break
                logger.info(
                    "%s: %d/%d accepted after %d attempts (%s), %.4f USD",
                    name,
                    status.accepted,
                    status.target,
                    status.attempted,
                    status.reason,
                    status.cost_usd,
                )

    counts = export_dataset(cards_by_id, RUN_DIR, OUT_DIR)
    logger.info("exported to %s: %s", OUT_DIR, counts)


if __name__ == "__main__":
    main()
