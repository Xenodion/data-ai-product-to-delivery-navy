# Feature Specification: Flow script A to Z

**Feature**: 012-flow-script<br>
**Created**: 5 November 2026<br>
**Status**: Implemented locally on 5 November 2026; results in the [plan](plan.md#measured-results)<br>
**Authority**: [Root product spec](../../spec.md), [workflow](../../docs/design/copilot-workflow.md), [Routing Node spec](../004-routing-node/spec.md). This feature comes first in the [integrated demo delivery](../005-010-demo-delivery/spec.md).

## Outcome

A local Python script takes a synthetic validation ticket through Qualifier, Routing Node and Drafter, and stops at the first human step. A small runner feeds it tickets. There is no database, API or front end yet: each run writes a JSONL file and a Langfuse trace.

The goal is to prove the real chain with the real D-q4 model before building anything around it.

## User stories

### US1: Process one ticket end to end (P1)

As a developer, I run one real validation ticket and read its seven fields, routing decision, draft, status and trace.

**Independent test**: with the Qualifier container and an OpenRouter key available, the runner processes one ticket and writes one complete record.

### US2: Keep failures visible (P1)

As a developer, I see a failed step on the ticket record, and the ticket is never lost, repaired or silently completed.

**Independent test**: with fake adapters, each failure in the table below produces the expected status and reason code.

### US3: Replay the correction loop (P1)

As a developer, I apply a desk correction to a finished run and get the behaviour of the workflow map: one new draft on the first change, manual handling on the second.

**Independent test**: with a fake Drafter, two successive corrections produce the expected drafts, statuses and counts.

### US4: Feed a sequence (P2)

As a presenter, I replay a repeatable sequence of validation tickets at a chosen cadence.

**Independent test**: two runs with the same seed select the same tickets in the same order.

## Behaviour

The Drafter attempts a reply for every ticket, as the root spec requires, including when the desk is unknown or the Qualifier failed. Draft preparation does not wait for a human.

| Situation | Desk | Priority | Draft | Status | Reason codes |
|---|---|---|---|---|---|
| Valid output, supported intent, Drafter succeeds | Mapped desk | From urgency | Yes | `awaiting_validation` | `DESK_FROM_SUPPORTED_INTENT` |
| `intent=UNDEFINED` | `triage` | From urgency | Generic | `awaiting_reroute` | `INTENT_UNDECIDABLE` |
| `intent=OTHER` | `triage` | From urgency | Generic | `awaiting_reroute` | `INTENT_UNSUPPORTED` |
| Qualifier output invalid | `triage` | `unknown` | Generic | `awaiting_reroute` | `QUALIFIER_INVALID` |
| Qualifier unavailable | `triage` | `unknown` | Generic | `awaiting_reroute` | `QUALIFIER_UNAVAILABLE` |
| Drafter fails, desk known | Unchanged | Unchanged | None | `manual_handling` | `DRAFTER_UNAVAILABLE` |
| Drafter fails, desk unknown | `triage` | Unchanged | None | `awaiting_reroute` | `DRAFTER_UNAVAILABLE` |
| First desk correction | Corrected desk | Unchanged | New version, old one kept and marked stale | `awaiting_validation` | `FIRST_REROUTE_RECOMPUTE` |
| First desk correction, Drafter fails | Corrected desk | Unchanged | None current, old one marked stale | `manual_handling` | `FIRST_REROUTE_RECOMPUTE`, `DRAFTER_UNAVAILABLE` |
| Second desk correction | `triage` | Unchanged | All marked stale | `manual_handling` | `SECOND_REROUTE_MANUAL` |

Additional reason codes: `PRIORITY_UNKNOWN` for `urgency=UNDEFINED`, `HIGH_PRIORITY_SURFACE_ONLY` for high urgency and `SENTIMENT_NEUTRAL_FALLBACK` for `sentiment=UNDEFINED`. None of these changes the path.

## Functional requirements

- **FR-001**: Validate Qualifier output with the existing `TicketLabel` contract, without repair. Keep the raw output on the record.
- **FR-002**: Call D-q4 with the same prompt as its evaluation: the shared instruction, the Qwen chat template, temperature 0, the same stop tokens and context size. Do not force the schema with a grammar.
- **FR-003**: Keep the Routing Node pure and deterministic. It performs no I/O and never sends. It reuses the existing intent-to-desk mapping.
- **FR-004**: Retry network errors, timeouts, 429 and 5xx only, within a bound. Never retry a malformed Qualifier output.
- **FR-005**: The Drafter receives no tools in this feature, so it has no verified facts. It must not state a payment status, refund, deadline or amount as verified. It writes a generic reply or asks for clarification.
- **FR-006**: Treat ticket text as untrusted data. It stays delimited in the Drafter prompt.
- **FR-007**: A correction reuses the stored Qualifier result and never calls the Qualifier again.
- **FR-008**: Each correction must name one of the four real desks, different from the current desk. Anything else is rejected, as is any correction after the second.
- **FR-009**: Expected labels never reach the Qualifier, Router or Drafter. The runner reads `val.csv` only and does not load `target` into a `Ticket`.
- **FR-010**: Record the cost of each draft. Spending is capped by the limit set on the OpenRouter key.
- **FR-011**: Each finished ticket is appended and flushed to JSONL immediately, so a crash keeps completed tickets.
- **FR-012**: Trace each step with Langfuse on synthetic data only. A Langfuse failure or missing key never stops a ticket.
- **FR-013**: Record versions on each run: policy, Qualifier model, Drafter model and prompt.

## Success criteria

- **SC-001**: Every row of the behaviour table has an automated test using fake adapters.
- **SC-002**: The Router returns identical output for identical input.
- **SC-003**: On five validation tickets, the served Qualifier gives the same parsed labels as `docs/results/d_q4_full_run_val_predictions.csv`. Any difference is explained before the model is called D-q4 in this flow.
- **SC-004**: One real validation ticket reaches a draft, with a full Langfuse trace and a JSONL record.
- **SC-005**: With Langfuse unreachable, the same run still completes.
- **SC-006**: Cold start, memory use and latency of the Qualifier container are recorded.

## Assumptions

- `val.csv` has no merchant or date column, so the runner assigns a fixed synthetic merchant ID and the receipt time, as the root input contract allows.
- The flow uses the 004 desk name `technical_api`. The historical scorer keeps `technical`, and the Router maps between them.
- Priority keeps the Qualifier's `high`, `medium`, `low`, or `unknown` for `UNDEFINED`. No independent priority signal exists yet.
- Corrections are function calls in this feature. Human screens come later.

## Out of scope

Database, API, worker, front end, simulated send, reset, queues, Lookup, RAG, Drafter tools, payment resolution, `preparation_mode`, cloud deployment, confidence signals and labelled scoring.
