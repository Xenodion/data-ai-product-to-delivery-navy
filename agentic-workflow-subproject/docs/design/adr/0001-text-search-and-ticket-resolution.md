# ADR 0001: Text Search and ticket resolution at send

- **Status:** Accepted for the V1 design
- **Date:** 10 November 2026
- **Scope:** Flow v2 evidence tools, ticket lifecycle, API and agent workspace

## Context

The flow has two independent read-only evidence sources: a structured transaction ledger and a small approved-document knowledge base. The current document lookup uses desk/sub-intent/date filters plus deterministic token overlap. It does not use embeddings, a vector index, a user-authored search query, or autonomous tool selection. Calling this RAG overstates the implemented retrieval method and makes embeddings appear to be a requirement when they are not.

The workflow already supports manual closure without a reply (`closed_manual`) and simulated sending (`sent_simulated`), but it does not let the Support Agent explicitly choose whether a ticket remains open or closes when the reply is sent.

## Decisions

1. Name the two evidence tools **SQL** and **Text Search** in current architecture and product documents. SQL serves structured records. Text Search returns a bounded set of approved, current document passages with stable source IDs, versions, and excerpts. It is deterministic and read-only.
2. Keep the tools independent. The Context Plan may select either, both, or neither. If both are selected they run concurrently and the Evidence Gate waits for both outcomes. A missing result from one source is not covered by the other.
3. Do not introduce embeddings or vector infrastructure in V1. Reconsider them only if a documented evaluation shows material retrieval misses caused by lexical mismatch, and compare against a deterministic lexical baseline on the same cases.
4. At the final human send action, require the Support Agent to choose **send and leave open** or **send and close**. This is a human disposition, not an LLM decision. The choice is recorded with the send event and simulated receipt; closure requires the same approval, final compliance gate, optimistic version, and idempotency protections as sending.
5. Preserve **close without reply** as a separate manual action with a required reason. A sent-and-closed ticket must remain distinguishable from a manually closed ticket and from a sent-but-open ticket in state, history, metrics, and UI.
6. Keep `flow_v2.svg` unchanged for now. This ADR and the detailed architecture/contracts are authoritative for the newly clarified behavior until the diagram is revised in a dedicated documentation update.
7. A sent-closed ticket is terminal in V1. Reopening it requires a separately designed, audited human action; a new merchant turn must not silently reopen it.

## Consequences

- Rename internal/documentation concepts from `RAG`/generic retrieval toward `Text Search` as implementation work permits; historical references and serialized data need compatibility handling.
- Define stable lifecycle states for sent-open and sent-closed, without conflating either with `closed_manual`.
- Extend the send request, persisted event/receipt, overview counters, and frontend controls to carry and display the explicit disposition.
- Add full-flow evaluation cases for send-open, send-close, close-without-reply, missing/ambiguous evidence, and SQL/Text Search independently and together.
- The existing SVG may temporarily show a generic knowledge search node and the old send/close distinction. Do not treat it as updated to this ADR.

## Implementation status

The domain contract, API send request, LangGraph send path, local metrics, injector follow-up guard, and workspace choice are now implemented in the local prototype. Existing `sent_simulated` checkpoints are read as sent-open for compatibility. Restart, HTTP idempotency, full-flow acceptance, and the 200-case evaluation have not yet been run against the new behavior.

## Revisit when

- A frozen retrieval evaluation demonstrates that lexical Text Search misses materially relevant passages due to paraphrase or vocabulary mismatch.
- Product validation finds that a single send-time disposition is insufficient (for example, a separate reopen flow or a more expressive resolution taxonomy is needed).
