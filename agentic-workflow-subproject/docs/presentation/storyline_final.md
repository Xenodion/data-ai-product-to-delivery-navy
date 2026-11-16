# Final oral: storyline and slide content

Status: **final content v1, 16 November 2026.** Merged from four independent drafts kept in this folder for reference (`storyline_v1.md` to `storyline_v4.md`, constraints in `brief.md`). This file is the one the deck is built from. Paths starting with `sub/` are in `agentic-workflow-subproject/`.

## 0. Rules for every slide (read before touching the deck)

The deck must look like a team presenting its work, not like generated content. Anti-patterns to avoid:

**Hierarchy**
1. **One title per slide at most.** No subtitle, no small label above the title, no sub-sub-title, no "section · topic" kicker. A divider carries the section name only.
2. **Size follows importance.** The main message (the sentence or the chart) is the largest element on the slide. Section names, labels, sources and page numbers are the smallest. Never a decorative label, a number or a section name bigger than the content that matters.
3. **One idea per slide.** If a slide needs two titles, it is two slides or one cut.

**Text**
4. At most about 25 words of text on a content slide, chart labels excluded. Speaker lines stay in the notes, never on the slide.
5. Sentences, not bullet lists. A list, if unavoidable, has 3 items at most.
6. No KPI tiles, big-number cards or number walls. A number appears only inside a sentence or a chart that explains it.
7. Plain words. No "leverage", "seamless", "robust", "cutting-edge", "unlock", "game-changer", "key takeaways", "why it matters", no rhetorical questions, no slogans, no punchline built with a dash.
8. Exact status words: "built", "designed", "measured", "assumption". Nothing claimed that the repository does not show.

**Visuals**
9. Every content slide has one visual that explains itself: a chart, a screenshot or a simple diagram. If it needs a paragraph of legend, redraw it.
10. Charts: one highlight colour, the rest grey; labels written on the data instead of a legend; axis titles in plain words with units; no 3D, no pie, no gradient; source in small type at the bottom.
11. One colour code for the whole deck, and the same colour always means the same thing (model, rule, person; passed, not passed).
12. Screenshots cropped to the part that matters, readable from the back of the room, at most one callout.
13. No decoration: no emojis, no icons used as ornaments, no drop shadows, no glow, no glass effect, no boxes around everything, no card inside a card.
14. One grid, one alignment, generous white space. Same unit and rounding everywhere (silent errors per 100 tickets, euros per month).

**Talk**
15. Sober tone: we present work and decisions, we do not sell. Limits and failed gates are said plainly, once, without apology.

## 1. The story in five lines

1. **Context.** Keelpay is a fictional B2B payments company. Its support agents answer 36,000 merchant tickets a month by hand, and one ticket in seven first lands in the wrong desk.
2. **Framing.** Before building, we priced the project against cheaper options and wrote the checks that would stop it: it is worth it only above about 13 % of handling time saved, and the model is judged first on errors nobody flags.
3. **Workflow.** We built a fixed workflow, not an agent: a fine-tuned small model reads the ticket, rules route it, read-only tools fetch facts, a second model drafts, and a person approves every send.
4. **Model, deployment, monitoring.** The reading model was fine-tuned as a Kubeflow pipeline on Vertex AI, compared with four simpler systems, compressed to run on a CPU, registered, served and traced with Langfuse. Rules around both models stop what they get wrong.
5. **Next.** We stop at a deployed MVP on synthetic data. The model gate is passed; the product gates (time saved at constant quality) are not measured yet and decide any pilot.

## 2. Slides

Progress bar on every slide after the index: Context · Framing · Workflow · Model · Guardrails · Deployment · Monitoring · Next. Dividers: section name only, 3 s.

| # | Slide | Time |
|---|---|---|
| 0 | Cover | 5 s |
| 1 | Index and team | 10 s |
| 2 | Context | 40 s |
| 3 | Framing: is it worth building | 30 s |
| 4 | Framing: what we measure, the gates | 35 s |
| 5 | The workflow | 45 s |
| 6 | The interface | 20 s |
| 7 | The model: input and output | 25 s |
| 8 | The training data | 30 s |
| 9 | Fine-tuning on Kubeflow | 50 s |
| 10 | Results against simpler systems | 40 s |
| 11 | The trade-off that chose the served model | 30 s |
| 12 | Guardrails | 45 s |
| 13 | Registry and endpoint | 35 s |
| 14 | Monitoring with Langfuse | 35 s |
| 15 | Where we stop, what comes next | 40 s |
| 16 | Demo video | 45-60 s |
| | 8 dividers | 24 s |
| | **Total** | **about 9 min 30** |

