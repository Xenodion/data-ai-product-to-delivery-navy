# LangGraph orchestration prototype

Status: incremental implementation. Intake through Policy Check are separate graph nodes and share business step functions with the synchronous `process()` adapter. Human review, approval, final send confirmation and simulated send are resumable graph steps. Optional Judge/Redraft, domain audit persistence and all of nodes 1–16 are not yet implemented in the graph.

## Graph

```text
START -> intake -> qualifier -> field_check -> routing -> context_plan -> tools
                                                        -> evidence_gate -> drafter -> policy_check -> finalize_ticket
                                                                                                      -> human_review -> apply_human_action
                                                     | approve -> send_confirmation -> simulated_send -> END
                                                     | edit/write/reroute -> human_review
                                                     | close -> END
                           no -------------------------------> END
```

Render the graph from Python with:

```python
graph = build_ticket_graph(deps)
print(graph.get_graph().draw_mermaid())
```

The graph can be opened in a Mermaid viewer for this first local iteration. LangGraph Studio is a later UI option; the prototype does not require a hosted LangSmith deployment.

## Qualifier model adapter

The runtime constructs a `ChatOpenAI` model through `langchain-openai`, pointed at llama.cpp's OpenAI-compatible `/v1` endpoint. `with_structured_output(..., method="json_schema", strict=True, include_raw=True)` sends the closed `TicketLabel` schema with the taxonomy enums. The raw answer is retained for diagnostics, and the existing Pydantic validator remains the authority for cross-field rules such as intent/sub-intent consistency and reference formats. Qualifier and Drafter prompts resolve by production label through Langfuse Prompt Management; the selected prompt name, label, version and fallback state are recorded on the node observation and result contract. LangGraph owns orchestration; LangChain owns the model adapter and structured-output wrapper.

This constrained runtime is a separate evaluated system from the historical unconstrained D-q4 benchmark. Do not report runtime scores as the original model-only benchmark. The exact `server-b5974` image still needs a smoke test to confirm it accepts LangChain's OpenAI-compatible `response_format` payload. The initial Langfuse prompt resources also need to be created and promoted with the configured labels; without that setup the explicitly marked local fallback is used.

## Resume contract

`build_ticket_graph(deps)` uses LangGraph's in-memory checkpointer by default, intended only for local exploration. Each ticket thread needs a stable LangGraph `thread_id` in `configurable`. Human review and send confirmation pause with `interrupt`; resume the same thread using LangGraph's `Command(resume=...)` with the corresponding action payload. For durable recovery, pass a production-capable checkpointer and separately persist ticket events, human action versions, idempotency keys and send receipts in the application database. A framework checkpoint alone is not the business audit log.

The current checkpoint contains serialized ticket/run state, including user text and reply text. Use synthetic cases only in this local prototype. Before enabling a durable or hosted checkpointer, define access controls, encryption, retention and deletion behavior.

## Runtime measures

`FlowState.metrics` carries per-thread snapshots: completed graph-node counts/outcomes, node duration samples, pipeline Qualifier/Drafter latency and reported cost, evidence/policy outcomes, interrupt/resume counts, human action counts, final gate outcome, simulated-send outcomes and elapsed wall time. `lifecycle_events` is an in-state diagnostic list. When enabled in `flow/config.toml`, `MetricsStore` also records allowlisted node events and increments SQLite aggregates transactionally. It stores no ticket text; it is a local telemetry adapter, not the durable domain audit/event store tracked by #31. Node measurements are aggregated once at their emitting node.

## Qualifier output contract

The Qualifier node calls the fine-tuned D-q4 model through llama.cpp's native `/completion` endpoint. It sends a JSON Schema derived from the shared `TicketLabel` Pydantic contract to constrain decoding, then runs the generated JSON through `parse_output` and the full Pydantic validator. The schema constrains the object shape and closed vocabularies; Pydantic remains authoritative for relational rules, including whether a `sub_intent` belongs to its `intent`.

This node does not call LangChain's `with_structured_output`: that is a model wrapper on LangChain chat-model objects, whereas the current inference adapter is direct HTTP to the llama.cpp completion API. LangGraph owns graph orchestration and state transitions; it does not itself change the model's decoding format. Keeping llama.cpp's native schema constraint avoids an extra wrapper while retaining deterministic application-side validation.

## Known prototype limits

- Optional Judge/Redraft and human rerouting remain grouped in the existing `reroute` business function; their full feedback budget is not implemented.
- The default `InMemorySaver` loses checkpoints when the process exits and is not a production persistence choice.
- The graph's human action branch is an integration proof. CI replay, restart recovery, duplicate-effect behavior and the complete 200-case full-flow suite remain to be implemented. SQL and deterministic lexical Text Search are independent tools: the plan calls only required tools, runs both concurrently when both are required, and waits for both before the Evidence Gate. Their current Python result field still uses the legacy name `retrieval` pending migration.
- `Langfuse` decorators explicitly disable both input and output capture on functions that receive or return ticket/draft state. `FlowState.metrics` are not yet exported as Langfuse scores/observations; safe metadata export and graph trace correlation remain follow-up work.
- SQLite metric events and incremental aggregates are implemented for local runs. Container named-volume mounting, rebuild/reconciliation, the PostgreSQL domain event store and durable send idempotency remain outstanding.
