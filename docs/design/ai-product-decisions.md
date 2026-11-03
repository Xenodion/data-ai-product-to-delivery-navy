# AI Product Decisions and Deliverable Alignment

Date: 3 November 2026. Status: shared product framing retained after audit; open business parameters and evidence are called out. Canonical names: [terminology](terminology.md). Target behavior: [workflow](copilot-workflow.md).

## 1. Decision

**GO to build and evaluate a complete demo; CONDITIONAL GO for a Keelpay pilot; no production expansion decision yet.** D-q4 is a Qualifier Model candidate supported by a synthetic benchmark, not evidence of full-product value. A strong fine-tuning result is not sufficient for product GO.

The economic alternative remains non-AI integration to attach merchant and transaction context. Present it as an option to validate, not a delivered project. Final model selection must compare with rules/classical ML and prompting; distinguish fine-tuning impact at the same model size from selection against a larger model that could serve as Drafter Model.

## 2. Decisions retained

| Topic | Position | Status / consequence |
|---|---|---|
| Shared product | Prepare and handle merchant tickets from receipt through human reply | Confirmed; one use case across both courses |
| Qualifier Model | Extract seven fields; no tool or desk choice by model | Confirmed; preserve historical artifact names |
| Routing Node | Deterministic Python; desk/priority/payment/draft are separate decisions | Confirmed; finalize table, state, tests in Feature 004 |
| Ambiguity | Block only the dependent decision; clarification is allowed | Confirmed; no global triage for every `UNDEFINED` |
| Human control | Targeted qualification when necessary; review every reply before send | Confirmed; ordinary tickets do not need two approvals |
| Urgency | Draft preparation allowed; surface priority and track handling | Principle agreed; exact signals/deadlines remain open |
| Demo queue | Visible wait and FIFO MUST; advanced urgency SHOULD | Confirmed; demo scope does not validate production safety |
| Interface | Two separate agent workspaces plus live Overview | Confirmed; usability effects still need testing |
| Prototype sequence | One local V0 baseline; one future V1 | Confirmed; rethink the full flow once, use English interface copy, preserve original ticket languages, and do not develop parallel mock-up variants |
| External services | Drafter/traces external only on non-critical synthetic demo data | Confirmed; fictional production data stays in Keelpay cloud |
| Promise | Reduce active time at constant quality; no established gain claim | Remove “twice as fast” |
| User research | No invented interviews/citations/timings as evidence | Fictional research content replaced with unattributed design feedback; actual desirability evidence remains open |
| Model selection | D-q4 measured candidate; prompting comparison outstanding | Do not claim all alternatives were beaten |
| Reroute | One automatic re-preparation after desk correction; second change to manual triage | Scope documented; test the integrated flow |
| Multi-intent | Qualification/triage; no automatic split | Current product scope; no implied schema change |

## 3. Four course MUSTs

Group by product capability, not microservice, within Assignment 3's four-MUST limit:

1. **Qualify and assign:** justified model choice, contract validation, deterministic decision table, targeted human resolution.
2. **Prepare a grounded reply:** merchant lookup, ambiguity resolution, retrieval, reply or clarification without invented facts.
3. **Enable human decisions:** qualification, final review, editing, sources, gates, history, and rerouting. Minimal workspace is MUST; visual refinements are SHOULD.
4. **Evaluate and observe:** reference cases, error/correction measures, traces, versions, and component disablement. Logs do not automatically become training labels.

Recalculate and justify RICE; do not copy old feature groupings. The eight candidates may include these capabilities, Overview refinements, advanced urgency, and two rejected ideas (autonomous send, ledger writes). Basic Overview remains a MUST for the educational demo; this does not assign it an artificial production economic benefit.

At least five WON'Ts: autonomous send; bank write/refund/unfreeze; automatic multi-intent split; external voice/chat; regulatory advice/decision; real data sent to external APIs. The synthetic demo exception is stated separately.

## 4. Expected effect and proof

