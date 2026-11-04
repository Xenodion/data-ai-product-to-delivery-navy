"""Turn a scenario card into the writing prompt of a ticket, and a written ticket into the model input.

The writer never sees a label: the situation is described in the merchant's terms and every reference or
amount is given as a string to copy verbatim. Text fragments live in ``config/prompt.toml``.
"""

import hashlib
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from src.dataset_build.cards import Card
from src.dataset_build.schema import OTHER, SUB_INTENTS, UNDEFINED

PROMPT_PATH = Path(__file__).parent / "config" / "prompt.toml"


class PromptConfig(BaseModel):
    """Validated content of ``prompt.toml``: fails fast on a missing fragment."""

    model_config = ConfigDict(extra="forbid")

    system: str
    user: str
    language: dict[str, str]
    channel: dict[str, str]
    length: dict[str, str]
    persona: dict[str, str]
    sector: dict[str, str]
    subject_mode: dict[str, str]
    area: dict[str, str]
    situation: dict[str, str]
    sub_case: dict[str, str]
    unlisted: dict[str, list[str]]
    sentinel: dict[str, str]
    reference: dict[str, str]
    amount: dict[str, str]
    semantic: dict[str, str]
    noise: dict[str, str]


def load_prompt_config(path: Path = PROMPT_PATH) -> PromptConfig:
    with path.open("rb") as handle:
        return PromptConfig.model_validate(tomllib.load(handle))


def render_prompt(card: Card, config: PromptConfig) -> tuple[str, str]:
    """Return the (system, user) messages that make a model write the ticket of ``card``."""
    user = config.user.format(
        language=config.language[card.language],
        channel=config.channel[card.channel],
        length=config.length[card.length],
        persona=config.persona[card.persona],
        sector=config.sector[card.sector],
        subject=config.subject_mode[card.subject_mode],
        situation=_situation(card, config),
        urgency_cue=card.urgency_cue,
        sentiment_cue=card.sentiment_cue,
        reference=_reference(card, config),
        amount=_amount(card, config),
        extras=_extras(card, config),
    )
    return config.system, user


def format_ticket(subject: str, body: str) -> str:
    """Model input: the subject line (when there is one), a blank line, then the body."""
    return f"Subject: {subject}\n\n{body}" if subject.strip() else body


def _situation(card: Card, config: PromptConfig) -> str:
    label = card.label
    if card.competing_requests:
        first, second = (
            _describe(request, config) for request in card.competing_requests
        )
        return config.sentinel["two_equal_requests"].format(a=first, b=second)
    if card.sentinel_kind:
        return config.sentinel[card.sentinel_kind]
    if label.sub_intent in (OTHER, UNDEFINED):
        kinds = [config.situation[sub] for sub in SUB_INTENTS[label.intent]]
        area = config.area[label.intent]
        digest = int(hashlib.sha256(card.card_id.encode()).hexdigest(), 16)
        if label.sub_intent == OTHER:
            example = config.unlisted[label.intent][
                digest % len(config.unlisted[label.intent])
            ]
            return config.sub_case["sub_other"].format(
                area=area, example=example, all="; ".join(kinds)
            )
        first = digest % len(kinds)
        second = (first + 1 + (digest // len(kinds)) % (len(kinds) - 1)) % len(kinds)
        return config.sub_case["sub_undefined"].format(
            area=area, a=kinds[first], b=kinds[second]
        )
    return config.situation[label.sub_intent]


def _describe(request: str, config: PromptConfig) -> str:
    return config.situation[request.split("/")[1]]


def _reference(card: Card, config: PromptConfig) -> str:
    return config.reference[card.id_case].format(
        id=card.id_surface, id2=card.id_second_surface
    )


def _amount(card: Card, config: PromptConfig) -> str:
    if card.currency_only:
        return config.amount["currency_only"].format(currency=card.currency_only)
    line = config.amount[card.amount_case].format(
        amount=card.amount_surface, amount2=card.amount_second_surface
    )
    if "currency_missing" in card.traps:
        line += config.amount["no_currency_note"]
    return line


def _extras(card: Card, config: PromptConfig) -> str:
    lines = [config.semantic[trap] for trap in card.traps if config.semantic.get(trap)]
    lines += [config.noise[noise] for noise in card.noise]
    return "\n".join(f"Also: {line}" for line in lines)
