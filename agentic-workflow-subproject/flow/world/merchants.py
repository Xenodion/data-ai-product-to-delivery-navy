"""Merchants, their currencies and contacts, derived from the tickets dealt to them."""

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from flow.world.config import WorldConfig
from flow.world.deck import DeckTicket
from flow.world.models import Contact, Merchant, MerchantCurrency
from flow.world.rng import stage_rng
from flow.world.sampling import SelectedTicket

DEFAULT_CURRENCY = "EUR"
TIERS = ("small", "medium", "large")


class MerchantBook:
    """The merchant rows built from one assignment, plus the contact lookup."""

    def __init__(
        self,
        merchants: tuple[Merchant, ...],
        currencies: tuple[MerchantCurrency, ...],
        contacts: tuple[Contact, ...],
    ) -> None:
        self.merchants = merchants
        self.currencies = currencies
        self.contacts = contacts
        self._contact_ids = {(c.merchant_id, c.persona, c.language): c.contact_id for c in contacts}

    def contact_id(self, merchant_id: str, persona: str, language: str) -> str:
        """Contact of a merchant for a persona and language (every ticket has one)."""
        return self._contact_ids[(merchant_id, persona, language)]


def amount_in_eur(ticket: DeckTicket, config: WorldConfig) -> Decimal | None:
    """Annotated amount converted to EUR, or None without a usable amount and currency."""
    rate = config.fx_to_eur.get(ticket.label.currency)
    if not ticket.label.amount or rate is None:
        return None
    try:
        return Decimal(ticket.label.amount) * Decimal(str(rate))
    except InvalidOperation:
        return None


def _tercile_edges(values: Sequence[Decimal]) -> tuple[Decimal, Decimal]:
    ordered = sorted(values)
    return ordered[len(ordered) // 3], ordered[2 * len(ordered) // 3]


def _most_common(values: Sequence[str], fallback: str) -> str:
    if not values:
        return fallback
    counts = Counter(values)
    return min(counts, key=lambda value: (-counts[value], value))


def build_merchants(
    assignment: Mapping[str, str],
    deck: Mapping[str, DeckTicket],
    selected: Mapping[str, SelectedTicket],
    config: WorldConfig,
) -> MerchantBook:
    """Build every merchant from the tickets it received.

    Volume tier is the tercile of the merchant's largest EUR amount among merchants that have
    one; the others draw from the configured weights. Onboarding precedes the earliest complete
    date cited by the merchant's tickets and the start of the window.
    """
    settings = config.merchants
    tickets: dict[str, list[str]] = defaultdict(list)
    for card_id, merchant_id in sorted(assignment.items()):
        tickets[merchant_id].append(card_id)
    largest: dict[str, Decimal] = {}
    for merchant_id, ids in tickets.items():
        amounts = [a for i in ids if (a := amount_in_eur(deck[i], config)) is not None]
        if amounts:
            largest[merchant_id] = max(amounts)
    low, high = _tercile_edges(list(largest.values())) if largest else (Decimal(0), Decimal(0))
    names = _names(len(tickets), config)
    merchants, currencies, contacts = [], [], []
    for position, merchant_id in enumerate(sorted(tickets)):
        ids = tickets[merchant_id]
        rng = stage_rng(config.seed, f"merchant:{merchant_id}")
        if merchant_id in largest:
            tier = (
                "small"
                if largest[merchant_id] < low
                else "large"
                if largest[merchant_id] >= high
                else "medium"
            )
        else:
            weights = settings.tier_weights_without_amount
            tier = rng.choices(TIERS, [weights[t] for t in TIERS])[0]
        held = sorted({c for i in ids if (c := deck[i].label.currency) in config.fx_to_eur})
        settlement = _most_common(
            [c for i in ids if (c := deck[i].label.currency) in config.fx_to_eur], DEFAULT_CURRENCY
        )
        language = _most_common([deck[i].language for i in ids], "en")
        cited = [d for i in ids if (d := selected[i].earliest_full_date) is not None]
        anchor = min([config.window_start, *cited])
        plan = settings.plans[tier]
        merchants.append(
            Merchant(
                merchant_id=merchant_id,
                name=names[position],
                sector=deck[ids[0]].sector,
                preferred_language=language,
                country=settings.country_by_language.get(language, "FR"),
                settlement_currency=settlement,
                volume_tier=tier,
                plan=plan.name,
                fee_bps=plan.fee_bps,
                kyc_status=rng.choices(
                    list(settings.kyc_weights), list(settings.kyc_weights.values())
                )[0],
                risk_level=rng.choices(
                    list(settings.risk_weights), list(settings.risk_weights.values())
                )[0],
                onboarded_at=anchor - timedelta(days=rng.randint(*settings.onboarding_days_before)),
            )
        )
        currencies.extend(
            MerchantCurrency(merchant_id=merchant_id, currency=c) for c in {*held, settlement}
        )
        pairs = sorted({(deck[i].persona, deck[i].language) for i in ids})
        contacts.extend(
            Contact(
                contact_id=f"C-{merchant_id[2:]}-{index + 1}",
                merchant_id=merchant_id,
                persona=persona,
                language=contact_language,
            )
            for index, (persona, contact_language) in enumerate(pairs)
        )
    return MerchantBook(tuple(merchants), tuple(currencies), tuple(contacts))


def _names(count: int, config: WorldConfig) -> list[str]:
    pairs = [
        f"{first} {second}"
        for first in config.merchants.name_first
        for second in config.merchants.name_second
    ]
    return stage_rng(config.seed, "merchant-names").sample(pairs, count)
