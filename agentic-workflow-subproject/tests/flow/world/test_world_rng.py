from flow.world.rng import stage_rng, stage_seed

# Literal values computed once: they must not change between interpreter runs or machines.
EXPECTED_SEED = 14088508265945197488
EXPECTED_FIRST_DRAW = 0.1763183946637451


def test_stage_seed_returns_fixed_value_for_known_inputs() -> None:
    assert stage_seed(1, "sample") == EXPECTED_SEED


def test_stage_rng_first_draw_matches_recorded_value() -> None:
    assert stage_rng(1, "sample").random() == EXPECTED_FIRST_DRAW


def test_stage_rng_streams_differ_between_stages() -> None:
    assert stage_rng(1, "sample").random() != stage_rng(1, "assign").random()


def test_stage_rng_streams_differ_between_seeds() -> None:
    assert stage_rng(1, "sample").random() != stage_rng(2, "sample").random()


def test_stage_rng_is_independent_of_other_stages_consumption() -> None:
    other = stage_rng(1, "assign")
    for _ in range(100):
        other.random()
    assert stage_rng(1, "sample").random() == EXPECTED_FIRST_DRAW
