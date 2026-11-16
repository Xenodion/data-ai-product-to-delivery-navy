"""Typed access to the frozen ticket deck.

The builder is an offline, evaluator-side tool and may read the annotations; nothing loaded here
reaches a runtime prompt or the served database. Quarantine files hold rejected tickets and are
never opened.
"""

import csv
import json
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, ValidationError

from flow.world.errors import DeckContractError
from ml.qualifier.src.dataset_build.schema import TicketLabel

Split = Literal["train", "val", "test_natural", "test_traps"]
Language = Literal["fr", "en", "es", "de", "it"]
Channel = Literal["formal_email", "short_email", "forwarded_thread", "chat_message"]
Length = Literal["short", "medium", "long"]
Persona = Literal[
    "small_shop_owner",
    "accountant",
    "developer",
    "operations_manager",
    "founder",
    "compliance_officer",
]
Sector = Literal["retail", "saas", "marketplace", "education", "logistics", "hospitality", "travel"]
IdCase = Literal[
    "canonical", "spaced", "nohyphen", "lowercase", "lookalike", "malformed", "subject_only",
    "bare_with_intro", "bare_no_intro", "quoted_only", "two_main", "two_equal", "split_lines", "none",
]  # fmt: skip
AmountCase = Literal["plain", "approx", "k_suffix", "two_main", "two_equal", "none"]
NO_ANOMALY = "none"
SPLIT_NAMES: tuple[Split, ...] = get_args(Split)
EXPECTED_COLUMNS = frozenset(
    {
        "card_id", "ticket", "target", "traps", "language", "channel", "length", "persona",
        "sector", "noise", "sentinel_kind", "id_case", "amount_case", "writer_model",
        "prompt_version", "voter_b_checked",
    }
)  # fmt: skip
MULTI_VALUE_SEPARATOR = "|"
Newline = Literal["lf", "crlf"]


class DeckTicket(BaseModel):
    """One frozen deck ticket with its parsed annotation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    card_id: str
    split: Split
    text: str
    label: TicketLabel
    traps: tuple[str, ...]
    noise: tuple[str, ...]
    sentinel_kind: str
    language: Language
    channel: Channel
    length: Length
    persona: Persona
    sector: Sector
    id_case: IdCase
    amount_case: AmountCase

    @property
    def anomalies(self) -> tuple[str, ...]:
        """Every trap and the sentinel kind of the ticket, or ``none`` when it holds neither."""
        tags = (*self.traps, *((self.sentinel_kind,) if self.sentinel_kind else ()))
        return tags or (NO_ANOMALY,)


def normalize_newlines(text: str, newline: Newline) -> str:
    """Return the text with one line ending, so that a build does not depend on the checkout.

    Git on Windows rewrites the deck files with CRLF while the committed form (and the log the
    tickets were generated into) uses LF; the world works on the committed form by default.
    """
    unified = text.replace("\r\n", "\n")
    return unified.replace("\n", "\r\n") if newline == "crlf" else unified


def _split_values(raw: str) -> tuple[str, ...]:
    return tuple(part for part in raw.split(MULTI_VALUE_SEPARATOR) if part)


def load_split(path: Path, split: Split, newline: Newline = "lf") -> tuple[DeckTicket, ...]:
    """Load one split file.

    Raises:
        DeckContractError: the file is a quarantine file, a column is missing, a row cannot be
            parsed, or a card identifier is repeated inside the split.
    """
    if "quarantine" in path.name:
        raise DeckContractError(f"quarantine files are never read: {path.name}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        if columns != EXPECTED_COLUMNS:
            raise DeckContractError(
                f"{path.name}: missing columns {sorted(EXPECTED_COLUMNS - columns)}, "
                f"unexpected columns {sorted(columns - EXPECTED_COLUMNS)}"
            )
        tickets: list[DeckTicket] = []
        seen: set[str] = set()
        for line, row in enumerate(reader, start=2):
            card_id = row["card_id"]
            if card_id in seen:
                raise DeckContractError(f"{path.name}:{line}: duplicate card_id {card_id}")
            seen.add(card_id)
            try:
                label = TicketLabel.model_validate(json.loads(row["target"]))
                tickets.append(
                    DeckTicket(
                        card_id=card_id,
                        split=split,
                        text=normalize_newlines(row["ticket"], newline),
                        label=label,
                        traps=_split_values(row["traps"]),
                        noise=_split_values(row["noise"]),
                        sentinel_kind=row["sentinel_kind"],
                        language=row["language"],
                        channel=row["channel"],
                        length=row["length"],
                        persona=row["persona"],
                        sector=row["sector"],
                        id_case=row["id_case"],
                        amount_case=row["amount_case"],
                    )
                )
            except (json.JSONDecodeError, ValidationError) as error:
                raise DeckContractError(f"{path.name}:{line}: {card_id}: {error}") from error
    return tuple(tickets)


def load_deck(deck_dir: Path, newline: Newline = "lf") -> tuple[DeckTicket, ...]:
    """Load the four splits in a fixed order; card identifiers must be unique across splits."""
    tickets: list[DeckTicket] = []
    for split in SPLIT_NAMES:
        tickets.extend(load_split(deck_dir / f"{split}.csv", split, newline))
    ids = [ticket.card_id for ticket in tickets]
    if len(set(ids)) != len(ids):
        raise DeckContractError("card_id values must be unique across splits")
    return tuple(tickets)
