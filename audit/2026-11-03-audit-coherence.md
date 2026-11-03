# NAVY / Keelpay Coherence Audit

Date: 3 November 2026. Scope: current local workspace, not only committed files. This audit compared course briefs, product documents, governance, sizing formulas, model schema/labels/scorer, dataset/config/results, local prototypes, and available demo material. The audit is a diagnostic; current target behavior is maintained in `spec.md` and `docs/design/`.

## Executive result

The two courses can describe one coherent product: AI Product decides whether a support copilot is worth piloting; LLMOps builds, evaluates, serves, and observes its language-model component in a complete demo. The core issue was not incompatible objectives but version drift that conflated fictional scenario inputs, economic assumptions, model results, simulated behavior, and human validation.

The active reference now names the **Qualifier Model**, deterministic Python **Routing Node**, **Lookup Node**, **Retrieval Node**, **Drafter Model**, human **Support Agent**, Python **Demo Injector**, and **Langfuse**. It defines three workspaces, dependency-scoped clarification, FIFO/wait, human-controlled sends, and a synthetic-only external-service exception for the demo.

**Decision:** GO to build/evaluate the synthetic demo; CONDITIONAL GO for a Keelpay pilot; no production deployment or expansion is approved. Product-level time/quality/safety evidence remains outstanding.

## User decisions incorporated

1. Provisional/fictitious user-research material is not treated as measured evidence. Design feedback informs the product; usability and time outcomes remain open.
2. The shared LLMOps result is expected to include a deployable demo and monitoring such as Langfuse, although no further formal written course brief was located in the repository.
3. Target demo is end-to-end: compact CPU Qualifier Model, deterministic Routing Node, synthetic lookup/KB, drafting, human decisions, functional front end, and Python ticket injector. Static hosting plus Cloud Run is the intended topology; exact front host and runtime choices remain open.
4. External Drafter Model API and external traces are permitted only for non-critical synthetic demo data. Fictional production keeps real tickets/models/traces in Keelpay cloud.
5. The model extracts seven fields; Python decides routing. Missing/ambiguous fields block only dependent actions. Unknown sentiment does not block routing.
6. Three tabs: Overview, Qualification & Routing, Replies to Review. Clicking a human node opens the correct workspace/task.
7. Waiting time and oldest-first FIFO are demo MUSTs; explicit urgent-first mode, advanced urgency, and multi-agent are SHOULD. This does not waive production urgency requirements.

## Evidence checked

Reproducible command: `node audit/reproduce.cjs`. It checks accepted dataset labels against the current contract, prediction alignment and key test metrics, exact cross-split text duplicates, and selected financial values.

Historical benchmark facts: 1,922 train + 293 validation + 610 natural test + 380 trap test = 3,205 accepted tickets. All labels pass the reproduced contract check; no exact text duplicates were found across these splits. Semantic similarity is not ruled out. On `test_natural`, D-q4 produced 595/610 desk matches (97.54%), 4/610 silent errors (0.656%), 1/167 wrong desk among urgent tickets (0.599%), and 597/610 schema-valid outputs (97.87%). B2 produced 207/610 silent errors (33.93%) and 11/167 urgent wrong desks (6.59%). These are component/scorer results, not full-flow or customer outcomes.

The historical scorer derives desk from intent and does not implement all proposed routing/priority/payment rules. The proposed prior blanket exclusion of every sentinel/high-priority case was not a valid product decision and has been superseded by dependency-scoped decisions. Preserve historical scores; evaluate the Routing Node separately.

The corrected workbook was exported, re-imported, checked across all seven sheets, and rendered for visual review. Formula-error scan returned zero. Verified outputs are base annualized net €194,297.65, weighted EV €214,308.07, low −€78,443.95, high €703,462.12, year-one base cash €137,631 (memo rounded), steady-state base €355,476, weighted do-nothing EV €98,334, and weighted next-best EV €100,843.12. The memo uses these outputs. They are still model outputs from assumptions, not measured economic outcomes or forecasts. OOXML comparison found that export removed `calcChain.xml` and the two document-property parts (`core.xml`, `app.xml`); the seven sheets and formulas remain, but original workbook metadata did not. The untouched original is preserved in the ignored local workbench.

