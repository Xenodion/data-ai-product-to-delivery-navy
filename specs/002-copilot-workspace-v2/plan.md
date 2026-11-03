# Historical Implementation Plan: Keelpay V0 Baseline

**Date**: 2026-11-03 · **Spec**: [spec.md](spec.md)

## Summary
The earlier work item used path `prototype/copilot_panel/v2.html`; it is now the one V0 local baseline. The earlier sketch is retained as provenance only. The future V1 will be a single reworked successor, designed from the current workflow and feedback rather than maintained as a parallel variant.

## Technical Context
HTML, CSS, vanilla JavaScript. Four existing fixtures. Memory-only session state, no backend or runtime dependencies. Browser interaction and viewport checks plus syntax checks. Desktop first, responsive below 1100px and 760px.

## Constitution Check
The installed `.specify/memory/constitution.md` in the classifier project was an unfilled template, not an adopted constitution. At the time of implementation, root `spec.md` required a critical confirmation before drafting. That behavior is now superseded: current target allows urgent draft preparation and uses dependency-scoped human decisions. The V0 baseline remains a historical research artifact; do not use its old criticality gate as the product rule. Do not change classifier taxonomy or pipeline.

## Project Structure
- `prototype/copilot_panel/v2.html`: portable implementation.
- `specs/002-copilot-workspace-v2/`: specification, research, plan, data model, quickstart, tasks, validation.

## Design
Three columns, 268px queue / fluid conversation / 300px context. Decision cards above the merchant message. Fixed composer footer, independently scrolling conversation. Native radio controls and details elements. Event handlers update session before rerendering. Source inspection uses a modal with honest synthetic provenance. A single pending-send transaction can be undone across ticket navigation.

## Complexity Tracking
No framework, build system, database or real model service warranted for a portable research prototype. Follow spec-kit artifacts manually using existing templates; do not initialize a new repository, switch branches or overwrite the classifier's spec-kit setup.
