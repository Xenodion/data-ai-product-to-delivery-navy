# Langfuse prompt releases

The Qualifier and Drafter resolve prompts by a stable Langfuse name and label from `flow/config.toml`:

| Node | Langfuse name | Type | Runtime variables |
|---|---|---|---|
| Qualifier | `navy/qualifier` | text | `ticket` |
| Drafter | `navy/drafter` | chat | `desk`, `mode`, `language`, `qualifier_fields`, `evidence_facts`, `allowed_source_ids`, `ticket_text` |

Initial version 1 of both resources was published and verified under the `production` label on 9 November 2026. Development can use a separate label by changing configuration. Langfuse labels are mutable pointers to immutable prompt versions; traces record the selected name, label, version and whether the local fallback was used.

Prompt templates are fetched through the Langfuse SDK cache. If no prompt is cached and Langfuse is unavailable or unconfigured, the SDK's fallback keeps the local flow usable. Such runs are explicitly recorded as `local-fallback` and are not a Langfuse prompt release. Prompt inputs and outputs remain excluded from Langfuse observation capture; the ticket value is only compiled locally into the retrieved template and sent to the model endpoint.

The published Qualifier content comes from `ml/qualifier/src/prompt.py`, followed by `{{ticket}}`. The published Drafter content matches the two-message `DRAFTER_FALLBACK_PROMPT` in `flow/drafter.py`. A future prompt edit must create a new Langfuse version, run the frozen staging evaluation, then move the deployment label; changing the model settings in `flow/config.toml` alone does not promote a prompt.

The historical unconstrained D-q4 model benchmark remains separate from runtime scoring: constrained structured output changes the evaluated system. See [`synthetic-context-and-e2e-evaluation-plan.md`](synthetic-context-and-e2e-evaluation-plan.md) for full-flow regression requirements.
