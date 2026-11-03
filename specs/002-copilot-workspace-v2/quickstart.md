# Historical V0 baseline checks

These checks characterize the standalone baseline, not the current integrated demo target. In particular, its criticality confirmation before drafting is legacy behavior. Use `03_user_research.md` for the future V1 study protocol.

Open `prototype/copilot_panel/v2.html` in a browser. No installation, account or server. Reload or use the reset control to reset local state. This path is the V0 baseline; the earlier sketch is retained only for provenance.

Give testers only: “A merchant asks about a pending payout. Prepare an appropriate response.” Do not identify the intended payment. Ask them to think aloud.

Historical checks cover payment selection (“No match”), source inspection, draft changes, wrong-payment sends, help needed, and manual mode. The legacy critical confirmation can be checked only to reproduce baseline behavior; it must not be recorded as a requirement for the current product. Do not compare multiple prototype variants in the future V1 evaluation.

Everything is simulated, including send/undo, policies and traces. No draft persists after reload. No authentic ledger or policy content is available. Multi-intent tickets support manual triage and composition, not automatic splitting.
