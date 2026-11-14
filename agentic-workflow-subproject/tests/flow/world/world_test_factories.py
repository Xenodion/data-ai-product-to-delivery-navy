"""Micro-deck builders for the world tests; nothing here reads the real deck."""

import csv
import json
from pathlib import Path

HEADER = (
    "card_id", "ticket", "target", "traps", "language", "channel", "length", "persona", "sector",
    "noise", "sentinel_kind", "id_case", "amount_case", "writer_model", "prompt_version",
    "voter_b_checked",
)  # fmt: skip
DEFAULT_TARGET = {
    "intent": "payment_status",
    "sub_intent": "status_inquiry",
    "transaction_id": "TX-123456",
    "amount": "100.00",
    "currency": "EUR",
    "urgency": "medium",
    "sentiment": "neutral",
}
SECTORS = ("retail", "saas", "travel")
LANGUAGES = ("fr", "en")
SUB_INTENTS = (
    ("payment_status", "status_inquiry"),
    ("dispute", "chargeback"),
    ("technical_api", "api_error"),
    ("compliance", "kyc_update"),
)
ID_CASES = ("canonical", "spaced", "none", "lookalike")


def make_row(card_id: str, text: str = "Where is TX-123456?", **overrides: str) -> dict[str, str]:
    """Build one deck row; ``target`` accepts a dict override."""
    row = {
        "card_id": card_id,
        "ticket": text,
        "target": json.dumps(DEFAULT_TARGET),
        "traps": "",
        "language": "fr",
        "channel": "formal_email",
        "length": "short",
        "persona": "founder",
        "sector": "retail",
        "noise": "",
        "sentinel_kind": "",
        "id_case": "canonical",
        "amount_case": "plain",
        "writer_model": "stub",
        "prompt_version": "v0",
        "voter_b_checked": "False",
    }
    row.update(overrides)
    return row


def write_split_file(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


def micro_rows(split: str, count: int) -> list[dict[str, str]]:
    """Deterministic rows cycling through sectors, languages, desks and id cases."""
    rows = []
    for index in range(count):
        intent, sub_intent = SUB_INTENTS[index % len(SUB_INTENTS)]
        target = DEFAULT_TARGET | {"intent": intent, "sub_intent": sub_intent}
        rows.append(
            make_row(
                f"{split}-{index:03d}",
                f"Ticket {split} {index} about TX-{100000 + index}",
                target=json.dumps(target),
                sector=SECTORS[index % len(SECTORS)],
                language=LANGUAGES[(index // 2) % len(LANGUAGES)],
                id_case=ID_CASES[index % len(ID_CASES)],
            )
        )
    return rows
