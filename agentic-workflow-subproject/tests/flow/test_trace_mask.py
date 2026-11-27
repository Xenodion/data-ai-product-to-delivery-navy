from flow.api import mask_trace_payload


def test_mask_trace_payload_drops_ticket_content_and_keeps_node_name() -> None:
    assert mask_trace_payload({"langgraph_node": "qualify", "body": "card 4111"}) == {"langgraph_node": "qualify"}
    assert mask_trace_payload({"ticket": {"body": "secret"}}) == "[masked]"
    assert mask_trace_payload("customer text") == "[masked]"
    assert mask_trace_payload(3) == 3
