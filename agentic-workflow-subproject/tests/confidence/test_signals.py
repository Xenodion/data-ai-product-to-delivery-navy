import math

from ml.confidence.src.signals import field_signal


def test_field_signal_reads_first_value_token_and_ignores_syntax() -> None:
    text = '{"intent":"payments","urgency":"high"}'
    tokens = ['{"', "intent", '":"', "pay", "ments", '","', "urgency", '":"', "high", '"}']
    offsets = []
    position = 0
    for token in tokens:
        offsets.append(position)
        position += len(token)
    logprobs = [math.log(p) for p in (0.99, 0.99, 0.99, 0.6, 0.9, 0.99, 0.99, 0.99, 0.8, 0.99)]
    top = [{t: lp, "other": math.log(0.1)} for t, lp in zip(tokens, logprobs)]
    signal = field_signal(text, offsets, tokens, logprobs, top, "intent")
    assert signal is not None
    assert signal.value_token == "pay"
    assert round(signal.p_chosen, 2) == 0.6
    assert round(signal.p_top2, 2) == 0.1
    assert round(signal.p_value, 3) == 0.54


def test_field_signal_returns_none_when_field_is_missing() -> None:
    assert field_signal("{}", [0], ["{}"], [0.0], [{"{}": 0.0}], "intent") is None
