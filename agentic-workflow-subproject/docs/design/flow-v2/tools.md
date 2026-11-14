# Flow v2: SQL and Text Search evidence tools (nodes 6 and 7)

Decision: [ADR 0001](../adr/0001-text-search-and-ticket-resolution.md). `flow/tools.py` exposes two distinct read-only tools and keeps their results separate in `EvidenceResult.ledger` (SQL) and, in the current implementation, `EvidenceResult.retrieval` (Text Search; legacy field name pending migration). `gather_evidence()` runs only the operations selected by `ContextPlan`; when both are required it starts them concurrently and waits for both before returning to the Evidence Gate. A successful result from one tool cannot cover a missing result from the other. Enablement, timeout, fixture paths, overlap floor and result count come from `flow/config.toml`. No tool can send, write, refund or change an account. Text Search is deterministic lexical matching with metadata filters, not embedding/vector retrieval.

## Ledger lookup

- `flow/fixtures/ledger.json` is built by `python -m flow.build_synthetic_ledger` from transaction-reference strings found in ticket text in the authored synthetic `val`, `test_natural` and `test_traps` splits. The builder never reads `target` or annotation columns. The resulting status values are deterministic simulator data, not observed Keelpay facts.
- Lookup constructs an ephemeral SQLite view and enables `PRAGMA query_only` before parameterized queries. The merchant ID and canonical transaction ID come from the validated plan; neither is read from ticket text.
- Exact match returns only transaction status and record date with a ledger source/version. No match returns `not_found`; a reference belonging only to another merchant returns `wrong_merchant` without exposing its row; multiple same-merchant rows return `candidate_selection` without selecting one.
- `TX-900001` is a fixed ambiguous fixture; `TX-900002` belongs only to `M-OTHER`; `TX-900003` is absent. These exercise ambiguity, tenant isolation and missing data.

## Text Search

- `flow/fixtures/knowledge.json` contains versioned desk/sub-intent passages. Text Search filters by desk, sub-intent, approved status and validity dates, then ranks by simple token overlap; it returns at most two passages with stable IDs, versions, and excerpts.
- The expired compliance passage and an unapproved prompt-injection passage are fixtures that the filter must exclude. A stale passage retains its validity dates in the fixture.
- Returned content becomes an `EvidenceFact`; the Drafter receives these selected facts only, never raw fixture rows or unfiltered documents.

Both tools return explicit `unavailable` on fixture, SQLite, validation or local-time-budget failures. The configured budget applies to each local operation; this is not an external-service timeout because the tier-2 implementation has no network calls. All records and document text are synthetic demo fixtures; they are not pilot or production evidence. Embeddings are deferred unless evaluation demonstrates a material lexical-retrieval gap.
