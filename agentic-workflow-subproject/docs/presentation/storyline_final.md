# Final oral: storyline and slide content

Status: **final content v2, 16 November 2026.** Merged from four independent drafts kept in this folder for reference (`storyline_v1.md` to `storyline_v4.md`, constraints in `brief.md`). This file is the one the deck is built from. Paths starting with `sub/` are in `agentic-workflow-subproject/`.

## 0. Directions for the deck

Advice, not rules: use judgment slide by slide. The aim is a deck that carries a lot of real work and still reads easily: neither a book nor empty slides.

**Progress gauge**
- Every slide after the index carries a discreet progress gauge with the chapter names (Context · Framing · Workflow · Model · Guardrails · Deployment · Monitoring · Next), the current chapter highlighted, so the audience always knows where we are. The index slide introduces it; dividers can show it enlarged.

**Visual identity: our own, not the generic AI look**
- Most student decks this year come out of the same AI tools and look alike. Ours must not. Avoid the recognisable generated look: dark navy or black backgrounds with purple-blue gradients, glowing accents, glass cards with rounded corners, a grid of identical cards, small uppercase labels above every title, giant stat numbers, emoji or line icons as decoration, the default Inter/system font everywhere.
- Instead, choose one deliberate art direction early and keep it: for example an editorial or print-like look (a characterful serif or grotesque typeface pair, a light paper background, one strong accent colour, generous margins, real photos/screenshots framed simply), or a "payments product" identity built around a fictional Keelpay brand (logo, palette, type) as if the copilot were a real internal product.
- Decide the identity once as a small style sheet (2 typefaces, 4-5 colours with their meaning, chart style, gauge style, divider style) before building slides, and make every chart in it.

**Density**
- A slide can hold two related pieces of information (two charts, a chart and a screenshot, two short titles) when the layout leaves each one room to breathe. Prefer one well-filled slide over two near-empty ones.
- Split a slide when the two pieces compete for attention or when the audience would need to read for more than a few seconds.

**Hierarchy**
- What matters most should look the most important: the main chart or message is the largest and most central element. Section names, labels, sources and page numbers stay discreet.
- Avoid stacked headings (title, subtitle, small label above it) that say the same thing twice. If two titles are on a slide, they are because two panels sit side by side.

**Text**
- Short sentences that explain, rather than bullet lists or keywords. Speaker details stay in the notes.
- A number earns its place when it explains something, in a sentence or on a chart. Avoid KPI tiles and walls of figures.
- Plain, sober wording: we present work and decisions, we do not sell. Avoid buzzwords, slogans and rhetorical questions.
- Use status words precisely: built, designed, measured, assumption. Say limits and failed gates plainly, once.

**Visuals**
- Each content slide is carried by visuals that explain themselves: charts, cropped screenshots, simple diagrams.
- Charts: one highlight colour against grey, labels on the data rather than a legend, axis titles in plain words with units, a discreet source line.
- One colour code for the whole deck (model, rule, person; passed, not passed), the same meaning everywhere.
- Screenshots cropped to what matters and readable from the back of the room.
- Keep decoration minimal: no ornamental icons, emojis, shadows or boxes around everything.

## 1. The story in five lines

1. **Context.** Keelpay is a fictional B2B payments company. Its support agents answer 36,000 merchant tickets a month by hand, and one ticket in seven first lands in the wrong desk.
2. **Framing.** Before building, we priced the project against cheaper options and wrote the checks that would stop it: it is worth it only above about 13 % of handling time saved, and the model is judged first on errors nobody flags.
3. **Workflow.** We built a fixed workflow, not an agent: a fine-tuned small model reads the ticket, rules route it, read-only tools fetch facts, a second model drafts, and a person approves every send.
4. **Model, deployment, monitoring.** The reading model was fine-tuned as a Kubeflow pipeline on Vertex AI, compared with four simpler systems, compressed to run on a CPU, registered, served and traced with Langfuse. Rules around both models stop what they get wrong.
5. **Next.** We stop at a deployed MVP on synthetic data. The model gate is passed; the product gates (time saved at constant quality) are not measured yet and decide any pilot.

## 2. Slides

Progress bar on every slide after the index: Context · Framing · Workflow · Model · Guardrails · Deployment · Monitoring · Next. Dividers carry the section name and are passed quickly.