Other limits: no training run, Python tests, real browser test, Vertex registry query, billing inspection, or live endpoint check was performed for this audit. No exact text duplicates does not prove semantic independence. Existing screenshots/browser checks do not establish usability. Future assignment briefs and unwritten instructor requirements cannot be certified.

## Major contradictions found and resolution

| Finding | Earlier conflict | Current resolution / remaining work |
|---|---|---|
| Research evidence | Synthetic interview dates, quotes, task times, or user GO could be read as observed | Current research page contains design feedback and a protocol; actual observations remain open |
| Demo vs component | Product docs implied lookup/KB/drafter/logging were already integrated | Current docs label mock-ups historical and integrated backend as to build |
| Deployment/monitoring | LLMOps endpoint/deployment scope was unclear | User confirmed a deployed functional demo and Langfuse/full-flow observability are wanted; exact implementation remains a future feature |
| External services | Blanket production ban contradicted desired demo Drafter Model | Exception restricted to synthetic non-critical demo data, including traces; real tickets stay in fictional Keelpay cloud |
| Model/routing naming | “Router” could mean the fine-tuned model or product routing logic | Canonical names distinguish Qualifier Model from deterministic Routing Node; historical IDs remain intact |
| Contract/schema | Old root spec used desk-valued intents, `critical`, `OTHER` currency, `tx_id`, and noncanonical IDs | Root spec now uses exact existing seven-string-field schema and separate business decisions |
| Absence/ambiguity | Missing ID was treated as `UNDEFINED`; every sentinel was sent to triage | Empty string means absent, `UNDEFINED` means undecidable; block only the dependent action |
| Urgent cases | Old prototype/spec required human approval before draft | Priority is visible and independent; draft may proceed; every reply still gets final human review |
| Scorer vs product | Historical `is_routed` metric was treated as production routing coverage | README/spec distinguish the historical scorer from the unbuilt Routing Node evaluation |
| Confidence | UI/docs requested confidence thresholds without a schema field | No confidence score is claimed; contract validation and explicit uncertainty reasons are used |
| Model comparison | Prompted alternative was missing while superiority language was used | D-q4 remains best measured among executed systems; prompted comparison is outstanding |
| Test-set selection | Selection/confirmation chronology and holdout independence were unclear | Preserve historical chronology; do not claim pre-registration or independent confirmation without evidence |
| Error thresholds | Silent extraction errors, serious customer errors, incremental risk were conflated | Define separately, with denominators; rare-risk protocol remains open |
| Small test sets | 20/200 cases were used to imply <0.1% risk assurance | S3 checks contract; ~200 explores; rare-risk evidence needs a separate protocol/larger design |
| Prototype behavior | The local baseline's urgency gate and memory differ from target | One V0 baseline is retained; the earlier sketch is provenance only. One English-language V1 successor will implement the three-tab target with durable backend state and real events |
| Demo state | UI animation/queue could imply backend functionality | Architecture makes backend operational state authoritative; Langfuse is observability only |

## Current artifacts and outstanding gates

Created/aligned: canonical terminology, root product spec, target architecture, workflow/UX, AI Product decision reference, product brief appendix, English course-facing framing, governance, user-research protocol/design feedback, single V0/one-successor version rule, revised 20-case CSV, corrected workbook, reconciled one-page memo, and Feature 004 Routing Node spec/plan/contracts/cases.

Not complete: full source fixture set and independent case-oracle review; actual usability evidence; approval of demo-specific policy values and implementation of Feature 004; later course deliverables whose briefs are not yet available. The assignment matrix, claims register, validation record, and shared Spec Kit plans are versioned under `specs/`.

The 20-case CSV names intended source IDs, but those ledger/KB records are not yet present. It is a proposed contract/flow case list, not a verified gold set, and currently cannot validate grounded generation. See `evals/README_eval_set.md`.

## Authority order

1. Original course instructions govern course requirements and remain intact.
2. User-confirmed product decisions govern this authorized work without implying team/instructor ratification.
3. `docs/design/terminology.md`, `spec.md`, and `docs/design/copilot-workflow.md` define the current shared product target.
4. `finetuned_llm_classifier/src/dataset_build/schema.py` and its label definitions govern the current Qualifier Model contract.
5. `02_sizing.xlsx` is the economic calculation source; memo values must be regenerated only after workbook verification.
6. Dated CSVs, predictions, and model reports remain historical evidence with their original scope.
