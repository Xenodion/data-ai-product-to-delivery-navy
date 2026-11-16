"""Pure intake contract checks for tickets and conversation turns (node 1)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from flow.contracts import Ticket

IntakeStatus = Literal["accepted", "replay", "rejected"]


class IntakeDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: IntakeStatus
    idempotency_key: tuple[str, int]
    reason_code: str


def check_turn_sequence(ticket: Ticket, latest_turn: int | None) -> IntakeDecision:
    """Accept only turn 1 for a new conversation or the next sequential turn.

    A repeated key is returned as ``replay`` for the persistence layer to serve
    the original result after confirming its request fingerprint. This function
    never writes state and never treats a conflicting replay as a new ticket.
    """
    key = (ticket.ticket_id, ticket.turn)
    if latest_turn is None:
        if ticket.turn == 1:
            return IntakeDecision(status="accepted", idempotency_key=key, reason_code="NEW_TICKET")
        return IntakeDecision(status="rejected", idempotency_key=key, reason_code="TURN_NOT_NEXT")

    if latest_turn < 1:
        raise ValueError("latest_turn must be positive when provided")
    if ticket.turn == latest_turn:
        return IntakeDecision(status="replay", idempotency_key=key, reason_code="IDEMPOTENT_REPLAY")
    if ticket.turn == latest_turn + 1:
        return IntakeDecision(status="accepted", idempotency_key=key, reason_code="NEXT_TURN")
    return IntakeDecision(status="rejected", idempotency_key=key, reason_code="TURN_NOT_NEXT")
