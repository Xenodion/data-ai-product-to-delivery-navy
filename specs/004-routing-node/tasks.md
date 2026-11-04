# Tasks: Deterministic Routing Node

Status: planning only. No Routing Node implementation exists as part of this feature yet.

## Phase 0 — Validate decision consequences

- [ ] T000 Review [`error-consequences.md`](error-consequences.md): confirm the intent-to-desk mapping, Re-router path, priority branches and offline metrics with the project owner.
- [ ] T000a Approve invalid/unavailable/unmapped intent handling, urgency display, and the rule that draft flow continues while Re-router work is pending.
- [ ] T000b Confirm the decision cases cover the Router outcomes; record reviewer, date, and policy version.

## Phase 1 — Freeze contract

- [ ] T001 Review enums, reason codes, and `RoutingDecision` output with Support and Compliance owners.
- [ ] T002 Approve and version the synthetic demo `PolicyConfig`; explicitly list business values still unset for production.
- [ ] T003 Cross-check decision cases against the 20 S3 cases and available fixture schema; keep sources untrusted until created/reviewed.

## Phase 2 — Pure Python decisions

- [ ] T004 Implement schema-result handling and deterministic intent-to-desk mapping.
- [ ] T005 Implement field dependency decisions for `UNDEFINED`, empty values, and `OTHER`; preserve known desk when payment identity is missing.
- [ ] T006 Implement independent priority aggregation and reason/source provenance; high priority must not block draft preparation.
- [ ] T007 Implement payment-resolution/preparation mapping for exact ID, candidates, missing ID, conflict, wrong merchant, not found, and lookup failure.
- [ ] T008 Implement source/drafter failure modes and safe clarification/manual outcomes.
- [ ] T009 Implement first/second desk-reroute behavior and downstream draft invalidation.

## Phase 3 — Contract, trace, and recovery checks

- [ ] T010 Add table-driven tests for every case in `decision-cases.md` and the S3 contract cases.
- [ ] T011 Add determinism, malformed-input, cross-merchant isolation, idempotency, and no-send/no-ledger-side-effect checks.
- [ ] T012 Emit structured reason/version events and verify sensitive values are excluded from external demo traces unless permitted by the synthetic-only policy.
- [ ] T013 Integrate with Features 005/006 after their request/result interfaces are frozen; record failures and retry/manual paths.

## Completion

- [ ] T014 Obtain second-person review of decision cases and policy provenance.
- [ ] T015 Re-run full acceptance checks on the integrated demo and update current capability status; do not call benchmark results end-to-end evidence.
- [ ] T016 Freeze action/urgency references and denominators on validation, then report the five-column action matrix and urgent cohort on the held-out test. Keep historical model-only gates and results separate; no retrospective threshold tuning.
- [ ] T017 Instrument direct inference and workflow counters, then define a reviewed sample for delayed quality metrics. Record initial Router decisions separately from Re-router/Validator corrections and tag all series by immutable model and policy version.
