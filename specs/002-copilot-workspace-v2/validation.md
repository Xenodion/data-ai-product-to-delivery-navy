# Historical UI Validation for the V0 Baseline — 3 November 2026

These checks establish how the standalone V0 baseline behaved at that date. They do not validate the current routing/urgency policy or deployed product; the pre-draft criticality confirmation is a known divergence from root `spec.md`.

21/21 checks passed in installed Chrome headless. Embedded JavaScript parsed successfully. Results: `browser-results.json`.

Covered: no payment preselection; desktop send action visible at 1440×900 and 1280×720; French held-payment draft; citation removal; source inspection; edits retained across ticket navigation and copilot toggle; edited-draft replacement confirmation and cancellation; no-match clarification; send-and-next; undo across tickets; critical confirmation; unrelated desk clears assisted draft; second reroute goes to triage; manual triage composition; whitespace-only send disabled; search; actual 10-second send completion and clean captured outgoing message; 390px layout without horizontal overflow.

Visual inspection: desktop and mobile PNG captures reviewed. Compacted inactive composer after the first capture showed excessive empty space. Removed mobile sticky-footer positioning. Repeated the affected journey and viewport checks after corrections.

Run from repository root: `node prototype/copilot_panel/verify-v2.cjs`. It uses the installed Windows Chrome via its headless debugging pipe, without npm dependencies. Browser launch needs an environment allowing Chrome subprocesses. Screenshots are in `assets/prototype_v2_*.png`.

The earlier build command was `node prototype/copilot_panel/build-v2.cjs`. It reuses the original synthetic fixtures. The file path is retained for reproducibility; it is not a product version label.

Limits: automated checks and visual QA are not a user study or a complete accessibility audit. Real usability outcomes remain unmeasured. No backend, genuine policy content, API calls, real send, persistent storage or automatic ticket splitting.

The implementation and Spec Kit records are now versionable. This validation applies only to the local V0 baseline; it is not a release or production readiness statement.
