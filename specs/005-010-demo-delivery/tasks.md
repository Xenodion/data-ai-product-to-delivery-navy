# Execution checklist — features 004–010

Detailed scope and gates: [plan.md](plan.md), [spec.md](spec.md). Items are unimplemented unless checked. Parallel confidence research has its own [plan](../011-confidence-signals/plan.md).

## Contracts and runtime

Feature [012](../012-flow-script/tasks.md) comes first and delivers the routing, Qualifier and direct Drafter steps as local functions (T05–T07).

- [x] T01 — Specify state transitions, event and HTTP schemas, idempotency and queue order (#30). See [runtime contract](runtime-contract.md).
- [ ] T02 — Define seed scenarios, session reset fence, cumulative metrics and recovery acceptance cases (#30, #32, #38).
- [ ] T03 — Provision local PostgreSQL, migrations, API and flow loop (#31).
- [ ] T04 — Implement ingress, restart recovery, reset and event persistence; exercise restarts and duplicate requests (#31, #32).
- [ ] T05 — Implement feature 004 deterministic routing and table-driven decision cases (#34).
- [ ] T06 — Integrate real D-q4 service, strict seven-field validation and model provenance; measure CPU footprint (#33).
- [ ] T07 — Implement V1 direct Drafter adapter, failure recovery and draft versions (#36).
- [ ] T08 — Expose route correction, one re-preparation and idempotent simulated send through the API (#31, #34, #36).

## Experience and delivery

- [ ] T09 — Build dataset injector with repeatable case selection, immediate and timed modes (#32).
- [ ] T10 — Build Re-router and Validator with server-backed actions and accessible states (#37).
- [ ] T11 — Build Overview with current queues, cumulative metrics and reset control (#38).
- [ ] T12 — Containerize and run real-model end-to-end local smoke, restart and teardown (#39).
- [ ] T13 — Evaluate cloud execution, persistent storage, costs, secrets and deploy/verify if feasible (#40).
- [ ] T14 — Extend Langfuse traces to the runtime, then add labelled scoring (#41, #42).
- [ ] T15 — Reconcile course requirements, CI evaluation, readiness and evidence (#16, #19, #21, #22, #44).
- [ ] T16 — V2 read-only synthetic SQL/KB tooling and retrieval comparison (#35, #43).