If it runs long: shorten the demo to 30 s and slide 8 to its first sentence. Do not cut slides 4, 12 or 15.

---

### 0 · Cover
- **On slide:** "Keelpay support copilot" and one line: "Reading, routing and drafting merchant tickets, with a person sending every reply." Team NAVY, course, date.
- **Visual:** none.

### 1 · Index and team
- **On slide:** the eight section names (they become the progress bar) and the four names: Alexandre Waerniers, Vincent Lamy, Nahel Bachiri, Yoni Mahieddine (`README.md`).
- **Say:** "The model, its guardrails, its deployment and its monitoring are parts 4 to 7. A video of the application closes the talk."

---
*Divider · Context*

### 2 · Context
- **On slide:** "Keelpay, a fictional B2B payments company: 2,500 merchants send 36,000 support tickets a month, in French and English. One ticket in seven first lands in the wrong desk."
- **Visual:** above, a real-looking ticket in French, three lines (from `sub/data/dataset/train.csv`). Below, one horizontal bar = the handling time of a ticket: read and route 15 %, find the payment and write 45 %, check and send 40 %. The first two parts coloured (what a copilot can help with). Small marker "1 in 7 to the wrong desk" on the first part.
- **Say:** the scenario comes from the AI Product course; we act as the product team. The users are support agents in four desks: payments, disputes, technical, compliance. These figures are the scenario's data, not our measurements.
- **Sources:** `README.md` "Shared scenario", `01_problem_statement.md` §1. **Material:** chart to make.

---
*Divider · Framing*

### 3 · Is it worth building
- **On slide:** "The copilot beats a simple rule-based option only if agents save more than 13 % of their handling time. Our base assumption is 20 %; nothing proves it yet."
- **Visual:** line chart, x = share of handling time saved (10 to 30 %), y = net value per year: 55 k€ at 10 %, 123 k€ at 15 %, 191 k€ at 20 %, 259 k€ at 25 %, 326 k€ at 30 %. Horizontal line at about 100 k€ "rules only, no AI". Vertical markers at 13.3 % and at 20.3 % "base assumption".
- **Say:** we built a sizing with three scenarios and two alternatives (do nothing, rules only). The low case loses money. The decision was "go to build and measure a demo, conditional go for a pilot". This threshold is why every later step measures something.
- **Sources:** `02_sizing.xlsx` `Decision!C32:C36`, `D23`, `D57`; `02_investment_memo.md`. **Material:** chart to make.

### 4 · What we measure, and the gates
- **On slide:** "A ticket can end three ways. The one we count first: sent to a desk with a wrong desk or a wrong payment reference, and nothing says so."
- **Visual, left:** one ticket splitting into three outcomes: right / handed to a person (a few minutes, no damage) / silent error (the draft is built on it; it can reach the merchant). **Right:** a short ladder of the gates fixed before building, each with a mark: dataset frozen ✓ · cheap baselines first ✓ · fine-tuned model must beat the best baseline ✓ · no urgent ticket in a wrong desk ✗ (1 of 167) · time saved at constant quality: to measure.
- **Say:** accuracy alone would have hidden the problem: the classical baseline sends 92 % of tickets to the right desk and still gets one payment reference in three wrong. The model is told to answer "undefined" rather than guess, so we always read silent errors together with the share handed to a person. Settings were chosen on validation; the test sets were read once. A failed gate is shown as failed.
- **Sources:** `sub/docs/scoring_protocol.md` §2, §4, §5, §8; `sub/docs/roadmap.md`. **Material:** diagram to make.

---
*Divider · Workflow*

