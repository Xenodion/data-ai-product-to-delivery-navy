# ADR 0002: Policy selection by key when the world database is on

- **Status:** Proposed (nothing committed)
- **Date:** 14 November 2026
- **Scope:** Flow v2 evidence tools, merchant world database

## Context

ADR 0001 names the document tool Text Search and ranks passages by keyword overlap with the ticket. The world database stores policies with their desk, sub-intents, status and validity, but no keywords. The Context Plan already fixes desk and sub-intent, and the knowledge base holds at most two approved documents per pair.

## Decision

1. With `world_database_path` set, `flow.world_access.search_policies` selects by key: approved, valid at the ticket date, same desk, same sub-intent, ordered by `source_id`, at most `max_knowledge_results`. The ticket text plays no part.
2. The result contract is unchanged (`RetrievalToolResult`, field `approved_guidance`). Without `world_database_path`, the fixture path and its keyword overlap stay as they are.
3. Evaluation cases and documents may call the tool "policy selection" for the world path. Text Search remains the name of the fixture path until the fixtures are retired.

## Consequences

- Selection is fully deterministic and cannot miss a passage because of vocabulary.
- If a desk and sub-intent ever hold more than `max_knowledge_results` approved policies, the order by `source_id` decides; a keywords column would then be needed.
- Drafts and expired policies are never returned; a test covers both.
