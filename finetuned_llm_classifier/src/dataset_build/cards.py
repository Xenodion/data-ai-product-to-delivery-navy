"""Scenario cards: a seeded sampler whose cards fully determine the label of a synthetic ticket.

A card holds (1) the label, derived by rule from the sampled variables, (2) the surface forms the ticket text
must contain (how the reference and the amount are written, lookalike distractors), (3) style variables that
only steer the writer and stay in the dataset metadata. The LLM that writes the ticket never decides the label.
Weights and values live in ``config/cards.toml``; trap definitions: ``specs/001-dataset-build`` and
``docs/label_definitions.md``.
"""

import math
import random
import tomllib
from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from src.dataset_build.schema import OTHER, SUB_INTENTS, UNDEFINED, TicketLabel

CONFIG_PATH = Path(__file__).parent / "config" / "cards.toml"
MAX_QUOTA_ATTEMPTS = 50_000

# Sentinel kinds that carry no reference and no amount, and (for the first two) no readable urgency or tone.
NO_FIELD_KINDS = frozenset(
    {"too_vague", "unintelligible", "truncated", "thanks_only", "spam"}
)
UNREADABLE_KINDS = frozenset({"too_vague", "unintelligible"})
SHORT_KINDS = frozenset({"too_vague", "truncated", "unintelligible", "thanks_only"})
LONG_FORM_NOISE = frozenset({"signature", "disclaimer", "quoted_thread"})
CASE_NEEDS_REAL_INTENT = frozenset(
    {"thanks_hiding_problem", "furious_not_urgent", "polite_but_urgent"}
)
ID_NON_TRAPS = frozenset({"canonical", "none"})


class Profile(BaseModel):
    trap_boost: float = 1.0
    quota: dict[str, int] = {}


class CardsConfig(BaseModel):
    """Validated content of ``cards.toml`` (fails fast on a typo or a missing table)."""

    model_config = ConfigDict(extra="forbid")

    splits: dict[str, int]
    profiles: dict[str, Profile]
    intent: dict[str, float]
    sub_case: dict[str, float]
    other_kind: dict[str, float]
    undefined_kind: dict[str, float]
    problem_sub_intents: list[str]
    always_high_sub_intents: list[str]
    urgency_problem: dict[str, float]
    urgency_info: dict[str, float]
    urgency_other: dict[str, float]
    sentiment: dict[str, float]
    cues: dict[str, dict[str, list[str]]]
    presence: dict[str, dict[str, float]]
    id_present: dict[str, float]
    id_absent: dict[str, float]
    id_templates: dict[str, list[str] | str]
    amount_min: float
    amount_max: float
    amount_case: dict[str, float]
    amount_format: dict[str, float]
    currency: dict[str, float]
    currency_case: dict[str, float]
    currency_names: dict[str, dict[str, str]]
    semantic: dict[str, float]
    language: dict[str, float]
    other_language: dict[str, float]
    channel: dict[str, float]
    length: dict[str, float]
    persona: dict[str, float]
    sector: dict[str, float]
    subject_mode: dict[str, float]
    noise_count: dict[str, float]
    noise: dict[str, float]


class Card(BaseModel):
    """One scenario: the target label plus everything the writer needs to realise it in a ticket."""

    model_config = ConfigDict(frozen=True)

    card_id: str
    label: TicketLabel
    traps: tuple[str, ...]
    sentinel_kind: str  # why the intent is OTHER or UNDEFINED, "" otherwise
    competing_requests: tuple[
        str, ...
    ]  # "intent/sub_intent" of the two equal requests, else ()
    urgency_cue: str
    sentiment_cue: str
    id_case: str
    id_surface: str  # text to embed for the reference, even when it is not a valid one (lookalike, malformed); may hold a line break
    id_second_surface: str  # a second reference or a lookalike distractor, "" if none
    id_location: str  # body, subject, quoted
    amount_case: str
    amount_surface: str  # amount with its currency as written, "" if none
    amount_second_surface: str
    currency_only: str  # a currency code mentioned without any amount, "" if none
    language: str
    channel: str
    length: str
    persona: str
    sector: str
    subject_mode: str
    noise: tuple[str, ...]

    @property
    def tags(self) -> frozenset[str]:
        """Searchable properties, used by the quotas of a profile."""
        tags = {f"trap:{trap}" for trap in self.traps}
        tags |= {f"intent:{self.label.intent}", f"lang:{self.language}"}
        if self.sentinel_kind:
            tags.add(f"sentinel:{self.sentinel_kind}")
        return frozenset(tags)


def load_config(path: Path = CONFIG_PATH) -> CardsConfig:
    with path.open("rb") as handle:
        return CardsConfig.model_validate(tomllib.load(handle))


