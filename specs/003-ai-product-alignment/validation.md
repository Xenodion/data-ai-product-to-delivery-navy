# Alignment Validation

Date: 3 November 2026. This is a documentary and artifact audit, not a deployment, usability study, or instructor approval.

## Checks completed

- Re-read the project narrative, governance, research protocol, current product specification, workflow, architecture, prototype status, evaluation notes, course matrix, and claims register.
- Reconciled `02_investment_memo.md` to the corrected `02_sizing.xlsx` export. Re-imported the root workbook, confirmed all seven sheets, scanned for formula errors (zero hits), and rendered all sheets for visual inspection. OOXML comparison found `calcChain.xml` and the `core.xml`/`app.xml` document-property parts were not retained; no sheet or formula loss was found, but original workbook metadata is absent from the exported copy. The untouched source backup remains in the ignored workbench.
- Confirmed the memo opens with the decision and explicitly answers the four assignment questions (“How much?”, “How sure?”, “What if we’re wrong?”, “Compared to what?”), with a final build/buy/orchestrate line; current Markdown body is about 470 whitespace-separated tokens.
- Ran `node audit/reproduce.cjs`: 3,205 accepted historical labels, zero invalid targets, no exact cross-split text duplicates, and historical model results reproduced. The script refreshes `audit/2026-11-03-evidence.json`; its financial block is a snapshot manually reconciled to the export, not a workbook parser.
- Checked 73 local Markdown links across active project and Spec Kit documents; no missing links.
- Preserved historical model outcomes, original assignment documents, and the single V0 baseline. Archived the older Paylio specification and marked the V0 pre-draft urgency gate as legacy behavior that conflicts with the current target. The earlier sketch is retained as provenance only, not an alternate design.
- Current project-authored documentation and plans are in English. The V0 and planned V1 interfaces use English copy; synthetic ticket messages and example replies retain their authored language.

## FR / SC coverage

| Requirement | Status | Evidence / limitation |
|---|---|---|
| FR-001 — canonical terminology | Pass | Current references use Qualifier Model, deterministic Routing Node, and Support Agent; legacy identifiers are explicitly historical. |
| FR-002 — benchmark/demo/production separation | Pass | README, root spec, architecture, workflow, and governance distinguish all three. |
| FR-003 — ownership and recovery | Pass | Governance names proposed Support, Compliance, and NAVY responsibilities and disablement/recovery; these are target controls, not certified operations. |
| FR-004 — research honesty and protocol | Pass | No fabricated observations or timing are claimed; `03_user_research.md` gives the planned method. Actual conversations remain outstanding. |
| FR-005 — preserve benchmark and disclose missing comparator | Pass | Historical results remain intact; prompted comparison is still open. |
| FR-006 — aligned workbook/memo and cost/cash distinctions | Pass | Memo values reconcile to exported workbook; budget inputs remain assumptions, not vendor quotes. |
| FR-007 — brief MUST/WON'T and RICE alignment | Pass | Counts and candidate ranking recorded in product brief and annex. |
| FR-008 — twenty S3 cases and provenance/context | Partial | Twenty proposed cases exist; ledger/knowledge fixtures and independent oracle review are missing. They are not a gold set. |
| FR-009 — distinct success measures and rare-risk limits | Pass | Product, component, UX, safety, and economic evidence are separated; small-case limits are explicit. |
| FR-010 — course requirements mapped to action/status | Partial | Available requirements are in the matrix; press release and future assignment deliverables remain open. |
| FR-011 — honest implementation status | Pass | Demo, deployment, research, and production capabilities are explicitly marked as targets or outstanding. |
| FR-012 — preserve sources and prototype history | Pass | Original course files and one V0 baseline remain; its predecessor is marked provenance-only, and an unrelated prior Paylio spec is archived. |
| FR-013 — plans aligned to trade-offs and verifiable outcomes | Partial | Feature 004 spec/plan/contracts/cases and roadmap are prepared; policy approval, implementation, later briefs, and downstream runtime specs remain open. |
| SC-001 — eight structural decisions aligned or conflicts disclosed | Pass | Current target is consistent; the V0 baseline's legacy urgency behavior is explicitly disclosed. |
| SC-002 — no unsupported user or deployment evidence | Pass | Research remains a protocol; no current deployed endpoint is claimed. |
| SC-003 — memo/workbook reconciliation | Pass | Verified export outputs match the memo within rounding. |
| SC-004 — every case has available provenance/context | Open | Source fixtures are absent, so groundedness cannot yet be evaluated. |
| SC-005 — assignment coverage | Partial | The matrix records response/status/action for available briefs; several course deliverables remain open. |
| SC-006 — recommendation and evidence gaps clear | Pass | GO for synthetic demo, conditional pilot, and no production approval are stated consistently. |

## Verified sizing outputs

| Output | Verified value |
|---|---:|
| Low / Base / High annualized net | −€78,443.95 / €194,297.65 / €703,462.12 |
| Weighted project EV | €214,308.07 |
| Weighted do-nothing EV | €98,334.00 |
| Weighted next-best EV | €100,843.12 |
| Base year-one cash illustration | €137,631 (rounded) |
| Base steady-state annual net | €355,476 (rounded) |
| Zero-net / beat next-best / beat do-nothing time-savings thresholds | 5.93% / 13.32% / 12.79% |

These are outputs of assumption-based sizing, not measured outcomes or forecasts. The reproducer's financial cross-checks use the verified exported workbook values; the workbook remains the calculation source.

## Open evidence and next actions

1. Create synthetic ledger and knowledge fixtures for each cited case, then have a second reviewer check the oracle.
2. Complete the planned user conversations and task observations; keep their actual findings and limitations separate from current design feedback.
3. Have Support/Compliance approve the demo `PolicyConfig`, then implement and verify Feature 004 against all 26 cases.
4. Decide deployment details for the single English-language V1 front end, implement it against backend state, and deploy only synthetic demo data before claiming a live demo.
5. Produce later course deliverables only after their briefs are available; collect actual baselines, value, usability, and safety evidence before changing the pilot recommendation.

The fuller audit and reproduced component results are in [the coherence audit](../../audit/2026-11-03-audit-coherence.md) and [machine-readable evidence](../../audit/2026-11-03-evidence.json).
