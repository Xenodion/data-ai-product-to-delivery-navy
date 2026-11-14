"""Conversation-turn policy shared by intake, routing and context planning."""


def is_within_automated_turn_limit(turn: int, maximum: int = 3) -> bool:
    """The fourth merchant turn and later go to the Re-router before automation."""
    if turn < 1:
        raise ValueError("turn must be a positive integer")
    if maximum < 1:
        raise ValueError("maximum automated turns must be positive")
    return turn <= maximum
