# Keelpay Governance

Reference: 3 November 2026. Responsibilities and rules describe the target product. Controls not yet implemented are requirements, not certified compliance.

## Session 1 — Six questions

| Question | Position and owner |
|---|---|
| AI Act risk | Working hypothesis: internal support copilot, outside credit scoring, decision-based onboarding, or automatic payment. Exact classification must be checked with Legal/DPO against intended use; a human in the loop alone does not determine classification. |
| Data and legal basis | Demo uses non-critical synthetic data. Production tickets/transactions may contain personal data; controller/processor roles, purposes, and legal bases must be documented. A B2B contract does not resolve every processing question. |
| Who is accountable? | Support owns quality, rules, queues, and operational rollback; Compliance owns sensitive policies/exposure; NAVY owns implementation and measurement. A Support Agent decides whether to send but is not solely responsible for system errors. |
| Prohibited actions | Autonomous send, ledger write, refund/unfreeze, regulatory decision, cross-merchant data mixing, unsupported claims. |
| Explainable to whom? | Support Agent: facts, sources, rules, open issues. Auditor: versions, actions, history. Merchant: human reply and route to clarification. |
| Unequal outcomes | Measure triage/wait/QA by language, case type, merchant tenure, and agent tenure; do not let average gains hide a degraded segment. |

Classification and obligations must be checked against the [AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689). [CNIL guidance](https://cnil.fr/fr/assurer-que-le-traitement-est-licite) requires a legal basis suited to processing purposes and conditions; none is declared established here.

## Session 2 — Error cost and decision

A wrong desk costs time; an unhandled urgent ticket or reply about the wrong payment may cause financial, legal, and reputational harm. Sizing error costs are assumptions, not observed penalties. Head of Compliance owns sensitive exposure; Head of Support owns service quality and interruption of affected functions.

Benchmark silent errors (wrong desk/reference under the scorer), errors after rules, serious errors sent to merchants, and their increment versus a control are four different measures. Average financial risk assumptions are not evidence. Rare serious errors need a defined denominator and a dedicated protocol; 20 or 200 cases cannot certify their rate.

## Session 3 — Data audit

| Question | Available data and limits |
|---|---|
| Provenance | Synthetic scenario cards/tickets; DeepSeek for train/validation, Xiaomi for tests per CSV; distinct readers/judges configured in the sub-project. Ledger/KB flow fixtures are a separate dataset. |
| Volume and labels | 1,922 train, 293 validation, 610 test_natural, 380 test_traps = 3,205 accepted, plus quarantines. Labels were generated and LLM-reviewed; this is not exhaustive human annotation. |
| Coverage | test_natural: FR 309, EN 291, other languages 10; payment_status 114, dispute 141, technical_api 144, compliance 114, OTHER 36, UNDEFINED 61. Synthetic mix, not a measure of Keelpay traffic. |
| Rights | No real customer ticket in the project. Production requires review of purposes, data-subject rights, and provider terms. Do not conflate anonymized, pseudonymized, and synthetic data. |
| Leakage | Deduplicated card pool followed by disjoint splits and configured reserves. The audit found no exact text duplicates across four splits; semantic similarity is not ruled out. Merchant isolation must be tested in the future backend. |
| Freshness | Dataset and rules are versioned. Changes to taxonomy, prompt, model, policy, or fixture require appropriate re-evaluation; synthetic tickets do not certify external payment rules. |

The tests include non-representative traps and languages. Pre-filter quotas do not guarantee twenty accepted examples per family; the dataset log flags nine families below twenty. Do not present a stress-set average as production performance.

**Purpose:** support assignment and replies only, not credit or merchant profiling. **Retention:** 90 days for audit logs is a proposal requiring confirmation by data type; demo state may reset under a test protocol; training corpus and human notes stay separate. Feedback does not automatically become a trusted training label.

**Location:** fictional production keeps models/data/traces in Keelpay cloud under the scenario's internal policy. The demo allows external Drafter Model API and Langfuse only for non-critical synthetic data. This exception never covers real tickets. Secrets stay server-side.

## Session 4 — Human decisions and recovery

| Step | Assurance level and rule |
|---|---|
| Qualifier Model | Reading assistance; seven fields and contract validation; no invented confidence |
| Routing Node | Deterministic Python, bounded L3 for supported intents; unknown/invalid intent creates a Re-router task while drafting continues |
| Lookup Node | Read-only, merchant-scoped; an incorrect lookup remains a real risk |
| Priority | Surface urgency while preparation continues; handling/escalation configured separately |
| Retrieval Node | Read-only approved sources; grounded facts or clarification; automated checks are imperfect |
| Drafter Model | L2; prepares factual, documentary, or clarification draft; automated checks are imperfect |
| Validator/send | Support Agent only; editing optional, checking required, unchanged draft needs confirmation |
| History | Automatic actor/version record; traceability is not a quality guarantee |

An absent/ambiguous payment reference blocks claims about that payment, not a known desk or a clarification. Unknown sentiment uses neutral tone. Unknown sub-intent blocks only its dependent procedure. Urgency alone never pauses draft preparation.

**Recovery:** first desk correction → recalculate context and draft; second → manual triage, no automatic loop. “Copilot off” leaves manual writing usable. Receipt and total age remain preserved.

**Separate rollback:** stop automatic assignment (suggestions/qualification), stop drafting (keep context plus human writing), or stop the whole copilot and use a manual queue. Head of Support triggers; NAVY executes; Compliance joins sensitive incidents. A serious incident triggers immediate review and tailored restriction, not just waiting for a weekly sample.

## Open settings and S5–S7

| Setting / evidence | Owner and closure criterion |
|---|---|
| Critical signals, deadlines, hours, escalation | Support + Compliance; tested configuration including missed urgencies |
| QA rubric and serious errors | Support/Compliance; events and denominators defined |
| Rare risk and A/B | NAVY; pre-registered protocol, appropriate sample size, segments |
| Retention/legal basis | DPO/Legal; decision by purpose and data category |
| Isolation and durable recovery | Tech lead; cross-merchant, reconnect, idempotency, and failure tests |

The demo requires FIFO and visible waiting time. Advanced urgency and multi-agent are SHOULD for demo implementation; this neither validates nor waives pilot safety requirements. Metrics, A/B, and operations deliverables will use available course instructions and observations actually collected.
