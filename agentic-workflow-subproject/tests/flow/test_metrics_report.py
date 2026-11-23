from pathlib import Path

from flow.metrics_report import load_report, percentile, render
from flow.metrics_store import MetricsStore


def _store(tmp_path: Path) -> Path:
    db = tmp_path / "metrics.sqlite"
    store = MetricsStore(db)
    for i in range(20):
        store.record_node(event_id=f"q{i}", flow_id=f"T-{i}", node_id="qualifier", outcome="valid",
                          duration_ms=7000 + i, metrics={"qualifier_latency_ms": 7000 + i})
        store.record_node(event_id=f"d{i}", flow_id=f"T-{i}", node_id="drafter", outcome="drafted",
                          duration_ms=900, metrics={"drafter_latency_ms": 900, "drafter_cost_usd": 0.001,
                                                    "policy_outcome": "pass" if i else "blocked"})
    return db


def test_percentile_is_none_on_an_empty_sample() -> None:
    assert percentile([], 0.95) is None
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.0


def test_report_aggregates_latency_cost_and_quality(tmp_path: Path) -> None:
    report = load_report(_store(tmp_path))
    assert report.events == 40 and report.flows == 20
    assert percentile(report.qualifier_latency_ms, 0.95) == 7019
    assert round(sum(report.drafter_cost_usd), 6) == 0.02
    assert report.quality["policy_outcome"]["blocked"] == 1


def test_rendered_report_has_no_ticket_identifier(tmp_path: Path) -> None:
    text = render(load_report(_store(tmp_path)), "metrics.sqlite")
    assert "T-1" not in text
    assert "policy_outcome" in text and "1/20" in text
    assert "- none" in text  # 7 s p95 is under the 18 s objective


def test_slow_qualifier_raises_the_latency_alert(tmp_path: Path) -> None:
    db = tmp_path / "metrics.sqlite"
    store = MetricsStore(db)
    for i in range(10):
        store.record_node(event_id=f"q{i}", flow_id=f"T-{i}", node_id="qualifier", outcome="valid",
                          duration_ms=25000, metrics={"qualifier_latency_ms": 25000})
    assert "above the 18 s objective" in render(load_report(db), "metrics.sqlite")


def test_since_filters_older_events(tmp_path: Path) -> None:
    assert load_report(_store(tmp_path), since="2999-01-01").events == 0


def test_unavailable_qualifier_above_five_percent_raises_the_l1_alert(tmp_path: Path) -> None:
    db = tmp_path / "metrics.sqlite"
    store = MetricsStore(db)
    for i in range(20):
        status = "unavailable" if i < 2 else "valid"
        store.record_node(event_id=f"q{i}", flow_id=f"T-{i}", node_id="qualifier", outcome="succeeded",
                          duration_ms=7000, metrics={"qualifier_latency_ms": 7000, "qualifier_status": status})
    text = render(load_report(db), "metrics.sqlite")
    assert "unavailable on 10.0% of calls" in text