| # | Slide | Layout | Time |
|---|---|---|---|
| 0 | Cover | | 5 s |
| 1 | Index and team | | 10 s |
| 2 | Context | ticket + time bar | 40 s |
| 3 | Framing | two panels: worth building · what we measure and the gates | 60 s |
| 4 | The workflow | one diagram | 45 s |
| 5 | The interface | one screenshot | 20 s |
| 6 | The model and its data | two panels: input/output · dataset | 50 s |
| 7 | Fine-tuning on Kubeflow | two panels: pipeline run · loss curve | 50 s |
| 8 | Results and choice | two charts: silent errors by system · quality vs cost | 60 s |
| 9 | Guardrails | strip + screenshot | 45 s |
| 10 | Registry and endpoint | screenshot chain | 35 s |
| 11 | Monitoring with Langfuse | one trace (+ dashboard if available) | 35 s |
| 12 | Where we stop, what comes next | gate track | 40 s |
| 13 | Demo video | | 45-60 s |
| | 8 dividers | | about 25 s |
| | **Total** | | **about 9 min 30** |

If it runs long, shorten the demo and the dataset panel of slide 6 first; slides 3, 9 and 12 carry the reasoning.

---

### 0 · Cover
- **On slide:** "Keelpay support copilot" and one line: "Reading, routing and drafting merchant tickets, with a person sending every reply." Team NAVY, course, date.

### 1 · Index and team
- **On slide:** the eight section names (they become the progress bar) and the four names: Alexandre Waerniers, Vincent Lamy, Nahel Bachiri, Yoni Mahieddine (`README.md`).
- **Say:** "The model, its guardrails, its deployment and its monitoring are parts 4 to 7. A video of the application closes the talk."

---
*Divider · Context*

### 2 · Context
- **On slide:** "Keelpay, a fictional B2B payments company: 2,500 merchants send 36,000 support tickets a month, in French and English. One ticket in seven first lands in the wrong desk."
- **Visual:** a real-looking ticket in French, three lines (from `sub/data/dataset/train.csv`), and one horizontal bar of the handling time of a ticket: read and route 15 %, find the payment and write 45 %, check and send 40 %. The first two parts coloured (what a copilot can help with), a marker "1 in 7 to the wrong desk" on the first.
- **Say:** the scenario comes from the AI Product course; we act as the product team. Users are support agents in four desks: payments, disputes, technical, compliance. These figures are the scenario's data, not our measurements.
- **Sources:** `README.md` "Shared scenario", `01_problem_statement.md` §1. **Material:** chart to make.

---
*Divider · Framing*

### 3 · Framing: worth building, and what we measure
Two panels side by side, each with its own short title.

- **Left, "Worth building only above 13 % of time saved".** Line chart: x = share of handling time saved (10 to 30 %), y = net value per year (55 k€ at 10 %, 123 k€ at 15 %, 191 k€ at 20 %, 259 k€ at 25 %, 326 k€ at 30 %); horizontal line about 100 k€ "rules only, no AI"; markers at 13.3 % and at 20.3 % "base assumption, not measured".
- **Right, "The error we count first, and the gates".** One ticket splitting into three outcomes: right / handed to a person (a few minutes, no damage) / silent error: a wrong desk or a wrong payment reference that nothing flags. Under it, the gates fixed before building with their marks: dataset frozen ✓ · cheap baselines first ✓ · fine-tuned model must beat the best baseline ✓ · no urgent ticket in a wrong desk ✗ (1 of 167) · time saved at constant quality: to measure.
- **Say:** we built a sizing with three scenarios and two alternatives (do nothing, rules only); the low case loses money, so the decision was "build and measure a demo, conditional go for a pilot". For the model, accuracy alone would have hidden the problem: the classical baseline sends 92 % of tickets to the right desk and still gets one payment reference in three wrong. The model may answer "undefined" rather than guess, so silent errors are read together with the share handed to a person. Settings were chosen on validation, test sets read once, failed gates shown as failed.
- **Sources:** `02_sizing.xlsx` `Decision!C32:C36`, `D23`, `D57` (check the values when drawing); `02_investment_memo.md`; `sub/docs/scoring_protocol.md` §2, §4, §5, §8; `sub/docs/roadmap.md`. **Material:** chart and diagram to make.

---
*Divider · Workflow*

