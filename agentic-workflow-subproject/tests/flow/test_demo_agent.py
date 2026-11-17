from flow.demo_agent import ACTOR, choose_action


def _item(allowed: list[str], **extra: object) -> dict[str, object]:
    return {"ticket_id": "val-x", "turn": 1, "version": 3, "allowed_actions": allowed, **extra}


def test_choose_action_sends_when_ready() -> None:
    assert choose_action(_item(["send"]), {}) == ("send", {"actor": ACTOR, "disposition": "close"})


def test_choose_action_prefers_approve_over_edit() -> None:
    route, payload = choose_action(_item(["write_reply", "handoff_to_rerouter", "approve", "edit_draft"]), {})
    assert (route, payload["action"]) == ("actions", "approve")


def test_choose_action_reroutes_to_reference_desk_and_never_to_triage() -> None:
    assert choose_action(_item(["reroute", "write_reply"]), {"val-x": "disputes"})[1]["desk"] == "disputes"
    assert choose_action(_item(["reroute", "write_reply"]), {"val-x": "triage"})[1]["desk"] == "payments"


def test_choose_action_edits_latest_fresh_draft() -> None:
    drafts = [{"version": 1, "text": "old", "stale": True}, {"version": 2, "text": "new", "stale": False}]
    payload = choose_action(_item(["write_reply", "edit_draft"], drafts=drafts), {})[1]
    assert (payload["action"], payload["text"], payload["draft_version"]) == ("edit_draft", "new", 2)


def test_choose_action_waits_when_nothing_is_allowed() -> None:
    assert choose_action(_item([]), {}) is None
