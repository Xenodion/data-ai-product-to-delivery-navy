# NAVY Reference Terminology

Date: 3 November 2026. This glossary governs current design documents, specifications, evaluations, and interface labels. Historical file names, registered model IDs, results, and code identifiers remain unchanged; they are not current architecture terms.

## Actors and components

| Canonical name | Type | Responsibility | Avoid in current documents |
|---|---|---|---|
| **Qualifier Model** | Fine-tuned language model | Extracts the seven fields in the `TicketLabel` contract. It does not choose a queue, desk, tool, or action. | router model, Model 1, flagger (except historical quotation) |
| **Routing Node** | Deterministic Python node | Maps the Qualifier Model's intent to an initial desk and surfaces priority. It never generates a draft or decides whether to send. | router model, Model 2 |
| **Re-router** | Human workflow node | Corrects a desk when the initial assignment is unclear or wrong, then sends the ticket for a fresh draft. | Human Qualification, triage queue |
| **Validator** | Human workflow node | Checks each generated draft, fixes draft issues, and approves or sends it; routes desk errors to the Re-router. | Human Review, reviewer queue |
| **Lookup Node** | Deterministic Python node | Performs read-only, merchant-scoped lookup in the synthetic transaction store and returns a match, candidates, absence, or conflict. | payment model |
| **Retrieval Node** | Deterministic Python node | Selects approved excerpts from the synthetic knowledge base and retains their source IDs. | knowledge model |
| **Drafter Model** | Language model called by the backend service | Prepares a sourced reply, clarification, or explicit failure from provided inputs. External API is allowed only for synthetic demo data; Keelpay-hosted in the fictional production scenario. | draft model 2, agentic drafter |
| **Support Agent** | Human role | Acts in the Re-router and Validator nodes; the same person may perform both steps. | agent alone, human model, LLM agent |
| **Demo Injector** | Python demo script | Sends synthetic tickets to the backend on a controllable schedule and scenario. | agent, node, scheduler model |
| **Langfuse** | Observability tool | Receives correlated traces and spans, versions, latency, errors, and available costs. It is not the authoritative queue store. | queue, backend, database |

## Human steps and interface spaces

- **Re-router** corrects the initial desk when needed. Draft preparation continues while routing work is pending.
- **Validator** handles draft problems after generation and is the only pre-send human gate. A desk problem returns through the Re-router and triggers a fresh draft.
- **Overview**, **Re-router**, and **Validator** are the three front-end tabs. Clicking a human node in Overview opens that space and an eligible task.
- **Desk** means payments, disputes, technical/API, or compliance. **Triage** is the qualification queue when the desk is unknown; it is not a fifth specialist desk.
- **Priority** uses `high`, `medium`, `low`, or `UNDEFINED` as produced by the current contract/rules. Do not introduce a `critical` model value absent from the contract.

## Writing and history

Use the bold names exactly in current prose, tables, diagrams, metrics, and mock-up labels. An explanation may follow in parentheses, but must not create a competing proper name. “Model” alone is ambiguous when it could mean the Qualifier Model or Drafter Model. “Agent” alone is ambiguous when it could mean a person or an agentic system.

`keelpay-router-json`, `D`, `D-q4`, `D-q8`, `router.py`, `initial_brief.md`, and `finetuned_llm_classifier` are exact historical identifiers. Preserve them in reproducible evidence, adding “historical Qualifier Model artifact” where helpful. Do not rename files, the Vertex registry entry, or metrics to imply a migration.
