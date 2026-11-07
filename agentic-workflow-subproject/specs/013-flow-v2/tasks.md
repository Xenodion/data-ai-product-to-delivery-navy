# Flow v2: task list

Updated 6 November 2026. Target: [diagram](../../docs/design/flow-v2/flow_v2.svg) and [node table](../../docs/design/flow-v2/node_table_v1.md). The target architecture was validated on 6 November 2026 by the project lead. Issues hold the details; this file holds the order.

## Dev side

Tracker: #67. Each step leaves a flow that runs.

| Order | Work | Nodes | Issue | Priority |
|---|---|---|---|---|
| 1 | Measures, rules of nodes 5 and 8, turn limit | All | #54 | p0 |
| 2 | Ticket envelope and turns | 1, 3, 4 | #55 | p0 |
| 3 | Context plan and Evidence gate with stubs (tool tier 1) | 5, 8 | #56 | p0 |
| 4 | Policy check and Final compliance gate | 10, 14 | #57 | p0 |
| 5 | Desk Drafter | 9 | #36 | p0 |
| 6 | Mini ledger, knowledge base and rules (tool tier 2) | 6, 7 | #35 | p0 |
| 7 | Human actions and Send | R, 13, 15 | #58 | p0 |
| 8 | API and database | All | #31 | p0 |
| 9 | Re-router and Validator screens, Overview, injector | R, 13 | #37, #38, #32 | p0 |
| 10 | Local container demo | All | #39 | p0 |
| 11 | Judge and Redraft loop, kept only if measured | 11, 12 | #59 | p1 |
| 12 | Override switch | All | #60 | p1 |
| 13 | Traces, audit log, labelled scoring | 16 | #41, #42 | p1 |
| 14 | Evaluation in CI, model routing, readiness | All | #19, #21, #22 | p1 |

Bonus: cloud deployment (#40), embedding retrieval (#43), confidence research (#45). Out of V1: Human-only queue, built only in the architecture.

## AI Product side

Session 4, tracker #53:

| Deliverable | Issue |
|---|---|
| `04_architecture.md` | #47 |
| `evals/report_v0.md` | #48 |
| Eval set at 50 cases | #49 |
| `spec.md` v2 | #50 |
| `/prototype` | #51 |
| `governance.md`, Session 4 | #52 |

Sessions 5 to 8 and final oral, tracker #68:

| Session | Deliverable | Issue |
|---|---|---|
| S5 | `05_metrics.md` | #61 |
| S5 | Eval set v1, 200 cases | #62 |
| S6 | `06_ab_protocol.md` | #63 |
| S7 | `07_operations.md` | #64 |
| S8 | `08_launch_memo.md`, final spec and brief, `v1.0` | #65 |
| Final | Pitch and oral | #66 |
| All | Lecturer confirmations | #16 |

## Dependencies between the two sides

- #47 can start now: the target architecture is validated.
- #48 runs on the current flow; it does not wait for flow v2.
- #51 needs the policy check from #57.
- #50 follows #48.
- #61 uses the measures from #54.
