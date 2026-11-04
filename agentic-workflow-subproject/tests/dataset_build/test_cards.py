import pytest

from src.dataset_build.cards import draw_cards, load_config, trap_rate

CONFIG = load_config()


def test_draw_cards_returns_identical_cards_for_the_same_seed():
    assert draw_cards(CONFIG, "train", 50, seed=1) == draw_cards(
        CONFIG, "train", 50, seed=1
    )
    assert draw_cards(CONFIG, "train", 50, seed=1) != draw_cards(
        CONFIG, "train", 50, seed=2
    )


def test_draw_cards_train_trap_rate_stays_near_the_target():
    assert 0.25 <= trap_rate(draw_cards(CONFIG, "train", 2000, seed=3)) <= 0.50


def test_draw_cards_seeds_profile_meets_every_quota():
    cards = draw_cards(CONFIG, "seeds", 40, seed=5)
    for tag, minimum in CONFIG.profiles["seeds"].quota.items():
        assert sum(tag in card.tags for card in cards) >= minimum, tag


def test_draw_cards_raises_when_quota_exceeds_n():
    with pytest.raises(ValueError):
        draw_cards(CONFIG, "seeds", 5, seed=1)


def test_draw_cards_labels_are_grounded_in_their_surface_forms():
    for card in draw_cards(CONFIG, "train", 1500, seed=6):
        label = card.label
        if label.transaction_id.startswith("TX-"):
            assert label.transaction_id[3:] in card.id_surface.replace(" ", "").replace(
                "\n", ""
            ).replace("TX-", "")
        if card.id_case in ("lookalike", "bare_no_intro", "none"):
            assert label.transaction_id == ""
        if label.amount.replace(".", "").isdigit():
            assert card.amount_surface, card
        if label.intent in ("OTHER", "UNDEFINED"):
            assert label.sub_intent == label.intent


def test_draw_cards_style_matches_what_the_label_allows_to_read():
    for card in draw_cards(CONFIG, "train", 3000, seed=8):
        if "UNDEFINED" in (
            card.label.urgency,
            card.label.sentiment,
        ) or card.sentinel_kind in (
            "too_vague",
            "truncated",
            "unintelligible",
            "thanks_only",
        ):
            assert card.length == "short", card.card_id
        if card.channel == "chat_message":
            assert not {"signature", "disclaimer", "quoted_thread"} & set(card.noise), (
                card.card_id
            )


def test_draw_cards_label_and_text_constraints_hold():
    for card in draw_cards(CONFIG, "train", 4000, seed=12):
        label = card.label
        if "UNDEFINED" in (label.urgency, label.sentiment):
            assert card.sentinel_kind in ("too_vague", "unintelligible"), card.card_id
        if label.intent == "OTHER":
            assert not label.amount and not label.transaction_id, card.card_id
        if card.sentinel_kind == "thanks_only":
            assert (label.sentiment, label.urgency) == ("positive", "low")
        assert not (
            card.id_case in ("two_main", "two_equal")
            and card.amount_case in ("two_main", "two_equal")
        )
        if card.id_case == "bare_no_intro":
            assert len(set(card.id_surface)) > 1, card.id_surface


def test_draw_cards_a_real_problem_is_never_low_urgency():
    for card in draw_cards(CONFIG, "train", 4000, seed=13):
        if card.label.sub_intent in CONFIG.problem_sub_intents:
            assert card.label.urgency in ("medium", "high"), card.card_id


def test_draw_cards_a_restricted_account_is_always_high_urgency():
    cards = [
        c
        for c in draw_cards(CONFIG, "train", 6000, seed=14)
        if c.label.sub_intent == "account_hold"
    ]
    assert cards and all(
        c.label.urgency == "high" and "furious_not_urgent" not in c.traps for c in cards
    )


def test_draw_cards_only_unintelligible_text_has_an_undefined_tone():
    for card in draw_cards(CONFIG, "train", 4000, seed=15):
        if card.label.sentiment == "UNDEFINED":
            assert card.sentinel_kind == "unintelligible", card.card_id