| Level | Measure | Evidence still needed |
|---|---|---|
| Primary product | End-to-end active handling time, net of triage/corrections | Baseline, comparable tasks, actual human measurement |
| Secondary business | Correct first-pass desk assignment | Human oracle/fixtures and full Routing Node, not only intent mapping |
| Secondary business | Critical-case handling within business deadline | Defined deadline, critical recall, missed-urgent measurement |
| Guardrails | Constant QA, post-review serious errors, no cross-merchant leakage | QA rubric, counterfactual, suitable sampling |
| Component diagnostics | Extraction, valid outputs, silent errors, latency/cost | Prompted comparator and target-runtime benchmark |
| UX | Task success, selection errors, hesitation, time, send confirmation | Actual conversations and declared role-play tests |

Use the corrected sizing workbook's economic threshold under its assumptions; do not convert it to universal accuracy. Sets of 20/200 support contract checking and exploration; they cannot certify a rare event below 0.1%. Zero observed errors in a small test is not proof of zero risk.

## 5. Operating governance

- Head of Support owns rules, queues, handling thresholds, service quality, and operational disablement.
- Head of Compliance owns sensitive reply policy and business exposure; legal basis and retention remain proposals to verify, not certifications.
- NAVY owns contracts, tests, measurement, instrumentation, and recovery; a system error is not automatically the clicking Support Agent's fault.
- Support Agent decides on the ticket, corrects, checks facts, and validates the reply; no mandatory pre-intervention on standard cases.
- Disable assignment, drafting, and the whole system separately. Serious errors trigger an incident/review and restriction of the affected component; a single global rollback is insufficient.
- Unknown priority, model errors, and missing traces are explicit states; none removes a ticket. Manual degraded mode remains usable.

Plans must close critical signals, deadlines/hours, acknowledgement/escalation, QA rubric, rare-risk measurement, and retention by data type. Do not invent business values to fill templates.

## 6. Deliverable status

| Deliverable | Work to complete | Completion criterion |
|---|---|---|
| README/pitch | One scenario, three evidence levels, canonical component roles | No conflict or invented implementation status |
| Problem statement | As-is, persona/journey/stakeholders, alternatives, hypotheses, staged GO | Problem/alternative/tests describe same product |
| Sizing workbook | Reconciled sensitivity/comments/comparators, cash/amortization, demo/production costs | Formulas and assumptions reconcile; scenarios feasible |
| Investment memo | One page after workbook correction | Same figures, conditional pilot, no fabricated evidence |
| Product brief | Four MUSTs, recalculated RICE/MoSCoW, process/success/team decisions | Concise brief with detailed appendix, no fictional validation claim |
| Lean canvas | Align 14 blocks and provenance | No unearned savings, wrong generator, or unbuilt integration claim |
| Design feedback/research | Preserve design feedback and a protocol for real evidence | No fabricated research presented as proof |
| Prototype note | One V0 baseline; one planned V1 successor; no parallel variants | UI checks distinguished from user research |
| Governance | Dependency-aware blocking, ownership, data, rollback, evidence | One clear rule per decision and honest status |
| Product spec/evals | Align contract/states, 20 case expectations/provenance | Each expectation traceable; no absent DB/article assumed |
| Architecture | Components and human decision points | Target behavior plus implemented/simulated/to-build status |
| Future 05–08 deliverables | Plan metrics, A/B, operations, launch per available course brief | No invented results or missing session instructions |

Known course dates remain in source assignments; Assignment 3 is due 6 November 2026. Preserve actual member contributions and commits.

## 7. Spec Kit sequence

Feature 003 handles AI Product alignment. Other delivery lots are in `specs/roadmap.md`. Keep detailed flow in `copilot-workflow.md`, rather than maintaining competing copies in every plan. Each plan states which contracts it consumes and which requirements it implements. Plan-ready does not mean implemented. Prepare detailed technical plans only after the product decisions and AI Product deliverables are aligned.
