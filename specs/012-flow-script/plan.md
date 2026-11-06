# Implementation Plan: Flow script A to Z

**Date**: 5 November 2026 · **Spec**: [spec.md](spec.md)

## Summary

Plain Python functions chain the steps, Pydantic types their inputs and outputs, and Langfuse traces them. The Qualifier runs in one container. Everything else is a local script.

## Technical context

- **Language**: Python 3.11, in the `agentic-workflow-subproject` environment.
- **Already installed**: `httpx`, `pydantic`, `tenacity`, `python-dotenv`.
- **New dependency**: `langfuse` only.
- **Storage**: JSONL under `flow/runs/`, ignored by Git.
- **Testing**: pytest with fake adapters; one manual real-model smoke test.
- **Constitution**: `.specify/memory/constitution.md` is still the blank template, so there is no gate to check. Repository rules apply.

## Structure

```text
agentic-workflow-subproject/
  flow/
    contracts.py         # Ticket, QualifierResult, RoutingDecision, Draft, TicketRun
    llm.py               # bounded HTTP POST with retry on transient errors
    qualifier.py         # D-q4 call and strict validation
    router.py            # pure decision
    drafter.py           # OpenRouter call and prompt
    pipeline.py          # process() and reroute()
    runner.py            # CLI: ticket selection, cadence, JSONL
    config.toml          # endpoints, models, timeouts, budget, versions
    docker-compose.yml   # Qualifier only
    runs/                # ignored
  tests/flow/
    test_router.py
    test_pipeline.py
    test_qualifier.py
    test_flow_runner.py  # distinct name: tests/ has no __init__.py and dataset_build has a test_runner.py
```

## Reused code

| Need | Existing code | Note |
|---|---|---|
| Seven-field contract | `research/qualifier/src/dataset_build/schema.py` | `TicketLabel` is imported, never copied |
| Validation | `research/qualifier/src/scoring.py` | `parse_output` |
| Desk mapping | `research/qualifier/src/scoring.py` | `desk_of`, `TRIAGE` |
| Qualifier instruction | `research/qualifier/src/prompt.py` | `build_user_message` |

## Core functions

```python
def process(ticket: Ticket, deps: FlowDeps) -> TicketRun: ...
def reroute(run: TicketRun, desk: Desk, deps: FlowDeps) -> TicketRun: ...
```

`FlowDeps` holds the `qualify` and `draft` callables and the policy version, which is how tests pass fakes.

`process` runs Qualifier, Router and Drafter. `reroute` applies the correction rules on the stored Qualifier result, so a correction costs one Drafter call at most. `TicketRun` is frozen: both functions return a new value, and drafts are kept as a versioned tuple.

`decide_route(result: QualifierResult, policy_version: str) -> RoutingDecision` covers the first decision only. It keeps the field names of the 004 contract. `reroute_count` lives on `TicketRun`.

## Qualifier call

D-q4 was evaluated by sending a raw prompt to `llama-cpp-python`, not through a chat endpoint. The flow calls the raw completion route of `llama-server` with the same formatted prompt. A chat route would apply the template embedded in the GGUF, and that is not what was measured.

- Prompt: the Qwen chat template around `build_user_message`, including the default system turn the tokenizer adds. A constant in `qualifier.py` holds it, and a one-off check compares it with `apply_chat_template` so that the runtime does not need `transformers`.
- Parameters: temperature 0, `n_ctx` 2048, stop tokens `<|im_end|>` and `<|endoftext|>`, and 160 max tokens as in the compact run.
- Failure mapping: any failed HTTP exchange, after retries where they apply, gives `unavailable`; a response that fails `parse_output` gives `invalid`.

## Drafter call

OpenRouter chat completions, plain text, with a timeout and bounded retry. The prompt gives the ticket between delimiters, the available Qualifier fields, the desk or an unknown-desk notice, and the FR-005 rules. Any Drafter error, or an empty reply, becomes `DRAFTER_UNAVAILABLE`, including a 402 from the provider. The ticket is kept.

## Tracing

`@observe(capture_input=False)` goes on `process`, `reroute`, `qualify` and `write_draft`, because their arguments hold HTTP clients and one of them carries the API key. The output of `process` includes the ticket. `decide_route` stays free of I/O, and its decision appears in the output of the `process` span. Keys come from `.env`. The runner flushes at exit, inside a guard that logs an error and carries on.

## Runner

```bash
uv run python -m flow.runner --n 5 --seed 7 --every 30
```

Reads `data/dataset/val.csv`, a fixed path with no split option, and samples with the seed. Each `Ticket` takes `card_id` and `ticket` from the file, plus a fixed merchant ID and the receipt time from the runner. Immediate mode is `--every 0`.

## Docker

One `llama-server` service with a pinned image, the `models/` folder mounted read-only, one parallel slot, and a health check. The GGUF stays outside Git and is fetched from the bucket with its checksum recorded.

## Decisions and rejected options

- **No orchestration library.** The flow is sequential, and human pauses fall between steps, so nothing needs to resume inside a running step.
- **No database yet.** Nothing here needs shared state. The front end will, and the API and storage will then wrap these functions without changing them.
- **Revisit LangGraph** only if a human must intervene inside the tool loop, agents must hand off to each other, or `pipeline.py` becomes hard to read.

## Open decisions

None for this feature.

## Decided

- Drafter model: `mistralai/mistral-nemo` through OpenRouter, $0.029 in and $0.03 out per million tokens on 5 November 2026. It is one line in `flow/config.toml`.
- Spending limit: the limit on the OpenRouter key.
- Desk naming: `technical_api`, mapped from the historical `technical` in `router.py`.
- Langfuse: cloud project.

## Risks

| Risk | Mitigation |
|---|---|
| Served Qualifier differs from evaluated D-q4 | SC-003 comparison before use |
| Container thread count differs from the evaluation | Compare outputs; latency measured separately |
| Drafter asserts unverified facts | FR-005 prompt rules, human review remains mandatory; no automated quality claim |
| `research` imports pull heavy dependencies into a future image | Only `schema`, `scoring`, `prompt` are imported; check this at containerization |

## Measured results

Local run on 5 November 2026, in Docker with about 3 GB of memory.

| Measure | Result |
|---|---|
| Prompt against `apply_chat_template` | Identical |
| Served Qualifier against stored D-q4 predictions | 10 of 10 labels identical on the first validation tickets |
| Qualifier cold start | 38 s |
| Qualifier memory | 1.7 GiB in use |
| Qualifier latency | 8.0 s on average, 17.5 s at most, over 10 tickets |
| Drafter latency, `mistralai/mistral-nemo` | 8.7 to 13.3 s over 5 tickets |
| Drafter cost | About $0.00001 per draft |
| Correction loop | One new draft, then manual handling, on a real ticket |
| Langfuse unreachable | The run completes and logs the export error |

These figures come from a handful of tickets and say nothing about draft quality.
