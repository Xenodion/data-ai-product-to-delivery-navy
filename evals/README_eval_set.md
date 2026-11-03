# NAVY Synthetic Acceptance Cases

`eval_set_v0.csv` contains 20 synthetic scenarios authored to check the product contract, not to estimate Qualifier Model, Routing Node, generation, or UX performance. `provenance=team_authored_synthetic` means both ticket and oracle are synthetic design data; they are not from customer interviews or independent annotation.

## Columns and interpretation

- `expected_*` describes the proposed reference outcome. The seven Qualifier Model fields retain the current schema values; these expectations do not rewrite historical benchmark predictions.
- `expected_desk` is the Routing Node decision, or `triage` when the product scope is missing/undecidable.
- `expected_payment_resolution` describes lookup dependency; missing ID does not invalidate a known desk.
- `expected_human_step` distinguishes required qualification from mandatory final review. Every send requires a Support Agent.
- `expected_draft_kind` describes the reply type allowed by available information; it does not mean draft quality was evaluated.
- `priority_attention` is an acceptance-case flag, independent of the contract priority field. It does not introduce a `critical` value.
- `source_ids` names intended synthetic fixtures; a source ID alone is not source content or proof of grounding.

The cases cover seven supported intents, `OTHER`/`UNDEFINED`, multiple transactions, missing/external IDs, multi-intent, urgency, sentiment neutrality, and taxonomy limits. Debatable expectations are scoped in notes. A business reviewer must approve the oracle before these are called “gold.”

## Exclusions and next step

This acceptance set does not evaluate Drafter Model fact-checking, actual source adequacy, or real backend isolation. Cases without authorized facts must lead to clarification, qualification, or manual handling. Before an integrated evaluation, create ledger/KB records for the named `source_ids`, check fixture consistency, version the data, and obtain an independent oracle review. Do not invent regulatory or banking authority to make a case pass.
