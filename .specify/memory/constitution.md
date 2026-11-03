<!-- Sync Impact Report: scaffold -> 1.0.0 initial project constitution.
Principles: evidence, shared product, deterministic decisions, human sending,
synthetic demo boundary, operational truth, proportional delivery.
Added: scope, workflow and amendment procedure. No existing principles removed.
Ratification: proposed for team adoption; no team approval is fabricated.
Deferred intents: AI Product alignment and demonstration delivery are separate feature workflows.
Templates and application code are unchanged by the constitution workflow. -->
# NAVY Constitution

## Core Principles

### I. Evidence must retain its status

Every claim MUST distinguish fictional scenario data, assumption, measured result,
target and unimplemented capability. Interviews, timings, deployment and tests MUST NOT
be invented. Historical model predictions and evaluation results MUST be preserved.
Corrections MUST explain changed definitions rather than silently rewriting history.

### II. One shared product with separate proof levels

AI Product and LLMOps MUST describe the same Keelpay support flow. Component benchmarks,
functional demonstration and production recommendation MUST remain distinct. Product
success is active handling time at constant quality, not extraction accuracy alone.
The classroom demo's scope MUST NOT silently weaken the proposed production safeguards.

### III. The model qualifies and deterministic rules decide

The Qualifier Model MUST retain the existing seven-field extraction contract unless an explicit
migration is planned. Desk, priority, transaction resolution and draft permission MUST
be separate decisions. Missing or ambiguous fields MUST block only their dependent steps.
No invented confidence score or implicit `critical` model label is permitted.

### IV. Human control at the point of consequence

Every outgoing reply MUST result from an explicit human action after review. The system
MUST NOT send autonomously, write to a payment ledger, refund or unfreeze funds. Criticality
alone MUST NOT block preparation of an internal draft. Unresolved facts MUST NOT become
assertions. Corrections, reroutes and sent versions MUST remain auditable.

### V. Synthetic demo exception is bounded

External drafting and external traces are permitted ONLY for non-critical synthetic demo
data. Real production Keelpay data remain confined to its cloud in the fictional scenario.
Merchant scoping MUST be enforced by the backend. Public frontends MUST contain no service
secrets. Cloud deployment MUST have explicit configuration, cost assumptions and teardown.

### VI. The interface reflects operational truth

The three spaces MUST use one backend state: Overview, Qualification and routing, Replies
to review. Queue counts and animations MUST reflect actual events. Waiting time and oldest
first order are MUST for the demo. Advanced urgency management is SHOULD for the demo;
any priority-first order MUST be explicit and preserve oldest first within each priority.
New arrivals MUST NOT overwrite edits or change the selected ticket. Langfuse observes the
flow; it is not the authoritative operational queue store.

### VII. Delivery is ordered and proportionate

The team MUST finalize product trade-offs and align AI Product deliverables before treating
technical plans as ready for implementation. Each feature MUST have measurable acceptance,
dependencies and honest status. Tests MUST target material business rules, contracts and
failure/recovery behavior; cosmetic documentation changes do not require mirror tests.
No unsupported performance targets or production claims may be introduced to fill templates.

## Scope and authoritative sources

- User decisions in this conversation govern the current authorized scope.
- Original course instructions govern educational deliverables and remain intact.
- `docs/design/copilot-workflow.md` describes the proposed operational behavior.
- `finetuned_llm_classifier/src/dataset_build/schema.py` defines the current model contract;
  `docs/label_definitions.md` in that sub-project defines semantics.
- `02_sizing.xlsx` remains the financial calculation source; revisions require reconciliation.
- Feature specs describe changes; numbered course files remain the submission deliverables.
- Legacy `specs/002-copilot-workspace-v2/` remains a historical mock-up feature.

## Development Workflow

Use specify -> clarify where needed -> plan -> tasks -> analyze -> implement. Resolve feature
templates using the local Spec Kit resolver. Keep one active feature in `.specify/feature.json`.
Do not create a feature per document or manufacture independent specs for tightly coupled
changes. Plan boundaries should reflect independently verifiable outcomes. Work from the
repository root for shared product specs; the nested LLMOps setup is retained unchanged.

## Governance

This initial version records the current session decisions and is proposed for team adoption.
It does not assert a retrospective team ratification. Changes require a dated rationale,
affected documents/contracts and a migration or follow-up plan where applicable. Apply
semantic versioning: major for incompatible principles, minor for new principles, patch for
clarifications. Feature analysis MUST report unresolved contradictions before implementation.

**Version**: 1.0.0 | **Ratified**: Pending team adoption | **Last Amended**: 2026-11-03
