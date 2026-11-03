# NAVY Reference Terminology

Date: 3 November 2026. This glossary governs current design documents, specifications, evaluations, and interface labels. Historical file names, registered model IDs, results, and code identifiers remain unchanged; they are not current architecture terms.

## Actors and components

| Canonical name | Type | Responsibility | Avoid in current documents |
|---|---|---|---|
| **Qualifier Model** | Fine-tuned language model | Extracts the seven fields in the `TicketLabel` contract. It does not choose a queue, desk, tool, or action. | router model, Model 1, flagger (except historical quotation) |
| **Routing Node** | Deterministic Python node | Applies versioned decision tables for desk, priority, qualification dependencies, and draft mode. Qualifier Model output is never a desk assignment by itself. | router, routing model, Model 2, decision tree while implementation remains open |
| **Lookup Node** | Deterministic Python node | Performs read-only, merchant-scoped lookup in the synthetic transaction store and returns a match, candidates, absence, or conflict. | payment model |
| **Retrieval Node** | Deterministic Python node | Selects approved excerpts from the synthetic knowledge base and retains their source IDs. | knowledge model |
| **Drafter Model** | Language model called by the backend service | Prepares a sourced reply, clarification, or explicit failure from provided inputs. External API is allowed only for synthetic demo data; Keelpay-hosted in the fictional production scenario. | draft model 2, agentic drafter |
| **Support Agent** | Human | Resolves blocking cases, corrects the desk, reviews facts and sources, edits when useful, and explicitly triggers each simulated send. | agent alone, human model, LLM agent |
| **Demo Injector** | Python demo script | Sends synthetic tickets to the backend on a controllable schedule and scenario. | agent, node, scheduler model |
| **Langfuse** | Observability tool | Receives correlated traces and spans, versions, latency, errors, and available costs. It is not the authoritative queue store. | queue, backend, database |

## Human steps and interface spaces

- **Human Qualification** resolves only a decision that cannot be made from available data. It is not mandatory for every ticket.
- **Human Review** checks every reply before sending; editing is optional.
- **Overview**, **Qualification & Routing**, and **Replies to Review** are the three front-end tabs. Clicking a human node in Overview opens the matching space and an eligible task.
- **Desk** means payments, disputes, technical/API, or compliance. **Triage** is the qualification queue when the desk is unknown; it is not a fifth specialist desk.
- **Priority** uses `high`, `medium`, `low`, or `UNDEFINED` as produced by the current contract/rules. Do not introduce a `critical` model value absent from the contract.

## Writing and history

Use the bold names exactly in current prose, tables, diagrams, metrics, and mock-up labels. An explanation may follow in parentheses, but must not create a competing proper name. “Model” alone is ambiguous when it could mean the Qualifier Model or Drafter Model. “Agent” alone is ambiguous when it could mean a person or an agentic system.

`keelpay-router-json`, `D`, `D-q4`, `D-q8`, `router.py`, `initial_brief.md`, and `finetuned_llm_classifier` are exact historical identifiers. Preserve them in reproducible evidence, adding “historical Qualifier Model artifact” where helpful. Do not rename files, the Vertex registry entry, or metrics to imply a migration.