### 5 · The workflow
- **On slide:** "A fixed path, not an agent. Two models read and write, rules decide and check, a person approves every send."
- **Visual:** the flow redrawn with only the nodes that run (`sub/flow/langgraph_app.py`): ticket → Qualifier (fine-tuned) → field check → routing → context plan → ledger and knowledge search (read-only) → evidence gate → Drafter → policy check → Validator (person) → final check and simulated send. Side exit to the Re-router (person) for unclear, invalid or sensitive tickets. Three colours: model, rule, person. Judge, redraft and override switch are not drawn (designed, not built).
- **Say:** no model chooses a tool or the next step, so the cost per ticket is bounded and every step can be explained. LangGraph keeps a checkpoint so a ticket waits for the person and resumes. The Qualifier runs locally on CPU; the Drafter is an external model, allowed only because demo data is synthetic. Nothing is sent, refunded or written to the ledger by the system.
- **Sources:** `04_architecture.md` §1, `sub/flow/config.toml`. **Material:** diagram to redraw from `sub/docs/design/flow-v2/flow_v2.svg`.

### 6 · The interface
- **On slide:** "The agent's screen: the ticket, the draft with its sources, the actions. Nothing is sent without a click."
- **Visual:** screenshot of the Workspace on a ticket with a grounded draft: queue, draft with sources, Approve / Send to re-routing / Close buttons, merchant history.
- **Say:** a FastAPI service runs the graph and serves this front end; the Dashboard shows the flow and queues from the same events. You will see it move in the video at the end.
- **Material:** screenshot to capture (`sub/flow/deploy/demo.ps1 -Inject 6`), after the front-end work is committed.

---
*Divider · Model*

### 7 · The model: one ticket in, seven fields out
- **On slide:** "It returns one strict JSON with closed values. When it cannot tell, it answers UNDEFINED and a person takes the ticket."
- **Visual:** left the French SEPA ticket ("virement de 12 500 €… ref: TX-994821… C'est urgent"), right its JSON (`intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`). Below, a smaller pair with an ambiguous id and `"UNDEFINED"`.
- **Say:** four intents map to the four desks, four sub-intents each, plus `OTHER` and `UNDEFINED`. An output that breaks the contract goes to a person. The same instruction is used in training, evaluation and serving.
- **Sources:** `sub/initial_brief.md` §3, `sub/ml/qualifier/src/dataset_build/schema.py`, `sub/ml/qualifier/src/prompt.py`; the `UNDEFINED` example from `sub/data/dataset/test_traps.csv`. **Material:** layout to make.

### 8 · The training data
- **On slide:** "No real tickets exist, so we generated 3,205. A scenario card fixes the label, a model writes only the text, two blind readers check it, and a failing ticket is set aside, never repaired."
- **Visual:** funnel per split, generated → accepted: train 2,657 → 1,922 · validation 450 → 293 · test 950 → 610 · traps 645 → 380.
- **Say:** about 3 dollars of API calls; about a third rejected. Test tickets are written by a different model than training ones, so the model is not scored on its own writer's style. The trap set holds 23 kinds of hard cases (spaced ids, two amounts, polite but urgent, prompt injection). Limit: labels are checked by models, not people; absolute scores are optimistic, comparisons hold.
- **Sources:** `sub/ml/qualifier/notebooks/01_dataset_build.ipynb`, `sub/docs/methodology.md` §2. **Material:** `sub/.local/figures/01_split_funnel.png` exists, re-export in the deck theme.

### 9 · Fine-tuning on Kubeflow
- **On slide:** "Qwen2.5-3B with LoRA, trained as a Kubeflow pipeline on Vertex AI. Short trial runs set the settings before the 2-hour GPU run."
- **Visual, left:** screenshot of the pipeline run in the Vertex AI console (`keelpay-router-training-pipeline-20261101173631`): data preparation → fine-tuning on a T4 → prediction, all green, Metrics artifact open (`train_loss`, `eval_loss`). **Right:** training and validation loss over 1,296 steps (3 epochs), minimum 0.0030 at step 1,250, no overfitting. **Under the chart, one line:** "Course settings (3 epochs, rank 8, lr 3e-4, 4-bit base) + three measured changes: 1,024-token sequences, loss on the answer only, float16."
- **Say:** we measured before paying: 41 % of our examples were longer than the course's 512 tokens and the JSON answer comes last, so it would have been cut for 4 tickets in 10. A 40-step trial showed float16 gives the same losses 3.1 times faster, which turned a 6-hour run into 2. The best checkpoint on validation loss is kept automatically. No hyperparameter sweep was run: the first run passed the validation gate.
- **Sources:** `sub/ml/qualifier/src/pipelines/model_training_pipeline.py`, `fine_tuning_component.py`; `sub/ml/qualifier/notebooks/03_finetuning_vertex.ipynb`; `sub/docs/results/d_qwen2.5-3b_full_run_log_history.json`; `sub/docs/roadmap.md` G3-G4. **Material:** console screenshot to capture (read-only, free); loss curve exists (`sub/.local/figures/03_loss_curve.png`), re-export.