### 4 · The workflow
- **On slide:** "A fixed path, not an agent. Two models read and write, rules decide and check, a person approves every send."
- **Visual:** the flow with the nodes that run (`sub/flow/langgraph_app.py`): ticket → Qualifier (fine-tuned) → field check → routing → context plan → ledger and knowledge search (read-only) → evidence gate → Drafter → policy check → Validator (person) → final check and simulated send; side exit to the Re-router (person) for unclear, invalid or sensitive tickets. Colours: model, rule, person. Judge, redraft and override switch not drawn (designed, not built).
- **Say:** no model chooses a tool or the next step, so the cost per ticket is bounded and each step can be explained. LangGraph keeps a checkpoint so a ticket waits for the person and resumes. The Qualifier runs locally on CPU; the Drafter is an external model, allowed only because demo data is synthetic. Nothing is sent, refunded or written to the ledger by the system.
- **Sources:** `04_architecture.md` §1, `sub/flow/config.toml`. **Material:** redraw from `sub/docs/design/flow-v2/flow_v2.svg`.

### 5 · The interface
- **On slide:** "The agent's screen: the ticket, the draft with its sources, the actions. Nothing is sent without a click."
- **Visual:** Workspace screenshot on a ticket with a grounded draft (queue, draft and sources, Approve / Send to re-routing / Close, merchant history). Could share the slide with a small Dashboard capture if the layout allows.
- **Say:** a FastAPI service runs the graph and serves this front end; the Dashboard shows the flow and queues from the same events. The video at the end shows it in use.
- **Material:** screenshot to capture (`sub/flow/deploy/demo.ps1 -Inject 6`), after the front-end work is committed.

---
*Divider · Model*

### 6 · The model and its data
Two panels.

- **Left, "One ticket in, seven fields out".** The French SEPA ticket ("virement de 12 500 €… ref: TX-994821… C'est urgent") and its JSON (`intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`); a smaller pair below with an ambiguous id answered `"UNDEFINED"`.
- **Right, "3,205 generated tickets, checked before use".** The chain in one line (scenario card fixes the label → a model writes the text → two blind readers → judge on disagreement → accepted or set aside) and the funnel per split: train 2,657 → 1,922 · validation 450 → 293 · test 950 → 610 · traps 645 → 380.
- **Say:** closed values, four intents mapping to the four desks, `OTHER` and `UNDEFINED` as sentinels; an output that breaks the contract goes to a person; the same instruction in training, evaluation and serving. No real tickets exist, so we generated them for about 3 dollars; about a third were rejected. Test tickets come from a different writer model, and a trap set holds 23 kinds of hard cases (spaced ids, two amounts, polite but urgent, prompt injection). Limit: labels are checked by models, not people, so absolute scores are optimistic and comparisons hold.
- **Sources:** `sub/initial_brief.md` §3, `sub/ml/qualifier/src/dataset_build/schema.py`, `sub/ml/qualifier/src/prompt.py`, `sub/data/dataset/test_traps.csv` (for the `UNDEFINED` example), `sub/ml/qualifier/notebooks/01_dataset_build.ipynb`, `sub/docs/methodology.md` §2. **Material:** layout to make; funnel exists in `sub/.local/figures/01_split_funnel.png`.

### 7 · Fine-tuning on Kubeflow
Two panels.

- **Left, the pipeline run.** Screenshot of `keelpay-router-training-pipeline-20261101173631` in the Vertex AI console: data preparation → fine-tuning on a T4 → prediction, Metrics artifact open (`train_loss`, `eval_loss`).
- **Right, the training.** Training and validation loss over 1,296 steps (3 epochs), minimum 0.0030 at step 1,250, no overfitting; under it, one line: "Qwen2.5-3B + LoRA. Course settings (3 epochs, rank 8, lr 3e-4, 4-bit base) with three measured changes: 1,024-token sequences, loss on the answer only, float16."
- **Say:** we measured before paying: 41 % of our examples were longer than the course's 512 tokens and the JSON answer comes last, so it would have been cut for 4 tickets in 10. A 40-step trial showed float16 gives the same losses 3.1 times faster, a 6-hour run became 2 h 06. The best checkpoint on validation loss is kept automatically. No hyperparameter sweep ran: the first run passed the validation gate.
- **Sources:** `sub/ml/qualifier/src/pipelines/model_training_pipeline.py`, `fine_tuning_component.py`, `sub/ml/qualifier/notebooks/03_finetuning_vertex.ipynb`, `sub/docs/results/d_qwen2.5-3b_full_run_log_history.json`, `sub/docs/roadmap.md` G3-G4. **Material:** console screenshot to capture (read-only); loss curve exists in `sub/.local/figures/03_loss_curve.png`.

### 8 · Results and choice
Two charts.

