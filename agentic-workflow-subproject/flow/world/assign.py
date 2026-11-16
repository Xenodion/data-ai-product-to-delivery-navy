"""Deal the sampled tickets to merchants, sector by sector, with a long tail of ticket counts."""

from collections import defaultdict
from collections.abc import Mapping, Sequence

from flow.world.config import WorldConfig
from flow.world.deck import DeckTicket
from flow.world.errors import AttributionError
from flow.world.rng import stage_rng
from flow.world.sampling import SelectedTicket


def merchants_per_sector(counts: Mapping[str, int], target: int) -> dict[str, int]:
    """Share ``target`` merchants between sectors in proportion to their tickets.

    Largest-remainder rounding; every sector gets at least one merchant and never more merchants
    than tickets.

    Raises:
        AttributionError: the target is smaller than the number of sectors.
    """
    if target < len(counts):
        raise AttributionError(f"merchant_target {target} is below the {len(counts)} sectors")
    total = sum(counts.values())
    exact = {sector: target * n / total for sector, n in counts.items()}
    shares = {sector: max(1, int(value)) for sector, value in exact.items()}
    by_remainder = sorted(exact, key=lambda s: (exact[s] - int(exact[s]), s), reverse=True)
    while sum(shares.values()) < target:
        grown = next((s for s in by_remainder if shares[s] < counts[s]), None)
        if grown is None:
            break
        shares[grown] += 1
        by_remainder.remove(grown)
        by_remainder.append(grown)
    while sum(shares.values()) > target:
        shrunk = max((s for s in shares if shares[s] > 1), key=lambda s: shares[s])
        shares[shrunk] -= 1
    return {sector: min(share, counts[sector]) for sector, share in shares.items()}


def assign_tickets(
    selected: Sequence[SelectedTicket], deck: Mapping[str, DeckTicket], config: WorldConfig
) -> dict[str, str]:
    """Return ``card_id -> merchant_id`` for every sampled ticket.

    Merchants are numbered ``M-0001`` upward, sector by sector. Each merchant first receives one
    ticket, then the others are dealt by Pareto weights, so a few merchants hold many tickets.
    """
    by_sector: dict[str, list[str]] = defaultdict(list)
    for ticket in sorted(selected, key=lambda item: item.card_id):
        by_sector[deck[ticket.card_id].sector].append(ticket.card_id)
    shares = merchants_per_sector(
        {sector: len(ids) for sector, ids in by_sector.items()}, config.merchant_target
    )
    rng = stage_rng(config.seed, "assign")
    assignment: dict[str, str] = {}
    number = 0
    for sector in sorted(by_sector):
        ids = by_sector[sector]
        rng.shuffle(ids)
        merchant_ids = [f"M-{number + index + 1:04d}" for index in range(shares[sector])]
        number += shares[sector]
        weights = [rng.paretovariate(config.merchants.ticket_count_alpha) for _ in merchant_ids]
        for merchant_id, card_id in zip(merchant_ids, ids, strict=False):
            assignment[card_id] = merchant_id
        for card_id in ids[len(merchant_ids) :]:
            assignment[card_id] = rng.choices(merchant_ids, weights)[0]
    return assignment
