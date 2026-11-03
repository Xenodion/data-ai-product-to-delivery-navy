# Session model

Fixtures retain their original merchant messages and transaction facts in the V0 baseline.
Per ticket: `desk`, `confirmed`, `reroutes`, `picked`, `text`, `edited`, `copilot`, `sent`, `log`.
`picked` is null, a tenant-scoped transaction ID, or `none` (clarification).
`text` is always the outgoing prose, never a citation-bearing internal draft.
Switching tickets does not reset session. Switching payments resets generated text only with explicit confirmation if edited.
Pending send: one ticket ID, captured text, next flag, timer expiry; undo restores that ticket to editable state. Expiry commits only in memory.
