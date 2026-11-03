# Implementation Plan: AI Product Alignment
**Feature**: 003-ai-product-alignment | **Date**: 2026-11-03<br>
**Spec**: [spec.md](spec.md)<br>
**Status**: In progress; multiple documents aligned, final evidence/reconciliation open.

## Summary

Align AI Product decisions, claims, and current deliverables to one shared flow. Deliver defensible course documents with sources, limits, and pilot conditions, then enable later technical planning.

## Technical context

**Language/version:** Markdown/CSV UTF-8, existing XLSX; no application stack in this feature.<br>
**Dependencies:** original Word assignment briefs, nested model schema/results, audit/design references, local Spec Kit scripts.<br>
**Storage:** versioned files; preserve human research notes according to their source.<br>
**Validation:** cross-requirement review, financial reconciliation, and twenty-case checks; no mirror tests for prose.<br>
**Target:** shared repository and course deliverables.<br>
**Feature type:** documentary/methodological alignment.<br>
**Quality goals:** no application latency requirement; published figures reconcile within rounding; no invented human evidence.<br>
**Constraints:** preserve local changes, original instructions, historical results, and brief limit of four MUST/five WON'T minimum.<br>
**Scope:** existing S1–S3 deliverables, S4 architecture, and future deliverable preparation.

## Constitution check

- Evidence status is explicit; unsupported research results are not presented as findings.
- Benchmark, demo, pilot, and production are distinct.
- Model contract remains; deterministic decisions and dependencies are explicit.
- Human send and targeted recovery remain.
- External-service exception is limited to synthetic demo data; historical data unchanged.
- Three spaces, wait, and FIFO are requirements, not claimed implementation.
- AI Product alignment precedes implementation; open parameters stay visible.

**Result:** no design violation identified; documentary implementation must still be validated.

## Project structure

Feature files: spec, plan, research, data model, quickstart, requirements checklist, tasks.<br>
Design sources: `docs/design/ai-product-decisions.md`, `copilot-workflow.md`, `terminology.md`.<br>
Deliverables: README, pitch, problem statement, sizing, memo, brief, canvas, user research, prototype note, governance, root product spec, evals, architecture.

Keep course deliverables; do not replace them with feature specs. Preserve source data, prototypes, and historical results.

## Phases

### Research

Decisions are recorded in `research.md`. No stack research is needed for this lot. Business settings stay open with owners; they do not block removal of unsupported claims or scope alignment. Detailed coverage of S5–S8 awaits their actual briefs. Actual user research is a human activity, not an unknown to fill with generated text.

### Design

1. Decision register with origin, scope, status.
2. Claims register with source and evidence type.
3. Matrix from supplied course requirements to deliverables/actions.
4. Reconcile workbook/memo after correction using Spreadsheets workflow.
5. Structure twenty S3 cases and consistent fixtures before integrated evaluation.
6. Cross-cutting validation path in `quickstart.md`.

No application contracts are introduced here; business/event contracts belong in Features 004/005.

### Execution

- **Foundation:** complete requirement/claim registers; prioritize S3 due 6 November.
- **US1:** align README/pitch/problem, governance, and brief; recalibrate RICE/MoSCoW.
- **US2:** correct provenance/case set; correct workbook before memo; preserve assumptions as assumptions; record missing evidence.
- **US3:** align canvas/prototype note, create architecture, align root product spec, prepare future deliverable matrix/roadmap.
- **Validation:** run quickstart, review diffs, report closed items and items requiring human evidence or business decisions.

## Dependencies and delivery

Obvious factual corrections do not depend on interviews. New user findings require actual collection. The memo depends on final sizing; twenty integrated cases depend on taxonomy and fixtures. This feature may deliver honest document alignment while leaving user research open, but cannot claim that research requirement is satisfied before collection.

## Complexity tracking

No infrastructure, new model, or dataset migration is introduced. No paid deployment, publication, commit, or contribution is attributed to someone else in this plan.
