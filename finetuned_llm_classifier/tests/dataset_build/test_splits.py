import pytest

from src.dataset_build.cards import load_config
from src.dataset_build.splits import SplitSizes, draw_pool, split_pool

CONFIG = load_config()
SIZES = SplitSizes(pool=4000, train=1500, val=100, test_natural=100, min_per_trap=8)


def _ids(cards):
    return {card.card_id for card in cards}


def test_split_pool_returns_disjoint_splits_with_the_requested_sizes():
    splits = split_pool(draw_pool(CONFIG, SIZES, seed=1), SIZES, seed=1)
    assert (
        len(splits["train"]) == 1500
        and len(splits["val"]) == 100
        and len(splits["test_natural"]) == 100
    )
    all_ids = [card.card_id for cards in splits.values() for card in cards]
    assert len(all_ids) == len(set(all_ids))


def test_split_pool_test_traps_meets_the_minimum_per_trap():
    pool = draw_pool(CONFIG, SIZES, seed=2)
    test_traps = split_pool(pool, SIZES, seed=2)["test_traps"]
    for trap in {trap for card in pool for trap in card.traps}:
        assert sum(trap in card.traps for card in test_traps) >= SIZES.min_per_trap, (
            trap
        )


def test_split_pool_raises_when_the_pool_is_too_small():
    small = SplitSizes(pool=300, train=200, val=50, test_natural=50, min_per_trap=8)
    with pytest.raises(ValueError):
        split_pool(draw_pool(CONFIG, small, seed=3), small, seed=3)


def test_split_pool_any_prefix_of_train_has_a_representative_trap_rate():
    from src.dataset_build.cards import trap_rate

    train = split_pool(draw_pool(CONFIG, SIZES, seed=5), SIZES, seed=5)["train"]
    assert 0.15 <= trap_rate(train[:100]) <= 0.55