### 10 · Results against simpler systems
- **On slide:** "On 610 test tickets read once: 0.7 silent errors per 100 for the fine-tuned model, 10.5 for the same model only prompted, 33.9 for classical ML."
- **Visual:** horizontal bars, silent errors per 100 tickets on `test_natural`, with 95 % intervals: majority 78.5 · keyword rules 40.3 · TF-IDF + logistic regression 33.9 · Qwen prompted 10.5 · fine-tuned GPU 2.0 · 8-bit 1.0 · 4-bit 0.7. Fine-tuned bars in the highlight colour.
- **Say:** the selection rule was written before scoring: keep the fine-tuned model only if its difference with the best baseline has an interval excluding zero; it does. The prompted model breaks the JSON format 4 times in 10, so it hands 43 tickets in 100 to a person. One bar is not met: one urgent ticket of 167 still goes to a wrong desk; the next section covers it.
- **Sources:** `sub/docs/scoring_protocol.md` §5, §8. **Material:** `sub/.local/figures/05_test_silent.png` exists, re-export.

### 11 · The trade-off that chose the served model
- **On slide:** "Compressed to 4 bits, the model keeps its quality and runs on a plain CPU: about 20 € a month for 36,000 tickets, against about 255 € for a GPU endpoint."
- **Visual:** scatter, x = estimated monthly serving cost, y = silent errors per 100 tickets; points TF-IDF, prompted Qwen, fine-tuned GPU, 8-bit, 4-bit; the 4-bit point circled. Label "validation set; cost is an assumption".
- **Say:** merge, conversion and quantisation ran as another pipeline on a Vertex CPU job. 1.9 GB file, 2.4 GB of RAM, about 6 s per ticket, invisible for email support. We cancelled the smaller models: at most 9 € a month to save, for less capacity to copy exact ids.
- **Sources:** `sub/docs/compact_variants.md` §1-2, `sub/docs/scoring_protocol.md` §6. **Material:** `sub/.local/figures/04_quality_vs_cost.png` exists, re-export.

---
*Divider · Guardrails*

### 12 · Guardrails
- **On slide:** "The model is confident even when it is wrong. So each risk has a rule or a person in front of it."
- **Visual:** the workflow of slide 5 as a thin strip with six stops, one short label each: contract check (invalid → person) · `OTHER`/`UNDEFINED` → Re-router · sensitive topics (legal threat, complaint, fraud, account hold) → no draft · evidence gate: no fact, no factual claim · policy check: no promise, no figure absent from the evidence, no other merchant's id · a person approves, the same check runs on the final text. Next to it, cropped screenshot of a draft blocked by the policy check, Approve disabled.
- **Say:** two findings drove this. Token probabilities do not separate right from wrong answers (AUC 0.60 on intent): no confidence threshold is usable. And on 50 tickets we wrote by hand, the earlier flow drafted replies for tickets only a person should answer; each fault became a rule in the specification and the code. The rules are deterministic and unit-tested; they can miss a paraphrase, and the person remains the check on meaning. Not built yet: the switch that turns drafting off.
- **Sources:** `sub/flow/qualifier.py`, `router.py`, `field_check.py`, `evidence.py`, `policy.py`, `config.toml`; `sub/ml/confidence/README.md`; `evals/report_v0.md`; `spec.md` §10. **Material:** strip to make; screenshot to capture (seed one ticket that triggers a block).

---
*Divider · Deployment*

