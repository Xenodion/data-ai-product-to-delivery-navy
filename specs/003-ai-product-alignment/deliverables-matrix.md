# Course Requirement and Deliverable Matrix

Sources reviewed: the supplied Assignment 1, 2, and 3 Word briefs, the shared project-proposals document, and Vincent's oral clarification of the LLMOps demo target. Original course files are preserved unchanged.

Status means documentary coverage in this workspace, not instructor approval or implementation.

| Source | Requirement | Current response | Status / next action |
|---|---|---|---|
| Assignment 1 | Named team, company, support-agent job, trust by step, forbidden action | `README.md`, `00_pitch.md`, `governance.md` | Covered; confirm final team commits/sign-off |
| Assignment 1 | Quantified problem; every number has a type/source | `01_problem_statement.md`, `02_sizing.xlsx` | Covered as scenario input/assumption/measurement distinctions; operational baseline remains unmeasured |
| Assignment 1 | Problem tree/5 Whys and whether fix is AI/rules/process/docs | `01_problem_statement.md` | Covered as hypotheses; validate against actual support practice |
| Assignment 1 | AI selection questions and alternatives below chosen rung | `01_problem_statement.md`, `docs/design/product-brief-annex.md` | Covered; prompted comparator still outstanding |
| Assignment 1 | Four selection criteria and testable hypotheses by session | `01_problem_statement.md` | Partial; tie final hypotheses to actual course session plan |
| Assignment 1 | Press release with launch quote and do-nothing baseline | Future press release / `02_sizing.xlsx` | Open; no quote or launch outcome should be fabricated; use the reconciled do-nothing baseline |
| Assignment 1 | Provisional six-question governance, open checks, two-member commits | `governance.md` | Content covered; member commits are not certified by this audit |
| Assignment 2 | Low/Base/High, source type/note for each input; quarterly adoption below 100% | `02_sizing.xlsx` | Workbook corrected, exported, re-imported, rendered, and formula-error checked; assumptions remain unverified |
| Assignment 2 | Seven cost lines, error probability × cost, refreshed prices | `02_sizing.xlsx` | Partial; price/hosting inputs are explicit assumptions, not provider quotes |
| Assignment 2 | Three weighted scenarios; do-nothing; named next-best hurdle | Workbook and `02_investment_memo.md` | Memo reconciles to verified export; economic assumptions are not measured |
| Assignment 2 | Sensitivity flip point named in memo and measured in S4 | Memo, sizing, future S4 protocol | Partial; numeric threshold is assumption-bound; S4 measurement is open |
| Assignment 2 | Build/buy/orchestrate ten-question score and break-even | Workbook and memo | Workbook logic and all seven exported sheets reviewed; market quotes and vendor fit remain open |
| Assignment 2 | One-page memo; first line decision; four CFO questions; build/buy line | `02_investment_memo.md` | Content aligned; verify final page length after render if DOCX is later created |
| Assignment 2 | Governance cost-of-error owner and risk type | `governance.md` | Covered; actual owners are proposed scenario roles |
| Assignment 3 | As-is process with minutes/error/source type, two pain steps | `01_problem_statement.md`, appendix | Partial; minutes/error rates are assumptions; actual baseline collection is open |
| Assignment 3 | Automate/augment/human, trust, metric, recovery path per step | Brief, workflow, governance | Covered at design level; routing/runtime implementation remains |
| Assignment 3 | Eight candidates, RICE, ≤4 MUST, ≥5 WON'T | Product appendix | Covered; inputs/effort/reach are judgments, not observed estimates |
| Assignment 3 | Model rung by component and why lower rung fails | Product appendix | Covered; model-choice comparison remains incomplete |
| Assignment 3 | Data audit: provenance, volume, coverage, rights, leakage, freshness; purpose, retention, isolation/gaps | `governance.md` | Covered as current limits; DPO/legal settings remain open |
| Assignment 3 | One-sentence success criterion: metric, threshold, guardrail, data, date | `03_product_brief.md` / future validation plan | Partial; final metric/date must follow corrected economic hurdle and available delivery schedule |
| Assignment 3 | One-page brief and AI Lean Canvas | `03_product_brief.md`, `03_ai_lean_canvas.md` | Content covered; canvas length/layout should be checked against the source requirement |
| Assignment 3 | Three 20-minute conversations, one prototype, two user tasks | `03_user_research.md`, `03_prototype_link.md` | Protocol/design material present; actual sessions and outcomes remain open |
| Assignment 3 | Brief v2: what users changed/could not decide with evidence | `03_product_brief.md`, research note | Partial; design decisions are recorded, observed evidence is not claimed |
| Assignment 3 | `spec.md` and 20 labelled cases with expected output, evidence, handover, segment, origin | Root `spec.md`, `evals/eval_set_v0.csv`, eval README | Partial; 20 scenarios exist but named synthetic ledger/KB fixtures and independent oracle review remain |
| Shared proposal/syllabus | Decode architecture, workflow, trust, tools, human points | `04_architecture.md`, workflow | Covered as target, not as delivered integration |
| Shared proposal/syllabus | Three business metrics; A/B sample size; adverse effects/monitoring; technical spec/rollback | Future deliverables 05–08, `governance.md` | Open; use actual future assignment briefs before inventing detailed requirements/results |
| User-confirmed LLMOps scope (oral) | Deployable end-to-end demo, CPU compact model, frontend, external synthetic-only Drafter Model, Python injector, Langfuse | `spec.md`, `04_architecture.md`, workflow | Agreed target; all deployment/runtime components remain to build and verify |

## Structural decision coverage

| Decision | Authoritative reference | Main affected deliverables |
|---|---|---|
| Qualifier Model extracts; Routing Node decides deterministically | `docs/design/terminology.md`, root `spec.md` | README, pitch, problem, brief, canvas, governance, LLMOps README |
| Missing/ambiguous fields block only dependent steps | `docs/design/copilot-workflow.md` | README, brief, governance, root spec, evaluation cases |
| Every reply has human review; urgency alone does not block drafting | Root `spec.md`, workflow | Pitch, problem, brief, governance, prototypes, evaluation cases |
| Three distinct tabs share actual backend state; human nodes navigate to tasks | Workflow, architecture | README, brief, prototype note, future interface features |
| Visible wait and oldest-first FIFO; urgent-first explicit if implemented | Workflow | Brief, prototype note, architecture, live Overview feature |
| External services only receive non-critical synthetic demo data | Root spec, governance | README, pitch, memo, canvas, architecture/deployment plan |
| Benchmark, demo, and production are separate evidence levels | README, root spec | Pitch, problem, memo, brief, governance, final recommendation |
| Prototype/deployment/research not described as delivered/measured until verified | Claims register, audit | All current status statements and future course deliverables |
