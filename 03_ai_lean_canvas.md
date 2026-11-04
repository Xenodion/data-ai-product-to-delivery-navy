# 03 — Keelpay AI Lean Canvas

Reference: 3 November 2026. Economic figures are sizing assumptions; extraction results are from a synthetic benchmark; target behavior is not deployed capability.

| Block | Position |
|---|---|
| 1. Problem | Active time spent reading/assigning and searching/drafting; wrong desk or payment; overlooked urgency. |
| 2. Users | Support Agents across payments/disputes/technical/compliance; support managers; merchants receiving human-reviewed replies. |
| 3. Value proposition | A qualified case and verifiable reply to reduce active work at constant quality without autonomous sending. |
| 4. Solution | Four MUSTs: qualification/assignment; grounded context/reply; human decision/history; evaluation/observability. |
| 5. Channel | Target agent workspace: Overview, Re-router, and Validator; the original V0 mock-up is available, while the integrated demo remains to build. |
| 6. Value | Savings are hypothetical net of error, adoption, and operating costs; see [memo](02_investment_memo.md) and [sizing](02_sizing.xlsx). Full-product gain is not measured by extraction. |
| 7. Costs | Integration, evaluation, human quality ownership, monitoring/hosting, reevaluation, variable usage, and errors. Year-one cash differs from amortized cost; external demo cost differs from private production scenario. |
| 8. Main metric | End-to-end active handling time at constant QA; initial desk and critical-case handling are secondary measures; serious errors and segments are guardrails. |
| 9. Advantage | In production: access to ledger, merchant context, and policy within approved boundaries. Our synthetic dataset and unbuilt integrations are not an established competitive moat. |
| 10. Data | 3,205 accepted synthetic tickets split 1,922/293/610/380; generated/reviewed labels differ from ledger/KB fixtures and the twenty product cases. |
| 11. Models | Qualifier Model D-q4 is a measured candidate; Routing Node, Lookup Node, and Retrieval Node are deterministic; Drafter Model is prompted with sources. Prompting comparison is incomplete. |
| 12. Evaluation | Preserve historical results; next evaluate rules and full flow; S3 twenty-case contract check, product study, and rare-risk protocol are distinct. |
| 13. Human control | Re-router only when the desk is unclear or wrong; Validator checks each reply; missing payment may lead to clarification; urgency does not prevent preparation. |
| 14. Risks/governance | No autonomous send or financial action; merchant isolation and supported facts; separate disablement of assignment/drafting/all; see [governance](governance.md). |

**Decision:** GO for demo/evaluation; conditional pilot; no production approval. External Drafter Model API and traces only for non-critical synthetic demo data; fictional production stays within Keelpay cloud. FIFO/wait are demo MUST; advanced urgency is SHOULD; production safety still needs validation.
