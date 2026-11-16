"""Mapping from the Qualifier desks to the desks stored in the world database."""

from ml.qualifier.src.dataset_build.schema import TicketLabel
from ml.qualifier.src.scoring import desk_of

OUTCOME_DESKS = ("payments", "disputes", "technical_api", "compliance", "triage")
_DESK_NAMES = {"technical": "technical_api"}


def outcome_desk(label: TicketLabel) -> str:
    """Desk of a label as stored in ``ticket_outcomes``; tickets no desk can take go to ``triage``."""
    desk = desk_of(label)
    return _DESK_NAMES.get(desk, desk)
