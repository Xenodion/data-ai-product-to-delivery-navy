# Historical Build Record: Keelpay Workspace Baseline

**Created**: 2026-11-03 · **Status**: Historical build record for the local V0 baseline (previously called V2); usability validation pending; superseded as the current product target by root `spec.md`.
**Input**: Refactor the helpdesk mock-up using spec-kit and enterprise console patterns.

## User Scenarios & Testing

### User Story 1 — Identify the payment and answer (P1)
As a support agent I compare matching payments before writing an answer.
1. Given K-24121, when opened, both payments show amount, date and decisive status above the composer. Neither is preselected.
2. When a payment is selected, an editable French draft appears under the merchant message; citations remain outside the outgoing text.
3. When neither matches, a clarification draft asks for a reference/date without asserting a payment status.
4. When switching tickets or disabling copilot, edits survive. Changing payment asks before discarding an edited draft.

### User Story 2 — Review and send safely (P1)
1. Empty answers cannot be sent. Only an explicit agent click simulates sending.
2. Send and Send & next remain accessible in a fixed composer footer on desktop.
3. A simulated outgoing message can be undone for 10 seconds, even after switching tickets.
4. The current target shows urgency without blocking draft preparation. The V0 baseline retains its legacy pre-draft criticality gate; this behavior is not part of the successor target.

### User Story 3 — Inspect and correct (P2)
1. Merchant context is in a narrow rail; extraction, sources, routing and activity are expandable.
2. Source buttons identify the synthetic record or policy (no fabricated external links).
3. Rerouting never reuses a payment/dispute answer for an unrelated desk: manual composition is offered. A second reroute requires triage.
4. Copilot off leaves a usable manual composer. Search filters the four fictional tickets.

## Requirements
- FR-001: Preserve all four synthetic scenarios and their provenance in the single V0 baseline.
- FR-002: No external fonts, dependencies, API calls or actual sending; open as a local file.
- FR-003 (superseded): The original V0 interface was French. The current V0 baseline uses English interface copy and retains original merchant message and reply languages.
- FR-004: Keyboard controls, visible focus, semantic headings, labelled radios and textarea, text as well as color for statuses, responsive layout.
- FR-005: Explicit prototype notice; reload resets state; reset button starts a new session.
- FR-006: Never expose internal numbered citation markers in the simulated sent reply.

## Key Entities
Ticket (original fixture); per-ticket session (desk, confirmation, payment, draft, edited flag, events); pending send (ticket, text, expiry).

## Success Criteria
- SC-001: At 1440×900 and 1280×720 the primary composer action is visible without scrolling.
- SC-002: All four paths, no-match, manual mode, reroute, draft preservation and undo pass browser checks.
- SC-003: Target for user research: 4/5 agents complete payment task without help in under 2 minutes; zero wrong-payment sends. This is a hypothesis, not a measured outcome.

## Assumptions & Edge Cases
Desktop first; mobile stacks views. Synthetic sources are labelled, not live evidence. Reload intentionally resets memory. An edited draft requires confirmation before payment replacement. Pending send locks its ticket until undo or completion. A second reroute requires human triage. No policy-block fixture is added in this UI iteration.