### 13 · Registry and endpoint
- **On slide:** "The chosen model is a version in the Vertex AI Model Registry, served on CPU from GCP next to the API that runs the workflow."
- **Visual:** a chain of cropped screenshots: Model Registry (`keelpay-router-json`, alias `qwen3b-lora-q4`, europe-west2) → container images in Artifact Registry → running service with its URL and health check.
- **Say:** the deployed file is the evaluated one: its checksum is pinned in the configuration. A GPU endpoint bills every hour even idle, so CPU, and every billed resource has a stop command. Secrets stay out of images; demo data is synthetic.
- **Sources:** `sub/docs/scoring_protocol.md` §8 "Registration", `sub/flow/deploy/`, `sub/flow/config.toml`. **Material:** blocked until the deployment is done (gap 1).

---
*Divider · Monitoring*

### 14 · Monitoring with Langfuse
- **On slide:** "Each ticket leaves a trace: one span per step, its duration, the model and the prompt version. Ticket text is not sent to it."
- **Visual:** cropped Langfuse trace of one ticket (qualifier, drafter, human action; durations; `prompt_name`, `prompt_version`).
- **Say:** prompts are released in Langfuse under a `production` label; if Langfuse is down, the flow uses a marked local copy and continues. Operational counts (waiting, approved, sent) stay in our own store; Langfuse observes. In production, silent errors have no label: the signals to watch are Re-router corrections, edited drafts, policy blocks and a weekly QA sample.
- **Sources:** `sub/flow/prompt_management.py`, `@observe` in `sub/flow/qualifier.py`, `drafter.py`, `human_actions.py`; `sub/docs/design/flow-v2/prompt-management.md`. **Material:** to capture after gap 2.

---
*Divider · Next*

### 15 · Where we stop, what comes next
- **On slide:** "We stop at a deployed MVP on synthetic data. The expected value, about 214 k€ a year, holds only if agents save more than 13 % of their time at equal quality."
- **Visual:** one gate track, left to right. Passed: dataset · baselines · trial run · full run · better than baselines · CPU variant · tests read once · registry · deployed and traced. Not passed: no urgent ticket in a wrong desk (1 of 167). Next, greyed, each with its check: rerun of the 100 hand-written tickets on the current flow · switch tested at "drafting off" · shadow run on real tickets inside Keelpay's cloud · pilot alternating weeks with and without the copilot (handling time, QA score, repeat contacts) · go by Support and Compliance.
- **Say:** the method was the same at each step: write the check, measure on data we did not tune on, then spend. It made us keep a 3B model on a CPU, cancel two experiments, and say which gates are not passed. A stop rule is already written for the pilot.
- **Sources:** `sub/docs/roadmap.md`, `02_investment_memo.md`, `05_metrics.md` §3, `governance.md`. **Material:** diagram to make.

### 16 · Demo (video, last)
- 45-60 s, no live demo, one caption per step: (1) tickets arrive, the Dashboard flow moves; (2) a payment ticket: the Qualifier's fields, the draft with its sources, edit, approve, send; (3) an unclear ticket in the Re-router, the agent sets the desk; (4) a sensitive ticket: no draft, reason shown; (5) the trace in Langfuse.
- **Material:** to record on the deployed service (or local containers, said so).

## 3. What we deliberately do not show

| Left out | Why |
|---|---|
| Severity score, macro-F1, per-field scores, trap families | One metric carries the model story; the rest is appendix. |
| Target flow with Judge, redraft and switch | Not built; showing it would be a false claim. Appendix with a built / designed legend. |
| Investment memo mechanics, lean canvas, press release, user research | AI Product course content; one chart and one sentence do the job here. The press release is fiction. |
| Grader agreement and LLM judge | Measured on an earlier Drafter; the Judge node is not built. Appendix. |
| Draft quality numbers (2 of 30 sendable) | Measured before evidence and policy checks existed; stated as the open point, not as a result. |
| MLflow | Local tracking, not required; one spoken mention, appendix. |
| Synthetic merchant world database | Supports the demo; visible in the video. |
| Euro cost of the GPU run | Not recorded in the repo; we give GPU hours. |

## 4. Appendix (hidden) and questions to prepare

