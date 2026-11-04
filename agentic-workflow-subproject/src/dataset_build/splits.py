"""Split a pool of scenario cards into train / val / test_natural / test_traps, before any text is generated.

The pool follows the natural distribution. ``test_natural`` and ``val`` are random samples of it, so aggregate
scores and cost estimates stay honest; ``test_traps`` takes a minimum of cards per trap type, to score each
trap separately. Splits are disjoint. Cards are free, so the pool is large and the unused cards are simply left out.
"""

import random
from collections import Counter

from pydantic import BaseModel, ConfigDict

from src.dataset_build.cards import Card, CardsConfig, draw_cards


class SplitSizes(BaseModel):
    model_config = ConfigDict(frozen=True)

    pool: int
    train: int
    val: int
    test_natural: int
    min_per_trap: int


def draw_pool(config: CardsConfig, sizes: SplitSizes, seed: int) -> list[Card]:
    """Draw the natural-distribution pool, dropping cards that are identical apart from their id."""
    seen: set[str] = set()
    pool: list[Card] = []
    for card in draw_cards(config, "train", sizes.pool, seed):
        key = card.model_copy(update={"card_id": ""}).model_dump_json()
        if key not in seen:
            seen.add(key)
            pool.append(card)
    return pool


def split_pool(pool: list[Card], sizes: SplitSizes, seed: int) -> dict[str, list[Card]]:
    """Return the four disjoint splits; raise if the pool cannot honour the sizes or the trap minimum."""
    rng = random.Random(seed)
    remaining = list(pool)
    rng.shuffle(remaining)

    def take(count: int) -> list[Card]:
        taken, rest = remaining[:count], remaining[count:]
        remaining[:] = rest
        return taken

    test_natural, val = take(sizes.test_natural), take(sizes.val)
    test_traps: list[Card] = []
    trap_tags = sorted({f"trap:{trap}" for card in remaining for trap in card.traps})
    for tag in trap_tags:
        missing = sizes.min_per_trap - sum(tag in card.tags for card in test_traps)
        chosen = [card for card in remaining if tag in card.tags][: max(missing, 0)]
        if (
            sum(tag in card.tags for card in test_traps) + len(chosen)
            < sizes.min_per_trap
        ):
            raise ValueError(f"pool too small for {sizes.min_per_trap} cards of {tag}")
        test_traps.extend(chosen)
        remaining[:] = [card for card in remaining if card not in chosen]
    if len(remaining) < sizes.train:
        raise ValueError(
            f"only {len(remaining)} cards left for train, need {sizes.train}"
        )
    splits = {
        "train": take(sizes.train),
        "val": val,
        "test_natural": test_natural,
        "test_traps": test_traps,
    }
    # Taking the first cards of each trap emptied the head of the list of its traps: shuffle so that any
    # prefix of a split (an incremental batch) is representative of the whole split.
    for cards in splits.values():
        rng.shuffle(cards)
    return splits


def describe(cards: list[Card]) -> dict[str, object]:
    """Distribution report of a set of cards, for the analysis step before splitting."""
    return {
        "n": len(cards),
        "trap_rate": round(
            sum(bool(card.traps) for card in cards) / max(len(cards), 1), 3
        ),
        "intent": dict(Counter(card.label.intent for card in cards)),
        "language": dict(Counter(card.language for card in cards)),
        "traps": dict(Counter(trap for card in cards for trap in card.traps)),
    }
