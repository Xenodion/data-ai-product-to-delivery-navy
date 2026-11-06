# Tasks: Flow script A to Z

Status: done on 5 November 2026. Each task lists its check.

## Setup

- [x] T001 Find the GCS path of `model-q4.gguf`. Check: recorded in `flow/config.toml`.
- [x] T002 Add `langfuse`, `flow/config.toml`, and `flow/runs/` to `.gitignore`. Check: `uv sync` passes, `git status` ignores the runs folder, and `@observe` works on the installed version.
- [x] T003 Add `flow/docker-compose.yml`, fetch the GGUF, start the service. Check: health endpoint is OK; cold start and memory recorded (SC-006).

## Core, tests first

- [x] T004 Write `flow/contracts.py`. Check: `Ticket` rejects unknown fields such as `target`.
- [x] T005 Write `tests/flow/test_router.py` from the behaviour table, then `flow/router.py`. Check: tests pass, including repeatability (SC-002).
- [x] T006 Write `flow/llm.py` and `flow/qualifier.py` with tests for valid, invalid and unavailable output. Check: a malformed answer triggers one call only.
- [x] T007 Check the prompt constant against `apply_chat_template`, then compare `parse_output` results on five validation tickets with `docs/results/d_q4_full_run_val_predictions.csv`, which follows the order of `val.csv`. Check: SC-003.
- [x] T008 Write `flow/drafter.py` with tests for success, empty reply and provider error, including a 402. Check: tests pass with a mocked transport.
- [x] T009 Write `tests/flow/test_pipeline.py`, then `flow/pipeline.py`. Check: every remaining row of the behaviour table passes (SC-001); a correction never calls the Qualifier.

## Runner and traces

- [x] T010 Write `tests/flow/test_flow_runner.py`, then `flow/runner.py`. Check: same seed gives same order, no `target` reaches a `Ticket`, a crash keeps finished lines.
- [x] T011 Add `@observe` and the flush guard. Check: a run with an unreachable Langfuse host completes (SC-005).

## Acceptance

- [x] T012 Run one real validation ticket. Check: full trace and JSONL record (SC-004).
- [x] T013 Run five tickets and one real correction loop. Check: statuses and draft versions match the spec; cost and latency recorded.
- [x] T014 Run `uv run pytest` and `uvx ruff check`. Check: both pass.
- [x] T015 Update the subproject README and this feature's status. Check: documented commands work.