- **Left, "Against simpler systems, on 610 test tickets read once".** Horizontal bars of silent errors per 100 tickets with 95 % intervals: majority 78.5 · keyword rules 40.3 · TF-IDF + logistic regression 33.9 · Qwen prompted 10.5 · fine-tuned GPU 2.0 · 8-bit 1.0 · 4-bit 0.7.
- **Right, "Same quality on a CPU".** Scatter of silent errors per 100 against estimated monthly serving cost: TF-IDF, prompted Qwen, fine-tuned GPU (about 255 €/month), 8-bit, 4-bit (about 20 €/month, circled). Label "validation set; cost is an assumption".
- **Say:** the selection rule was written before scoring: keep the fine-tuned model only if its difference with the best baseline has an interval excluding zero; it does. The prompted model breaks the JSON 4 times in 10 and hands 43 tickets in 100 to a person. We merged and quantised the model in another pipeline on a Vertex CPU job: 1.9 GB, about 6 s per ticket, invisible for email support. We cancelled smaller models: at most 9 € a month to save. One gate is not met: one urgent ticket in 167 still goes to a wrong desk; the next section covers it.
- **Sources:** `sub/docs/scoring_protocol.md` §5, §6, §8; `sub/docs/compact_variants.md` §1-2. **Material:** both figures exist (`05_test_silent.png`, `04_quality_vs_cost.png`), re-export in the deck theme.

---
*Divider · Guardrails*

### 9 · Guardrails
- **On slide:** "The model is confident even when it is wrong, so each risk has a rule or a person in front of it."
- **Visual:** the workflow as a thin strip with its stops, one short label each: contract check (invalid → person) · `OTHER`/`UNDEFINED` → Re-router · sensitive topics (legal threat, complaint, fraud, account hold) → no draft · evidence gate: no fact, no factual claim · policy check: no promise, no figure absent from the evidence, no other merchant's id · a person approves, the same check runs on the final text. Next to it, a cropped screenshot of a draft blocked by the policy check.
- **Say:** two findings drove this. Token probabilities do not separate right from wrong answers (AUC 0.60 on intent), so no confidence threshold is usable. On 50 tickets we wrote by hand, the earlier flow drafted replies for tickets only a person should answer; each fault became a rule in the specification and the code. The rules are deterministic and unit-tested; they can miss a paraphrase, and the person stays the check on meaning. Not built yet: the switch that turns drafting off.
- **Sources:** `sub/flow/qualifier.py`, `router.py`, `field_check.py`, `evidence.py`, `policy.py`, `config.toml`; `sub/ml/confidence/README.md`; `evals/report_v0.md`; `spec.md` §10. **Material:** strip to make; screenshot to capture (seed a ticket that triggers a block).

---
*Divider · Deployment*

### 10 · Registry and endpoint
- **On slide:** "The chosen model is a version in the Vertex AI Model Registry, served on a Vertex AI endpoint by a llama.cpp container. The interface and the API that runs the workflow call it."
- **Visual:** chain of cropped screenshots: Model Registry (`keelpay-router-json`, alias `qwen3b-lora-q4`, europe-west2) → Vertex AI endpoint with the D-q4 model deployed (CPU machine, status) → front end on Cloudflare Pages calling the hosted API → Qualifier answer in the app. A small architecture strip above: Cloudflare Pages (front end) → API (FastAPI + LangGraph, persistent storage) → Vertex AI endpoint (D-q4, llama.cpp) ; Langfuse Cloud on the side.
- **Say:** the deployed file is the evaluated one (4-bit GGUF, checksum pinned). The llama.cpp container is adapted to the Vertex prediction contract. An endpoint bills every hour, even idle: the model is deployed for tests and the demo, then undeployed to free the billed resources. Secrets stay out of images; demo data is synthetic.
- **Sources:** `sub/docs/scoring_protocol.md` §8 "Registration", `sub/flow/deploy/`, `sub/flow/config.toml`; deployment issues #40, #73-#77. **Material:** blocked until the deployment is done (gap 1).

---
*Divider · Monitoring*

### 11 · Monitoring with Langfuse
- **On slide:** "Each ticket leaves a trace: one span per step, its duration, the model and the prompt version. Ticket text is not sent to it."
- **Visual:** cropped Langfuse trace of one ticket (qualifier, drafter, human action; durations; `prompt_name`, `prompt_version`), with a dashboard view next to it if latency or cost per ticket is available.
- **Say:** we use Langfuse Cloud with synthetic traces only, identified by demo session. The demo history is produced by a deterministic human simulator (`demo-agent`) that acts through the same API as the interface, so the traces look like real use without real data. Prompts are released in Langfuse under a `production` label; if Langfuse is down, the flow uses a marked local copy and continues. Operational counts (waiting, approved, sent) stay in our own store; Langfuse observes. In production, silent errors have no label: the signals to watch are Re-router corrections, edited drafts, policy blocks and a weekly QA sample.
- **Sources:** `sub/flow/prompt_management.py`, `@observe` in `sub/flow/qualifier.py`, `drafter.py`, `human_actions.py`; `sub/docs/design/flow-v2/prompt-management.md`. **Material:** to capture after gap 2.

