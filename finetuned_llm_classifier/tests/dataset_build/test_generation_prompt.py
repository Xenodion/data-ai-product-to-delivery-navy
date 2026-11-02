import re

from src.dataset_build.cards import draw_cards, load_config
from src.dataset_build.generation_prompt import (
    format_ticket,
    load_prompt_config,
    render_prompt,
)
from src.dataset_build.schema import SUB_INTENTS

CARDS = load_config()
PROMPTS = load_prompt_config()
SAMPLE = draw_cards(CARDS, "train", 3000, seed=9)
LABEL_NAMES = {sub for subs in SUB_INTENTS.values() for sub in subs if "_" in sub} | {
    i for i in SUB_INTENTS if "_" in i
}


def test_render_prompt_covers_every_card_and_copies_surface_forms_verbatim():
    for card in SAMPLE:
        _, user = render_prompt(card, PROMPTS)
        for surface in (
            card.id_surface,
            card.id_second_surface,
            card.amount_surface,
            card.amount_second_surface,
        ):
            assert surface in user, (card.card_id, surface)


def test_render_prompt_never_leaks_a_label_name():
    for card in SAMPLE:
        system, user = render_prompt(card, PROMPTS)
        assert not re.search(r"\b(UNDEFINED|OTHER)\b", system + user), card.card_id
        assert not any(name in system + user for name in LABEL_NAMES), card.card_id


def test_render_prompt_shows_both_requests_of_a_two_request_card():
    card = next(c for c in SAMPLE if c.sentinel_kind == "two_equal_requests")
    _, user = render_prompt(card, PROMPTS)
    assert "First request" in user and "Second request" in user


def test_format_ticket_omits_an_empty_subject():
    assert format_ticket("Hello", "Body") == "Subject: Hello\n\nBody"
    assert format_ticket("  ", "Body") == "Body"


def test_render_prompt_gives_a_concrete_unlisted_example_for_sub_other_and_two_kinds_for_sub_undefined():
    other = next(
        c
        for c in SAMPLE
        if c.label.intent in SUB_INTENTS and c.label.sub_intent == "OTHER"
    )
    undefined = next(
        c
        for c in SAMPLE
        if c.label.intent in SUB_INTENTS and c.label.sub_intent == "UNDEFINED"
    )
    assert any(
        example in render_prompt(other, PROMPTS)[1]
        for example in PROMPTS.unlisted[other.label.intent]
    )
    assert (
        "First kind:" in render_prompt(undefined, PROMPTS)[1]
        and "Second kind:" in render_prompt(undefined, PROMPTS)[1]
    )


def test_render_prompt_forbids_any_currency_when_the_card_has_none():
    card = next(c for c in SAMPLE if "currency_missing" in c.traps)
    assert "no currency symbol" in render_prompt(card, PROMPTS)[1]
