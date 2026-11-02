"""Export the produced splits: one CSV of accepted tickets and one quarantine CSV per split.

The dataset CSVs feed the training pipeline (columns ``ticket`` and ``target``) and the scoring (metadata). The
quarantine keeps every non-conforming ticket with its reason: nothing is deleted, nothing is reused.
"""

import csv
import re
from pathlib import Path

from src.dataset_build.cards import Card
from src.dataset_build.production import accepted_ids, log_paths
from src.dataset_build.review import ReviewRecord, read_reviews
from src.dataset_build.runner import TicketRecord, read_log

SPLITS = ("train", "val", "test_natural", "test_traps")
TEST_SPLITS = ("test_natural", "test_traps")
SHINGLE_WORDS = 5
NEAR_DUPLICATE_JACCARD = 0.5
DATASET_COLUMNS = (
    "card_id", "ticket", "target", "traps", "language", "channel", "length", "persona", "sector",
    "noise", "sentinel_kind", "id_case", "amount_case", "writer_model", "prompt_version", "voter_b_checked",
)  # fmt: skip
QUARANTINE_COLUMNS = ("reason", *DATASET_COLUMNS)


def shingles(text: str) -> set[str]:
    words = re.findall(r"\w+", text.lower())
    return {
        " ".join(words[i : i + SHINGLE_WORDS])
        for i in range(max(len(words) - SHINGLE_WORDS + 1, 1))
    }


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _row(
    card: Card, ticket: TicketRecord, review: ReviewRecord | None
) -> dict[str, str]:
    return {
        "card_id": card.card_id,
        "ticket": ticket.ticket or ticket.body,
        "target": card.label.model_dump_json(),
        "traps": "|".join(card.traps),
        "language": card.language,
        "channel": card.channel,
        "length": card.length,
        "persona": card.persona,
        "sector": card.sector,
        "noise": "|".join(card.noise),
        "sentinel_kind": card.sentinel_kind,
        "id_case": card.id_case,
        "amount_case": card.amount_case,
        "writer_model": ticket.model,
        "prompt_version": ticket.prompt_version,
        "voter_b_checked": str(bool(review and len(review.votes) > 1)),
    }


def _reason(ticket: TicketRecord, review: ReviewRecord | None) -> str:
    if ticket.status == "discarded":
        return "checks: " + ", ".join(ticket.reasons)
    return f"judge: {review.judge_reason}" if review else "not reviewed"


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def export_dataset(
    cards_by_id: dict[str, Card], run_dir: Path, out_dir: Path
) -> dict[str, dict[str, int]]:
    """Write ``<split>.csv`` and ``<split>_quarantine.csv``; return the row counts per split."""
    accepted: dict[str, list[dict[str, str]]] = {}
    quarantine: dict[str, list[dict[str, str]]] = {}
    for split in SPLITS:
        tickets_log, reviews_log = log_paths(run_dir, split)
        tickets, reviews = read_log(tickets_log), read_reviews(reviews_log)
        good, review_of = (
            accepted_ids(tickets, reviews),
            {r.card_id: r for r in reviews},
        )
        accepted[split], quarantine[split] = [], []
        for ticket in tickets:
            card, review = cards_by_id[ticket.card_id], review_of.get(ticket.card_id)
            if ticket.card_id in good:
                accepted[split].append(_row(card, ticket, review))
            else:
                quarantine[split].append(
                    {"reason": _reason(ticket, review), **_row(card, ticket, review)}
                )
    _move_near_duplicates_of_tests(accepted, quarantine)
    for split in SPLITS:
        write_csv(out_dir / f"{split}.csv", DATASET_COLUMNS, accepted[split])
        write_csv(
            out_dir / f"{split}_quarantine.csv", QUARANTINE_COLUMNS, quarantine[split]
        )
    return {
        split: {"accepted": len(accepted[split]), "quarantine": len(quarantine[split])}
        for split in SPLITS
    }


def _move_near_duplicates_of_tests(
    accepted: dict[str, list[dict[str, str]]],
    quarantine: dict[str, list[dict[str, str]]],
) -> None:
    """A train or val ticket too close to a test ticket leaves the dataset for the quarantine."""
    test_shingles = [
        (row["card_id"], shingles(row["ticket"]))
        for split in TEST_SPLITS
        for row in accepted[split]
    ]
    for split in ("train", "val"):
        kept = []
        for row in accepted[split]:
            mine = shingles(row["ticket"])
            twin = next(
                (
                    cid
                    for cid, other in test_shingles
                    if jaccard(mine, other) >= NEAR_DUPLICATE_JACCARD
                ),
                None,
            )
            if twin:
                quarantine[split].append(
                    {"reason": f"near duplicate of test ticket {twin}", **row}
                )
            else:
                kept.append(row)
        accepted[split] = kept
