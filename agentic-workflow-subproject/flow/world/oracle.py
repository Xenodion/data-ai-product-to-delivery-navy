"""Export of the evaluation oracle: the deck annotation of the ``current`` tickets.

Nothing that serves the flow may import this module; a test enforces it.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from flow.world.deck import DeckTicket
from flow.world.desks import outcome_desk
from flow.world.sampling import SelectedTicket

ORACLE_FILE = "current_oracle.json"


def export_oracle(
    selected: Sequence[SelectedTicket], deck: Mapping[str, DeckTicket], directory: Path
) -> Path:
    """Write label and desk of every ``current`` ticket, sorted by identifier."""
    entries = [
        {
            "ticket_id": ticket.card_id,
            "desk": outcome_desk(deck[ticket.card_id].label),
            "label": deck[ticket.card_id].label.model_dump(),
        }
        for ticket in sorted(selected, key=lambda item: item.card_id)
        if ticket.role == "current"
    ]
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / ORACLE_FILE
    payload = json.dumps(entries, indent=2, ensure_ascii=False, sort_keys=True)
    target.write_text(payload + "\n", encoding="utf-8", newline="\n")
    return target