Appendix, one visual each: A1 all measures, all systems (`05_scorecard.png`) · A2 traps by family · A3 urgent failure modes · A4 latency, size and RAM of the variants · A5 full training settings and the smoke runs (654 s vs 213 s) · A6 the prompt · A7 confidence study (AUC by field, validation only) · A8 hand-written evaluation and the three faults (`evals/report_v0.md`) · A9 graders and judge (`05_metrics.md` §5) · A10 target flow, built / designed · A11 human checkpoints and the switch positions (`04_architecture.md` §5-6) · A12 sizing scenarios · A13 data location: demo vs production · A14 project cost (dataset 3 $, 2 h 06 of T4, compression job 0.54 €).

Questions, with the short honest answer:
1. *Is the endpoint up now, and is it the registered model?* Depends on gap 1; checksum pinned in `sub/flow/config.toml`.
2. *Where are the metrics in the pipeline?* Losses and trainable parameters in the Metrics artifact; task metrics computed by our scorer on the predictions file the pipeline writes; the evaluation component is a placeholder.
3. *Validation loss on what?* A slice held out of the training file inside the component; `val.csv` is used for the scored predictions.
4. *Why fine-tune instead of prompting a big model?* Same 3B prompted: 10.5 and 40 % broken JSON; a hosted large model is excluded by the scenario's data rule. The comparison with a large API model was not run.
5. *Did you tune hyperparameters?* No sweep ran; the pipeline exists and compiles.
6. *Is 4-bit really better than full precision?* 4 tickets against 12 of 610, and full precision is better on traps: the claim is "no visible loss".
7. *Synthetic labels: why believe the scores?* Same tickets for every system, tests by another writer; the hand-written set gave lower numbers (88 % valid outputs).
8. *One urgent ticket in 167 misrouted?* Not acceptable against our own bar; covered by the Re-router and the weekly QA sample, not yet measured.
9. *Is the 20 % saving real?* No, an assumption; only routing has a partial estimate (about 9 %).
10. *What if Langfuse or the model is down?* Local prompt fallback; a ticket whose reading fails goes to the Re-router.
11. *Why a workflow and not an agent?* `04_architecture.md` §1.
12. *Who are your users?* Classmates playing support roles; no real support agent interviewed.

## 5. Gaps to close before building the slides

| # | Gap | Blocks | Action |
|---|---|---|---|
| 1 | Nothing is deployed on GCP; only the Model Registry entry exists. A Vertex endpoint lived 32 min on 2 November and was deleted. | slides 13, 14, 16 | Decide Cloud Run vs Vertex endpoint (ask the lecturer), get the go, deploy with a written teardown, capture. Issue #40. |
| 2 | Langfuse: spans and prompt versions in code, no trace or dashboard captured; no cost, token or score on spans; one trace per ticket not verified. | slide 14 | Run with keys, check the trace tree, group spans per ticket if needed, capture. Issue #41. |
| 3 | Charts live in untracked `sub/.local/figures/`; four charts and two diagrams to make. | slides 2-5, 8-12, 15 | One script, one theme, tracked output folder. |
| 4 | No screenshot or video exists. | slides 6, 9, 12-14, 16 | Capture after 1 and 2. |
| 5 | Front-end work uncommitted. | slide 6, video | Commit before capturing. |
| 6 | READMEs and `04_architecture.md` contradict the code ("the API does not exist yet", nodes marked "to build" that run). | jury opening the repo | Align status lines before the oral. |
| 7 | Full flow not re-evaluated since the guardrails (only the 13 November run). | slide 12 wording | Optional rerun on `evals/eval_set_v1.csv` (Drafter API cost, synthetic data); otherwise say "built and tested, not re-measured". |
| 8 | `audit_logs_equipe_navy.csv` holds a personal e-mail and IPs. | appendix | Never commit or show as is; quote timestamps only. |

## 6. Decisions to take as a team

- **D1** Endpoint type: Cloud Run on CPU (recommended, scales to zero) or a short-lived Vertex AI endpoint for the screenshot. Ask the lecturer.
- **D2** Slide tool (Google Slides recommended for 4 editors, charts exported from code).
- **D3** Slide language.
- **D4** Who presents which section; date of the oral.
- **D5** Same deck as the AI Product final oral (#66) or a separate one (recommended: separate, shared charts).
