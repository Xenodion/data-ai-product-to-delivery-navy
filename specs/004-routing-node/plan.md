# Implementation Plan: Deterministic Routing Node

**Date**: 3 November 2026 · **Spec**: [Feature 004 specification](spec.md)

## Summary

Implement the Routing Node as a pure, typed Python decision module in the shared Cloud Run backend. It consumes the existing Qualifier Model contract and versioned evidence/policy inputs. It does not retrain the model, call external APIs, write financial state, or own message sending.

## Technical context

- Runtime: Python backend, aligned with the confirmed Cloud Run target.
- Model boundary: preserve `agentic-workflow-subproject/src/dataset_build/schema.py`; adapt it into a typed validated result without changing stored historical labels.
- Decision state: immutable input envelope and output contract in `contracts.md`; persistent orchestration and event writing remain in later runtime features.
- Decision cases: `decision-cases.md` are product acceptance cases, not benchmark labels or human-validated business policy.
- Observability: emit reason codes and version references; Langfuse may trace the synthetic demo but is not the state store.

## Implementation approach

1. Freeze versioned enums, reason codes, and policy configuration with Support/Compliance review for any business settings.
2. Implement pure functions for qualifier validation result handling, desk assignment, field dependencies, priority, payment-state interpretation, preparation mode, and reroute limits.
3. Keep API orchestration, lookup clients, retrieval, generation, persistence, and send gates outside the pure decision module.
4. Add contract and table-driven unit tests from every decision case. Add determinism, tenant-isolation, idempotency, and forbidden-side-effect checks.
5. Emit a structured decision event; review trace payloads for synthetic-only data and sensitive-field minimization.
6. Integrate with the persistent ticket runtime only after the input/output contract is approved.

## Dependencies

- Stable product decisions in the root deliverables and the seven-field `TicketLabel` contract.
- Approved synthetic `PolicyConfig`; exact production deadline/escalation values remain owned by Support and Compliance.
- Backend ticket/merchant context and immutable event IDs from Feature 005.
- Lookup/retrieval status contracts from Feature 006.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Hidden decision logic in the UI or prompt | One pure Routing Node; UI displays returned reasons only |
| Missing field becomes a blanket triage | Dependency matrix and cases for every field sentinel |
| High priority is accidentally treated as a draft hold | Acceptance case requires preparation to continue |
| Wrong merchant payment leaks into a draft | Tenant scope checked before candidates/facts leave Lookup Node |
| Re-route loop or stale draft is sent | One recompute limit, version invalidation, second-change manual triage |
| Unsupported business policy is encoded as a “technical default” | Versioned config, named policy owner, no invented production values |

## Entry and exit criteria

Entry: Product target documents and the seven-field contract are stable; Support/Compliance identify the demo policy owner and approve synthetic policy values; Features 005–006 agree on result envelopes. Exit: every acceptance case passes, reason codes/versioning are inspectable, forbidden side effects are structurally absent, and failed components lead to explicit recoverable states. No production readiness is implied.