---
*Divider · Next*

### 12 · Where we stop, what comes next
- **On slide:** "We stop at a deployed MVP on synthetic data. The expected value, about 214 k€ a year, holds only if agents save more than 13 % of their time at equal quality."
- **Visual:** one gate track, left to right. Passed: dataset · baselines · trial run · full run · better than baselines · CPU variant · tests read once · registry · deployed and traced. Not passed: no urgent ticket in a wrong desk (1 of 167). Next, greyed, each with its check: rerun of the 100 hand-written tickets on the current flow · switch tested at "drafting off" · shadow run on real tickets inside Keelpay's cloud · pilot alternating weeks with and without the copilot (handling time, QA score, repeat contacts) · go by Support and Compliance.
- **Say:** the method was the same at each step: write the check, measure on data we did not tune on, then spend. It made us keep a 3B model on a CPU, cancel two experiments, and say which gates are not passed. A stop rule is already written for the pilot.
- **Sources:** `sub/docs/roadmap.md`, `02_investment_memo.md`, `05_metrics.md` §3, `governance.md`. **Material:** diagram to make.

### 13 · Demo (video, last)
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
| 1 | Nothing is deployed on GCP; only the Model Registry entry exists. A Vertex endpoint lived 32 min on 2 November and was deleted. gcloud and a GCP browser session are not available in the current environment. | slides 10, 11, 13 | Check the registered Vertex artifact, adapt the llama.cpp container to the Vertex prediction contract, choose the API host with persistent storage, deploy for tests and demo, undeploy after, capture. Issues #40, #73-#77. |
| 2 | Langfuse: spans and prompt versions in code, no trace or dashboard captured; no cost, token or score on spans; one trace per ticket not verified. | slide 11 | Run with keys, check the trace tree, group spans per ticket if needed, capture. Issue #41. |
| 3 | Charts live in untracked `sub/.local/figures/`; several charts and diagrams to make. | slides 2-4, 6-9, 12 | One script, one theme, tracked output folder. |
| 4 | No screenshot or video exists. | slides 5, 7, 9-11, 13 | Capture after 1 and 2. |
| 5 | Front-end work uncommitted. | slide 5, video | Commit before capturing. |
| 6 | READMEs and `04_architecture.md` contradict the code ("the API does not exist yet", nodes marked "to build" that run). | jury opening the repo | Align status lines before the oral. |
| 7 | Full flow not re-evaluated since the guardrails (only the 13 November run). | slide 9 wording | Optional rerun on `evals/eval_set_v1.csv` (Drafter API cost, synthetic data); otherwise say "built and tested, not re-measured". |
| 8 | `audit_logs_equipe_navy.csv` holds a personal e-mail and IPs. | appendix | Never commit or show as is; quote timestamps only. |

## 6. Decisions

**Taken (deployment, 16 November 2026):**
- Model: D-q4, 4-bit GGUF served by llama.cpp.
- Qualifier served on a Vertex AI endpoint (required by the project); deployed for tests and the demo, then undeployed to free billed resources (the empty endpoint can be kept or deleted).
- Front end on Cloudflare Pages. Back end: the current FastAPI + LangGraph API needs a compatible host with persistent storage (Pages/Workers cannot host it as is): host to choose.
- Monitoring: Langfuse Cloud, synthetic traces, no sensitive content.
- Demo history: a deterministic human simulator acting through the same API as the interface, identified as `demo-agent`.
- Reset: protected per demo session; Langfuse traces stay identified by session and follow their retention policy.
- Next technical step: check the registered Vertex artifact, then adapt the llama.cpp container to the Vertex prediction contract before any billed deployment.
- Tracking: issues #40, #41, #73-#77.

**Still open:**
- **D1** API host with persistent storage.
- **D2** Slide tool (Google Slides recommended for 4 editors, charts exported from code).
- **D3** Slide language.
- **D4** Who presents which section; date of the oral.
- **D5** Same deck as the AI Product final oral (#66) or a separate one (recommended: separate, shared charts).
