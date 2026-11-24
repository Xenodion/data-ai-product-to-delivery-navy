"""End-to-end rollback verification on the 100-case eval-set v1 (#60)."""

from flow.rollback_check import render_markdown, replay_mode


def test_eval_set_v1_at_l1_produces_zero_drafts_and_keeps_routing_and_context() -> None:
    summary = replay_mode("l1_drafting_off")
    assert summary.total == 100
    assert summary.qualifier_calls == 100
    assert summary.drafter_calls == 0
    assert summary.drafts_created == 0
    assert summary.sends_triggered == 0
    assert summary.by_status == {"awaiting_reroute": 21, "awaiting_validation": 79}
    assert summary.tool_calls > 0
    assert summary.fifo_preserved
    assert summary.manual_resolution_verified


def test_eval_set_v1_at_l2_sends_every_ticket_to_manual_routing_with_zero_drafts() -> None:
    summary = replay_mode("l2_routing_off")
    assert summary.total == 100
    assert summary.qualifier_calls == 100
    assert summary.tool_calls == 0
    assert summary.drafter_calls == 0
    assert summary.drafts_created == 0
    assert summary.by_status == {"awaiting_reroute": 100}
    assert summary.by_desk == {"triage": 100}
    assert summary.fifo_preserved
    assert summary.manual_resolution_verified


def test_eval_set_v1_at_l3_runs_zero_models_or_tools_and_manual_queue_works() -> None:
    summary = replay_mode("l3_copilot_off")
    assert summary.total == 100
    assert summary.qualifier_calls == 0
    assert summary.tool_calls == 0
    assert summary.drafter_calls == 0
    assert summary.drafts_created == 0
    assert summary.sends_triggered == 0
    assert summary.by_status == {"awaiting_reroute": 100}
    assert summary.by_desk == {"triage": 100}
    assert summary.fifo_preserved
    assert summary.manual_resolution_verified
    assert "`l3_copilot_off`" in render_markdown([summary])