def draw_cards(config: CardsConfig, profile: str, n: int, seed: int) -> list[Card]:
    """Draw ``n`` cards: first enough cards to meet the profile quotas, then free draws. Same seed, same cards."""
    rng = random.Random(seed)
    settings = config.profiles[profile]
    cards: list[Card] = []
    for tag, minimum in settings.quota.items():
        attempts = 0
        while sum(tag in card.tags for card in cards) < minimum:
            attempts += 1
            if attempts > MAX_QUOTA_ATTEMPTS:
                raise ValueError(f"tag {tag!r} is unreachable with this config")
            card = _draw_card(rng, config, settings.trap_boost)
            if tag in card.tags:
                cards.append(card)
    if len(cards) > n:
        raise ValueError(
            f"the quotas of profile {profile!r} need {len(cards)} cards, more than n={n}"
        )
    while len(cards) < n:
        cards.append(_draw_card(rng, config, settings.trap_boost))
    rng.shuffle(cards)
    return [
        card.model_copy(update={"card_id": f"{profile}-{seed}-{i:05d}"})
        for i, card in enumerate(cards)
    ]


def _pick(rng: random.Random, weights: Mapping[str, float]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def _boosted(
    weights: Mapping[str, float], trap_keys: set[str], boost: float
) -> dict[str, float]:
    return {key: w * boost if key in trap_keys else w for key, w in weights.items()}


def _digits(rng: random.Random, count: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(count))


def _fill(rng: random.Random, template: str) -> str:
    return "".join(
        rng.choice("0123456789") if char == "#" else char for char in template
    )


def _draw_card(rng: random.Random, config: CardsConfig, boost: float) -> Card:
    traps: list[str] = []
    semantic = _pick(
        rng, _boosted(config.semantic, set(config.semantic) - {"none"}, boost)
    )

    # intent, sub-intent and the reason behind a sentinel
    intent = _pick(rng, config.intent)
    sentinel_kind = ""
    competing: tuple[str, ...] = ()
    if intent == OTHER:
        sub_intent, sentinel_kind = OTHER, _pick(rng, config.other_kind)
    elif intent == UNDEFINED:
        sub_intent, sentinel_kind = UNDEFINED, _pick(rng, config.undefined_kind)
        if sentinel_kind == "two_equal_requests":
            competing = tuple(
                f"{name}/{rng.choice(SUB_INTENTS[name])}"
                for name in rng.sample(list(SUB_INTENTS), 2)
            )
    else:
        sub_case = _pick(rng, config.sub_case)
        sub_intent = {"sub_other": OTHER, "sub_undefined": UNDEFINED}.get(
            sub_case
        ) or rng.choice(SUB_INTENTS[intent])
    if semantic in CASE_NEEDS_REAL_INTENT and intent in (OTHER, UNDEFINED):
        semantic = "none"
    if (
        semantic == "furious_not_urgent"
        and sub_intent in config.always_high_sub_intents
    ):
        semantic = "none"  # a frozen account is urgent whatever the tone

    # urgency and sentiment, then the semantic traps that override them
    is_problem = intent == UNDEFINED or sub_intent in config.problem_sub_intents
    if intent == OTHER:
        urgency = _pick(rng, config.urgency_other)
    elif sub_intent in config.always_high_sub_intents:
        urgency = "high"
    else:
        urgency = _pick(
            rng, config.urgency_problem if is_problem else config.urgency_info
        )
    sentiment = _pick(rng, config.sentiment)
    if sentinel_kind == "unintelligible":
        urgency = sentiment = UNDEFINED
    elif sentinel_kind == "too_vague":
        urgency, sentiment = (
            UNDEFINED,
            "neutral" if sentiment == "positive" else sentiment,
        )
    elif sentinel_kind == "thanks_only":
        sentiment, urgency = "positive", "low"
    elif semantic == "thanks_hiding_problem":
        sentiment = "positive"
    elif semantic == "furious_not_urgent":
        sentiment, urgency = "negative", "medium" if is_problem else "low"
    elif semantic == "polite_but_urgent":
        sentiment, urgency = "neutral", "high"
    if semantic != "none":
        traps.append(semantic)

    # transaction reference
    presence = config.presence.get(sub_intent, config.presence["default"])
    has_fields = sentinel_kind not in NO_FIELD_KINDS
    has_id = (
        has_fields
        and intent != OTHER
        and rng.random() < presence.get("id", config.presence["default"]["id"])
    )
    id_label, id_case, id_surface, id_second, id_location = _draw_reference(
        rng, config, has_id, has_fields and intent != OTHER, boost
    )
    if id_case not in ID_NON_TRAPS:
        traps.append(f"id_{id_case}")

    # amount and currency
    has_amount = (
        has_fields
        and intent != OTHER
        and rng.random() < presence.get("amount", config.presence["default"]["amount"])
    )
    currency_only = ""
    if (
        has_fields
        and intent != OTHER
        and not has_amount
        and rng.random() < config.presence["default"]["currency_only"]
    ):
        currency_only = _pick(rng, config.currency)
    language = (
        _pick(rng, config.other_language)
        if semantic == "other_language"
        else _pick(rng, config.language)
    )
    amount = _draw_amount(
        rng,
        config,
        language,
        has_amount,
        currency_only,
        boost,
        single_amount=id_case in ("two_main", "two_equal"),
    )
    traps.extend(amount.traps)

    # style
    channel = _pick(rng, config.channel)
    subject_mode = _pick(rng, config.subject_mode)
    noise = _draw_noise(rng, config)
    if id_case == "subject_only":
        channel, subject_mode = "formal_email", "present"
    elif id_case == "quoted_only":
        channel = "forwarded_thread"
        noise = tuple(dict.fromkeys((*noise, "quoted_thread")))
    elif channel == "chat_message":
        subject_mode = "absent"
    length = _pick(rng, config.length)
    # Coherence constraints: a message with no readable tone or urgency, or no clear request, is short;
    # a chat message has no signature, disclaimer or quoted thread.
    if sentinel_kind in SHORT_KINDS or UNDEFINED in (urgency, sentiment):
        length = "short"
        channel = (
            "short_email"
            if channel == "forwarded_thread" and id_case != "quoted_only"
            else channel
        )
    if channel == "chat_message":
        noise = tuple(item for item in noise if item not in LONG_FORM_NOISE)
    if semantic == "other_language":
        noise = tuple(item for item in noise if item != "fr_en_mix")
    if semantic == "prompt_injection":
        noise = (*noise, "injection")

    label = TicketLabel(
        intent=intent,
        sub_intent=sub_intent,
        transaction_id=id_label,
        amount=amount.label_amount,
        currency=amount.label_currency,
        urgency=urgency,
        sentiment=sentiment,
    )
    return Card(
        card_id="",
        label=label,
        traps=tuple(traps),
        sentinel_kind=sentinel_kind,
        competing_requests=competing,
        urgency_cue=rng.choice(config.cues["urgency"][urgency]),
        sentiment_cue=rng.choice(config.cues["sentiment"][sentiment]),
        id_case=id_case,
        id_surface=id_surface,
        id_second_surface=id_second,
        id_location=id_location,
        amount_case=amount.case,
        amount_surface=amount.surface,
        amount_second_surface=amount.second_surface,
        currency_only=currency_only,
        language=language,
        channel=channel,
        length=length,
        persona=_pick(rng, config.persona),
        sector=_pick(rng, config.sector),
        subject_mode=subject_mode,
        noise=noise,
    )


def _draw_noise(rng: random.Random, config: CardsConfig) -> tuple[str, ...]:
    count = int(_pick(rng, config.noise_count))
    pool = dict(config.noise)
    chosen: list[str] = []
    for _ in range(count):
        item = _pick(rng, pool)
        chosen.append(item)
        del pool[item]
    return tuple(chosen)


def _draw_reference(
    rng: random.Random,
    config: CardsConfig,
    has_id: bool,
    has_fields: bool,
    boost: float,
) -> tuple[str, str, str, str, str]:
    """Return (label, case, surface, second surface, location) for the transaction reference."""
    if not has_fields:
        return "", "none", "", "", "body"
    templates = config.id_templates
    if has_id:
        case = _pick(
            rng,
            _boosted(config.id_present, set(config.id_present) - ID_NON_TRAPS, boost),
        )
        digits = _digits(rng, 6)
        canonical = f"TX-{digits}"
        surface = {
            "spaced": f"TX {digits[:3]} {digits[3:]}",
            "nohyphen": f"TX{digits}",
            "lowercase": f"tx-{digits}",
            "split_lines": f"TX-{digits[:3]}\n{digits[3:]}",
            "bare_with_intro": digits,
        }.get(case, canonical)
        location = {"subject_only": "subject", "quoted_only": "quoted"}.get(
            case, "body"
        )
        if case in ("two_main", "two_equal"):
            return (
                (canonical if case == "two_main" else UNDEFINED),
                case,
                canonical,
                f"TX-{_digits(rng, 6)}",
                location,
            )
        return canonical, case, surface, "", location
    case = _pick(
        rng, _boosted(config.id_absent, set(config.id_absent) - ID_NON_TRAPS, boost)
    )
    if case == "none":
        return "", case, "", "", "body"
    if case == "bare_no_intro":
        return (
            "",
            case,
            _fill(rng, str(templates["bare"])),
            "",
            "body",
        )
    template = rng.choice(templates[case])
    return (
        (UNDEFINED if case == "malformed" else ""),
        case,
        _fill(rng, template),
        "",
        "body",
    )


class _Amount(BaseModel):
    case: str
    label_amount: str
    label_currency: str
    surface: str
    second_surface: str
    traps: tuple[str, ...]


def _draw_amount(
    rng: random.Random,
    config: CardsConfig,
    language: str,
    has_amount: bool,
    currency_only: str,
    boost: float,
    single_amount: bool = False,
) -> _Amount:
    if not has_amount:
        return _Amount(
            case="none",
            label_amount="",
            label_currency=currency_only,
            surface="",
            second_surface="",
            traps=(),
        )
    case = _pick(
        rng, _boosted(config.amount_case, set(config.amount_case) - {"plain"}, boost)
    )
    if single_amount and case in ("two_main", "two_equal"):
        case = (
            "plain"  # amounts tied to two references would make the main one ambiguous
        )
    value = _random_value(rng, config)
    if case == "k_suffix":
        value = max(
            Decimal(1000), (value / 100).quantize(Decimal(1), ROUND_HALF_UP) * 100
        )
    code = _pick(rng, config.currency)
    currency_case = _pick(
        rng, _boosted(config.currency_case, {"lone_dollar", "none"}, boost)
    )
    if currency_case == "symbol" and code not in ("EUR", "GBP"):
        currency_case = "lone_dollar" if code == "USD" else "code"
    fmt = _pick(rng, config.amount_format)
    style = _number_style(language, fmt)

    def write(amount: Decimal) -> str:
        number = _format_number(
            amount, style, k_suffix=(case == "k_suffix"), keep_cents=rng.random() < 0.6
        )
        return _attach_currency(
            number, code, currency_case, language, config.currency_names
        )

    surface = write(value)
    second = (
        write(_random_value(rng, config)) if case in ("two_main", "two_equal") else ""
    )
    label_currency = {"lone_dollar": UNDEFINED, "none": ""}.get(currency_case, code)
    traps = [f"amount_{case}"] if case != "plain" else []
    if currency_case == "lone_dollar":
        traps.append("currency_lone_dollar")
    elif currency_case == "none":
        traps.append("currency_missing")
    return _Amount(
        case=case,
        label_amount=UNDEFINED if case == "two_equal" else f"{value:.2f}",
        label_currency=label_currency,
        surface=surface,
        second_surface=second,
        traps=tuple(traps),
    )


def _random_value(rng: random.Random, config: CardsConfig) -> Decimal:
    raw = math.exp(
        rng.uniform(math.log(config.amount_min), math.log(config.amount_max))
    )
    whole = Decimal(round(raw))
    cents = Decimal(rng.choice((0, 0, 0, 50, 99, 90, 20))) / 100
    return (whole + cents).quantize(Decimal("0.01"))


def _number_style(language: str, fmt: str) -> str:
    local = "fr" if language == "fr" else "en"
    other = "en" if local == "fr" else "fr"
    return {"local": local, "other": other, "plain": "plain"}[fmt]


def _format_number(
    amount: Decimal, style: str, k_suffix: bool, keep_cents: bool
) -> str:
    if k_suffix:
        return f"{amount / 1000:g}k"
    whole, cents = f"{amount:.2f}".split(".")
    show_cents = cents != "00" or keep_cents
    if style == "plain":
        return f"{whole}.{cents}" if show_cents else whole
    grouped = f"{int(whole):,}"
    if style == "fr":
        grouped = grouped.replace(",", " ")
        return f"{grouped},{cents}" if show_cents else grouped
    return f"{grouped}.{cents}" if show_cents else grouped


def _attach_currency(
    number: str,
    code: str,
    case: str,
    language: str,
    names: Mapping[str, Mapping[str, str]],
) -> str:
    if case == "none":
        return number
    if case == "lone_dollar":
        return f"{number} $" if language == "fr" else f"${number}"
    if case == "symbol":
        symbol = "€" if code == "EUR" else "£"
        return (
            f"{number} {symbol}"
            if language == "fr" and code == "EUR"
            else f"{symbol}{number}"
        )
    if case == "name":
        return f"{number} {names['fr' if language == 'fr' else 'en'][code]}"
    return f"{number} {code}"


def trap_rate(cards: Sequence[Card]) -> float:
    """Share of cards that carry at least one trap."""
    return sum(bool(card.traps) for card in cards) / len(cards)
