# NAVY Reference Terminology

Date: 3 November 2026, updated 6 November 2026 for flow v2. This glossary governs current design documents, specifications, evaluations, and interface labels. Historical file names, registered model IDs, results, and code identifiers remain unchanged; they are not current architecture terms.

## Actors and components

| Canonical name | Type | Responsibility | Avoid in current documents |
|---|---|---|---|
| **Qualifier Model** | Fine-tuned language model | Extracts the seven fields in the `TicketLabel` contract. It does not choose a queue, desk, tool, or action. | router model, Model 1, flagger (except historical quotation) |
| **Routing Node** | Deterministic Python node | Maps the Qualifier Model's intent to a desk or triage, surfaces priority, keeps the desk on later turns. It never generates a draft or decides whether to send. | router model, Model 2 |
| **Re-router** | Human workflow node | Receives unclear tickets (`OTHER`, `UNDEFINED`, Qualifier failure, turn limit). A person corrects and enriches with typed fields (one re-entry at node 5), writes the reply, or closes. | Human Qualification, triage queue |
| **Validator** | Human workflow node | Reviews the draft with its evidence, fact dates and objections; approves, edits, sends back, or writes. Nothing is sent without this step or the Re-router. | Human Review, reviewer queue |
| **Lookup Node** (node 6) | Deterministic Python tool | Performs read-only, merchant-scoped lookup in the synthetic transaction store and returns a record, `missing`, `ambiguous` or `unavailable`. | payment model |
| **Retrieval Node** (node 7) | Deterministic Python tool | Selects approved excerpts from the synthetic knowledge base and retains their source IDs. | knowledge model |
| **Drafter Model** | Language model called by the backend service | Prepares a sourced reply or clarification from the evidence and mode given by the Evidence gate; it calls no tool. External API is allowed only for synthetic demo data; Keelpay-hosted in the fictional production scenario. | draft model 2, agentic drafter |
| **Support Agent** | Human role | Acts in the Re-router and Validator nodes; the same person may perform both steps. | agent alone, human model, LLM agent |
| **Demo Injector** | Python demo script | Sends synthetic tickets to the backend on a controllable schedule and scenario. | agent, node, scheduler model |
| **Langfuse** | Observability tool | Receives correlated traces and spans, versions, latency, errors, and available costs. It is not the authoritative queue store. | queue, backend, database |

## Rule nodes and optional LLM nodes added by flow v2

| Name | Responsibility |
|---|---|
| **Evidence gate** (node 8) | Decides `factual`, `clarification` or `no_draft` from the tool results. No evidence, no factual claim. |
| **Policy check** (node 10) | Rules on the draft: no price, no refund promise, no legal advice, no figure outside the evidence. A blocked draft cannot be approved. |
| **Judge** (node 11, optional) | A different LLM with a closed rubric. It recommends and never approves; kept only if measured. |
| **Redraft** (node 12) | A stronger model rewrites with the same evidence. Shares the revision budget of 2 with the policy check. |
| **Final compliance gate** (node 14) | The same rules as the Policy check, run on the final text, whoever wrote it. |

## Human steps and interface spaces

- **Re-router** takes tickets the flow cannot route and tickets sent back by a person. No draft is prepared while a ticket is there.
- **Validator** reviews each draft that reached it; a person can also write and send from either space, through the Final compliance gate.
- **Overview**, **Re-router**, and **Validator** are the three front-end tabs. Clicking a human node in Overview opens that space and an eligible task.
- **Desk** means payments, disputes, technical/API, or compliance. **Triage** is the qualification queue when the desk is unknown; it is not a fifth specialist desk.
- **Priority** uses `high`, `medium`, `low`, or `UNDEFINED` as produced by the current contract/rules. Do not introduce a `critical` model value absent from the contract.

## Writing and history

Use the bold names exactly in current prose, tables, diagrams, metrics, and mock-up labels. An explanation may follow in parentheses, but must not create a competing proper name. “Model” alone is ambiguous when it could mean the Qualifier Model or Drafter Model. “Agent” alone is ambiguous when it could mean a person or an agentic system.

`keelpay-router-json`, `D`, `D-q4`, `D-q8`, `router.py`, `initial_brief.md`, and `finetuned_llm_classifier` are exact historical identifiers. Preserve them in reproducible evidence, adding “historical Qualifier Model artifact” where helpful. Do not rename files, the Vertex registry entry, or metrics to imply a migration.
