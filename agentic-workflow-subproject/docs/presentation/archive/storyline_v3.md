# Storyline v3 — final oral, read through the eyes of the LLMOps lecturer

Written on 16 November 2026 from the repository only (branch `feat/container-demo`). Paths are relative to `agentic-workflow-subproject/` unless they start with `/` (repository root).

Lens of this version: the person who grades ticks four mandatory boxes and two bonus boxes. Each box gets one slide whose visual proves it in a few seconds, in the order fixed by the brief. Everything else is kept short so that the ML, deployment and monitoring sections get a little more than half of the speaking time.

| Box to tick | Slide | Proof on screen | State of the proof today |
|---|---|---|---|
| Fine-tuned LLM on Kubeflow, with metrics | 7 | Vertex AI Pipelines run graph of `keelpay-router-training-pipeline`, Metrics artifact open | run done; screenshot to capture |
| Endpoint on GCP, with registry | 12 | Vertex Model Registry page of `keelpay-router-json`, tab "Deploy and test", listing the endpoint | model registered; **no endpoint standing** (gap 1) |
| Interface to use the flow | 5, then the demo video (15) | Workspace screen of the front end on a real ticket | built, runs locally in containers; screenshot and video to capture |
| Monitoring with Langfuse | 13 | Langfuse trace of one ticket (Qualifier, Drafter, human action; latency; prompt version) | spans are sent by the code; what the UI shows is unverified (gap 2) |
| Bonus: fine-tuning R&D | 6, 8, 9, 10 | dataset funnel, loss curve, all-systems chart, quality against cost | all four charts exist |
| Bonus: guardrails | 11 | a draft blocked by the policy check in the Workspace | code and tests exist; screenshot to capture |

## 1. Storyline in 5 lines

1. Keelpay (fictional B2B payments company) receives 36,000 merchant tickets a month; agents lose most of their time reading, routing and looking up payments, and 1 ticket in 7 first lands in the wrong desk.
2. Before building, we fixed what the product must reach to be worth it (time saved above 13.32 %) and what the model must never do silently (a wrong desk or a wrong payment reference that nobody flags).
3. We built a fixed workflow, not an agent: a fine-tuned small model reads the ticket into 7 fields, rules route it, read-only tools fetch facts, a second model drafts, and a person approves every send.
4. The fine-tuned model was trained as a Kubeflow pipeline on Vertex AI, compared with four simpler systems on the same tickets, compressed to run on CPU, registered, served, and traced with Langfuse; rules around both models stop what they get wrong.
5. We stop at a deployed MVP on synthetic data: the model gate is passed, the full-flow gates (time saved at constant quality, serious errors) are not measured yet and decide the pilot.

## 2. Slide by slide

A thin progress bar sits at the bottom of every slide after the index: eight segments (Context, Framing, Workflow, Model, Guardrails, Deployment, Monitoring, Conclusion), the current one filled. Dividers carry only the section name and one line.

---

### Slide 0 — Cover
- **Section:** none.
- **Text:** "Keelpay support copilot. From a merchant ticket to a reply a person approves." Team NAVY, course name, date.
- **Visual:** none (sober cover).
- **Speaker:** names the team and the course, nothing else.
- **Time:** 5 s. **Status:** to make.

### Slide 1 — Index
- **Section:** none.
- **Purpose:** the jury sees the eight sections and where the four mandatory items sit.
- **Text:** the eight section names in one row (they become the progress bar); the four team names, from `/README.md`: Alexandre Waerniers, Vincent Lamy, Nahel Bachiri, Yoni Mahieddine.
- **Visual:** the progress bar itself, enlarged.
- **Speaker:** "Eight short parts. The model, its guardrails, its deployment and its monitoring are parts 4 to 7. A video of the application closes the talk."
- **Time:** 10 s. **Status:** to make.

### Divider A — Context (3 s)
"Who asked what."

### Slide 2 — Context: one ticket today
- **Section:** Context.
- **Purpose:** someone who knows nothing understands the company, the user and the problem.
- **Text:** "Keelpay, a fictional B2B payments company: 2,500 merchants, 36,000 support tickets a month, in French and English. A support agent reads each ticket, picks one of four desks, finds the payment and writes the reply. 1 ticket in 7 first lands in the wrong desk."
- **Visual (chart to make):** one horizontal bar = the handling time of one ticket, cut in three parts: reading and routing 15 %, finding the payment and writing 45 %, the rest 40 %. The first two parts are coloured (what the copilot touches), with a small marker "1 in 7 goes to the wrong desk" on the first part. Source: `/README.md` section "Shared scenario", `/01_problem_statement.md` section 1 (all tagged "given", scenario data).
- **Speaker:** "The scenario comes from the AI Product course: we are the product team of this company. The users are its support agents. These numbers are the scenario's starting data, not our measurements. The two coloured parts are where a copilot can help; the send stays human."
- **Time:** 30 s. **Status:** chart to make.

### Divider B — Framing (3 s)
"What it must reach to be worth building."

### Slide 3 — Framing: the gates fixed before building
- **Section:** Framing.
- **Purpose:** the jury retains that thresholds existed before the model, and which one decides.
- **Text:** "The copilot is worth building only above 13.32 % of handling time saved: below, a simpler project without AI earns more. Quality gate: no urgent ticket routed by the system to a wrong desk."
- **Visual (chart to make):** one horizontal axis "share of handling time saved", 0 to 25 %, with four vertical marks: 5.93 % break-even, 12.79 % beats doing nothing, 13.32 % beats the rules-only alternative, 20.26 % base assumption of the sizing. One point in another colour: about 8.9 %, "routing alone, estimated from our 50-ticket evaluation". Sources: `/02_investment_memo.md` ("How sure?"), `/05_metrics.md` section 2 for the 8.9 % and its derivation, `/02_sizing.xlsx` `Decision!D57`.
- **Speaker:** "These thresholds come from the sizing, with a do-nothing baseline and a rules-only alternative. Routing alone gets us part of the way; the rest must come from drafting, which is why the workflow does not stop at the classifier. For the model itself we fixed one main error to count, the silent error: a confident answer with a wrong desk or a wrong payment reference. I come back to it with the results."
- **Time:** 30 s. **Status:** chart to make.

### Divider C — Workflow (3 s)
"What we built."

### Slide 4 — The workflow
- **Section:** Workflow.
- **Purpose:** the jury sees the whole path of a ticket, where the two models are, and where a person decides.
- **Text:** "A fixed path, not an agent: no model chooses a tool or a next step. Two models: the fine-tuned Qualifier reads, the Drafter writes. Rules route and check. A person approves every send."
- **Visual (diagram to simplify from an existing one):** a one-line version of `docs/design/flow-v2/flow_v2.svg`, restricted to the nodes that exist in `flow/langgraph_app.py` (lines 475-490): intake, Qualifier, field check, routing, context plan, tools (ledger, text search), evidence gate, Drafter, policy check, human review, send confirmation, simulated send. Three colours only: model, rule, person. The Re-router exit drawn as one branch.
- **Speaker:** "Each box is one node of a LangGraph graph with a durable checkpoint, so a ticket waits for the person and resumes. The Qualifier is our fine-tuned model, running locally on CPU. The Drafter is an external model, allowed only because the demo data is synthetic. Judge and redraft nodes of the target design are not built; we do not show them."
- **Time:** 40 s. **Status:** diagram to redraw (the existing SVG shows the target, including nodes 11-12 that are not built).

### Slide 5 — The interface
- **Section:** Workflow. **Mandatory item: interface.**
- **Purpose:** the jury sees that the flow is used through an application, before the video.
- **Text:** "The agent's screen: the ticket, the draft with its sources, and the actions. Nothing is sent without a click."
- **Visual (screenshot to capture):** the Workspace view of the front end on one ticket that has a grounded draft: left the queue, centre the draft and the buttons "Approve reply", "Send to re-routing", "Close manually", right the routing signals and merchant history. Source: `frontend/src/App.tsx` (button labels at lines 304-309), served by `flow/api.py` through `flow/deploy/compose.demo.yml`.
- **Speaker:** "A FastAPI service runs the graph and serves this front end. The second area, the Dashboard, shows the flow and the queues from the same events. You will see it move in the video at the end."
- **Time:** 20 s. **Status:** screenshot to capture from the container demo (`flow/deploy/demo.ps1 -Inject 6`); the working tree has uncommitted front-end changes, capture after they are settled.

### Divider D — The model (3 s)
"The fine-tuned model: task, data, training, choice."

### Slide 6 — Task and data
- **Section:** Model. **Bonus: R&D.**
- **Purpose:** the jury retains the input and output formats and how the dataset was made trustworthy.
- **Text:** "Input: one raw ticket. Output: one JSON object with 7 string fields (intent, sub-intent, transaction id, amount, currency, urgency, sentiment). 3,205 synthetic tickets: labels come from a scenario card, a language model only writes the text, two blind readers check it, and a ticket that fails is set aside, never repaired."
- **Visual (exists):** `.local/figures/01_split_funnel.png` — tickets accepted and quarantined by split (train 1,922 kept of 2,657; val 293 of 450; test_natural 610 of 950; test_traps 380 of 645). Built by `ml/qualifier/notebooks/01_dataset_build.ipynb`; counts also in `docs/roadmap.md` G1. A small inset on the right shows one real ticket and its JSON target (first row of `data/dataset/val.csv`).
- **Speaker:** "About a third of the generated tickets were rejected by the review chain: that is the price of labels we can trust. The two test sets were written by a different model than the training set, so the model is not graded on the style of its own writer. One test set is the natural mix; the other holds 23 kinds of traps, such as an id written with spaces or two amounts in one message."
- **Time:** 30 s. **Status:** chart exists; inset to add. Sources for the speech: `docs/methodology.md` section 2, `docs/scoring_protocol.md` section 1.

### Slide 7 — Fine-tuning as a Kubeflow pipeline
- **Section:** Model. **Mandatory item: fine-tuned LLM on Kubeflow with metrics.**
- **Purpose:** the box is ticked in five seconds: a pipeline run on Vertex AI, with its metrics.
- **Text:** "Qwen2.5-3B-Instruct with LoRA, trained as a three-step Kubeflow pipeline on Vertex AI: data preparation, fine-tuning on a T4 GPU, prediction on the validation set. 2 h 06 of GPU for the full run."
- **Visual (screenshot to capture):** the Vertex AI Pipelines console, run `keelpay-router-training-pipeline-20261101173631`: the graph with its three green steps (`data-transformation`, `fine-tuning-component`, `inference-component`) and the Metrics artifact of the fine-tuning step selected, its panel showing `train_loss`, `eval_loss`, `trainable_params`. Run name from `docs/compact_variants.md` (adapter URI); pipeline in `ml/qualifier/src/pipelines/model_training_pipeline.py`; metrics logged at `ml/qualifier/src/pipeline_components/fine_tuning_component.py` lines 146-148.
- **Speaker:** "The code follows the course sessions, with our task instead of the course one. Before the full run we ran a smoke pipeline: 200 tickets, 40 steps. It told us the time per step, so we knew the cost before paying it, and it showed that half precision gives the same losses 3.1 times faster. The quality metrics of the task are computed from the predictions file this pipeline writes; I show them in two slides."
- **Time:** 40 s. **Status:** screenshot to capture (console is read-only, nothing billed). Numbers: 2 h 06 in `docs/roadmap.md` G4 and `docs/results/d_qwen2.5-3b_full_run_log_history.json` (`train_runtime` 7,568 s); 3.1 times in `docs/methodology.md` section 3 (213 s against 654 s).

### Slide 8 — How we trained it
- **Section:** Model. **Bonus: R&D.**
- **Purpose:** the jury sees the settings, what we changed from the course defaults and why, and that training converged without overfitting.
- **Text:** "3 epochs, LoRA rank 8, learning rate 3e-4, base model loaded in 4 bits: the course settings. Three changes for our data: sequences of 1,024 tokens instead of 512, loss on the JSON answer only, half precision. The checkpoint with the lowest validation loss is kept."
- **Visual (exists):** `.local/figures/03_loss_curve.png` — training and validation loss by step on a log axis, best validation loss 0.0030 at step 1,250 of 1,296, epoch ends marked. Data: `docs/results/d_qwen2.5-3b_full_run_log_history.json`; built by `ml/qualifier/notebooks/03_finetuning_vertex.ipynb`.
- **Speaker:** "We measured the token lengths before training: 41 % of our examples were longer than the course's 512 tokens, and the JSON answer comes last, so it would have been cut for 4 tickets in 10. No loss curve would have shown that. The validation loss is still going down at the end, so we kept the last evaluation; the mechanism that reloads the best checkpoint was there but not needed."
- **Time:** 40 s. **Status:** chart exists. Sources: settings in `ml/qualifier/src/pipeline_components/fine_tuning_component.py` (lines 24-32, 83-95) and `README.md` "Training settings"; 41 % in `docs/methodology.md` section 3 and notebook 03 section 1 (790 of 1,922).

### Slide 9 — Results against simpler systems
- **Section:** Model. **Bonus: R&D.**
- **Purpose:** the jury retains that fine-tuning was necessary, measured against four alternatives on the same tickets.
- **Text:** "Silent error: a confident answer with a wrong desk or a wrong payment reference. On 610 test tickets read once, the fine-tuned model makes 0.7 per 100; the same model only prompted makes 10.5, and classical machine learning 33.9."
- **Visual (exists):** `.local/figures/05_test_silent.png` — silent errors per 100 tickets for the seven systems (majority class, keyword rules, TF-IDF + logistic regression, prompted Qwen 3B, fine-tuned on GPU, 8-bit CPU, 4-bit CPU) with 95 % intervals. Data: `docs/scoring_protocol.md` section 8; predictions in `docs/results/` and `data/runs/`; built by `ml/qualifier/notebooks/05_final_evaluation.ipynb`.
- **Speaker:** "The scoring protocol was written before any score, with the rule that the fine-tuned model is kept only if the difference to the best baseline has an interval that excludes zero; it does. The prompted base model looks decent on this chart, but 40 % of its answers break the JSON contract, so it hands 43 tickets in 100 to a person. One limit we state: 1 urgent ticket of 167 still went to a wrong desk, so the 'zero' gate is not met by the model alone. That is why the next section exists."
- **Time:** 40 s. **Status:** chart exists. Numbers: `docs/scoring_protocol.md` section 8 (0.7, 10.5, 33.9; valid JSON 60.3 %; 43.1 per 100; 1 of 167; bootstrap intervals).

### Slide 10 — The trade-off that chose the deployed model
- **Section:** Model. **Bonus: R&D.**
- **Purpose:** the jury sees a model chosen on quality against serving cost, not on the best score.
- **Text:** "We merged the adapter into the model and compressed it to 4 bits. Same quality on validation, no GPU: about 20 euros a month on CPU against about 255 for a GPU endpoint that never scales to zero."
- **Visual (exists):** `.local/figures/04_quality_vs_cost.png` — silent errors per 100 tickets (val, 293 tickets) against estimated monthly serving cost for B2, B3, D, D-q8, D-q4; D-q4 in the lower-left corner. Built by `ml/qualifier/notebooks/04_compact_variants.ipynb`; data in `docs/compact_variants.md`.
- **Speaker:** "The compression ran as another pipeline on a Vertex CPU job: merge, convert to GGUF, quantise, predict, time each ticket. The 4-bit model answers in about 6 seconds on 8 CPU cores and needs 2.4 GB of memory; for email support that delay is invisible. The cost axis is an assumption, 36,000 tickets a month at a serverless CPU price; the latency is measured. We cancelled the smaller models: at most 9 euros a month to gain, and less capacity to copy exact ids."
- **Time:** 35 s. **Status:** chart exists. Numbers: `docs/compact_variants.md` sections 1-2 (6.43 s, 2.4 GB, about 20 and 255 euros, tagged as assumptions in `docs/scoring_protocol.md` section 6).

### Divider E — Guardrails (3 s)
"What stops a model when it is wrong."

### Slide 11 — Guardrails
- **Section:** Guardrails. **Bonus: guardrails.**
- **Purpose:** the jury retains that every model output passes a rule, and that a rule blocks rather than warns.
- **Text:** "Around the Qualifier: a strict schema; an invalid or undecided answer goes to a person, never to a desk. Around the Drafter: no evidence, no factual claim; every figure in a draft must come from the ledger or an approved document. Before any send: the same policy check on the final text, whoever wrote it, then a human click."
- **Visual (screenshot to capture):** the Workspace on a ticket whose model draft was blocked by the policy check: the block reason visible (for example a figure absent from the evidence, or a refund promise) and the "Approve reply" button disabled. Rules in `flow/policy.py` (`check_draft`, `check_final_text`, `can_approve_model_draft`); described in `docs/design/flow-v2/policy-check.md`.
- **Speaker:** "These are deterministic rules, tested, not a second model's opinion: they can miss a paraphrase, and we say so. Some topics never get a draft at all: a frozen account, a legal threat, a complaint go to a person. The read-only tools are scoped to the merchant of the ticket; another merchant's identifier in a reply is a hard block. We also tested one guardrail that we did not keep: using the model's token probabilities as a confidence threshold. On validation the wrong answers were as confident as the right ones, so we did not adopt it."
- **Time:** 40 s. **Status:** screenshot to capture; needs one seeded ticket that triggers a block (to prepare). Sources: `flow/config.toml` (`human_only_sub_intents`, `human_only_keywords`), `flow/evidence.py`, `flow/field_check.py`, tests in `tests/flow/` (`test_tool_barrier.py`, `test_human_only.py`, `test_drafter_failures.py`); negative result in `ml/confidence/README.md` (AUC 0.60 on intent, val only).

### Divider F — Deployment (3 s)
"Registry and endpoint on GCP."

### Slide 12 — Registry and endpoint
- **Section:** Deployment. **Mandatory item: endpoint on GCP with registry.**
- **Purpose:** the box is ticked with one screenshot that shows both the registered version and where it is served.
- **Text:** "The chosen model is a version in the Vertex AI Model Registry: `keelpay-router-json`, alias `qwen3b-lora-q4`, region europe-west2. It is served from GCP on CPU. An endpoint bills every hour, even idle: ours runs for tests and for this session, then is deleted."
- **Visual (screenshot to capture, see gap 1):** the Vertex AI Model Registry page of `keelpay-router-json` (ID `7308774847222382592`), version with its alias, tab "Deploy and test" listing the endpoint that serves it (name, region, machine type, status). One screen proves registry and endpoint together. If the team deploys on Cloud Run instead of a Vertex endpoint, the visual becomes the Cloud Run service page (URL, revision, image from Artifact Registry) with the registry model named in the caption, and the registry screenshot moves to the appendix.
- **Speaker:** "The lineage is: pipeline run, adapter in the bucket, compression job, 4-bit file with its checksum, registry version. The application reads that same file; its checksum is pinned in the configuration, so the deployed model is exactly the evaluated one. Because an idle endpoint costs as much as a busy one, we kept a rule all along: no endpoint overnight."
- **Time:** 35 s. **Status:** **blocked by gap 1.** Registry facts: `docs/scoring_protocol.md` section 8 "Registration", `docs/roadmap.md` G8. Checksum: `flow/config.toml` (`qualifier_model_md5`) and `flow/deploy/Dockerfile.qualifier`. Cost rule: `README.md` "Cost and teardown".

### Divider G — Monitoring (3 s)
"What we watch once it runs."

### Slide 13 — Monitoring with Langfuse
- **Section:** Monitoring. **Mandatory item: Langfuse.**
- **Purpose:** the box is ticked: one ticket seen as a trace, with timings and versions.
- **Text:** "Each model call and each human action is a span in Langfuse, with its latency and the prompt version used. Prompts are released from Langfuse under a `production` label. Ticket text is never sent to the traces."
- **Visual (screenshot to capture, see gap 2):** the Langfuse trace view of one demo ticket: the tree of spans (`qualify`, `write_draft`, the human action), the latency of each, and the metadata panel showing `prompt_name`, `prompt_version`, `prompt_source`. Emitted by `@observe` in `flow/qualifier.py`, `flow/drafter.py`, `flow/human_actions.py`; metadata set in `flow/prompt_management.py` (`record_prompt_release`).
- **Speaker:** "We use Langfuse for two things: to see where time goes per ticket, and to know which prompt version produced an answer. Inputs and outputs are deliberately not captured. A Langfuse outage does not stop a ticket: the flow falls back to a local prompt and marks the run as such. Business counts, such as tickets per queue, live in our own event store and feed the Dashboard; Langfuse observes the model calls."
- **Time:** 35 s. **Status:** screenshot to capture after a demo session with Langfuse keys set. Sources: `docs/design/flow-v2/prompt-management.md`, `flow/config.toml` (`qualifier_prompt_label`), `flow/metrics_store.py`.

### Divider H — Conclusion (3 s)
"Where we stop, and what decides the next step."

### Slide 14 — Method, economics, next gates
- **Section:** Conclusion.
- **Purpose:** the jury retains the method in one line, what the project could earn with its uncertainty, and that the pilot is conditional.
- **Text:** "Method: fix the contract and the scoring first, beat cheap baselines, read the test sets once, choose on quality against cost. Expected value of the copilot in year one: about 214,000 euros, against about 101,000 for the rules-only alternative; the low case loses 78,000. These are sizing assumptions, not measurements. We stop at a deployed MVP on synthetic data."
- **Visual (chart to make):** a horizontal ladder of gates. Left, passed (filled): dataset frozen, baselines, pipeline run, model chosen on test, registry. Middle, current (outlined): deployed MVP with interface and traces. Right, not passed (empty), each with its threshold: full-flow evaluation on 100 hand-labelled tickets; time saved at or above 13.32 % at constant QA in an A/B on alternating weeks; no increase of serious errors; then pilot decision by Support and Compliance. Sources: `docs/roadmap.md` (G1-G9), `/02_investment_memo.md` (table and "What if we're wrong?"), `/05_metrics.md` sections 3-5, `/governance.md` Session 4 (rollback switch).
- **Speaker:** "The model gate is passed; the product gates are not measured. Our own 50-ticket evaluation of an earlier version of the flow already told us where the work is: routing met the brief's criterion, drafting did not, which is what the evidence and policy nodes answer. If a gate fails, one switch turns drafting off and keeps routing, or turns everything off."
- **Time:** 40 s. **Status:** chart to make. Numbers: `/02_investment_memo.md` (+214,308 weighted, 100,843 next-best, -78,444 low); `/evals/report_v0.md` section 1.

### Slide 15 — Demo (video)
- **Section:** Demo.
- **Purpose:** the jury sees the interface used on live tickets, end to end.
- **Text:** none (full-screen video; one caption line per step).
- **Visual (video to record), about 45 s, four shots:** (1) tickets are injected and move through the Dashboard graph; (2) a clean ticket: fields read by the Qualifier, grounded draft with its sources, "Approve reply", send confirmation; (3) an unclear ticket lands in the Re-router, the agent assigns a desk; (4) a blocked draft cannot be approved. Run with `flow/deploy/demo.ps1 -Inject 6` (container demo) or against the cloud deployment if gap 1 is closed.
- **Speaker:** one sentence per shot, read over the video; no live demo (Qualifier latency is 6 to 7 s per ticket and Docker memory is tight on the laptop, `specs/roadmap.md`).
- **Time:** 45 s. **Status:** to record.

## 3. What we deliberately do not show, and why

- **The severity score, macro-F1, per-field exact match, the six-panel scorecard** (`.local/figures/05_scorecard.png`): one metric explains the choice; the rest is in the appendix for questions.
- **The trap-family chart** (`05_traps.png`): 23 rows, needs a paragraph to read. Appendix.
- **The dataset build chain in detail** (cards, voters, judge, stop rules, API budget): one sentence on slide 6 is enough; the funnel shows the result.
- **MLflow**: real work (`docs/mlops_tracking.md`), but it is a local server with imported history, not required by the exam, and it would dilute the Kubeflow and Langfuse proofs. One appendix slide.
- **The 16-node target table, trust levels L1-L5, Judge and Redraft**: target design and AI Product course vocabulary; slide 4 shows only what runs.
- **The world database and synthetic merchant history** (`flow/world/`): supports the demo, not a graded item.
- **The investment memo tables, lean canvas, user research, A/B sample size**: the AI Product oral covers them; here two sentences and one ladder.
- **The 2-of-30 sendable drafts and grader agreement** (`/evals/report_v0.md`, `/05_metrics.md` section 5): measured on an earlier Drafter (`mistralai/mistral-nemo`, no evidence); the current flow was not re-evaluated, so no draft-quality number goes on a main slide. Said in one clause on slide 14, detailed in the appendix.
- **Costs of training runs in euros**: only the 0.54 euro of the compression job is recorded (`docs/compact_variants.md`); no figure for the GPU run is in the repo, so we give GPU hours, not money.
- **Any claim of "production"**: nothing real is processed; the word used is "deployed MVP on synthetic data".

## 4. Appendix slides and the questions to prepare

Hidden slides, one visual each:

| # | Appendix slide | Visual and source |
|---|---|---|
| A1 | Every system on every measure | `.local/figures/05_scorecard.png`; `docs/scoring_protocol.md` section 8 |
| A2 | Urgent tickets: two ways to fail | `.local/figures/05_urgent_failure_modes.png` (D-q4: 1 of 167 in a wrong desk, 7 of 167 not flagged high) |
| A3 | Traps by family | `.local/figures/05_traps.png` |
| A4 | Size, memory and latency of the variants | `.local/figures/04_file_size_and_ram.png`, `04_latency_mean_p95.png`; `docs/results/d_compact_*_timings.json` |
| A5 | Smoke runs: float32 against float16 | small table from notebook 03 section 2 (654 s against 213 s, loss 0.050 against 0.049) |
| A6 | Full training settings | table from `fine_tuning_component.py`: 4-bit NF4 base, LoRA r 8 / alpha 16 / dropout 0.05 on 7 projection modules, batch 2 with accumulation 2, evaluation every 50 steps, 1,296 steps |
| A7 | The prompt | `ml/qualifier/src/prompt.py` (same instruction in training, evaluation, serving) |
| A8 | Confidence study, negative result | table from `ml/confidence/README.md` (AUC by field, val only; test runs not fetched) |
| A9 | Hand-labelled evaluation of the flow, 13 November | table from `/evals/report_v0.md` section 1 (74 % routed automatically, 1 of 37 misrouted, 88 % valid outputs, drafts not grounded at that commit) |
| A10 | Experiment tracking in MLflow | screenshot of the local `navy-qualifier` experiment; `docs/mlops_tracking.md` |
| A11 | Sizing scenarios | table of `/02_investment_memo.md` |
| A12 | Target flow v2 with the nodes not built | `docs/design/flow-v2/flow_v2.svg`, `node_table_v1.md` |
| A13 | Teardown evidence of the 2 November endpoint | redacted lines of `audit_logs_equipe_navy.csv` (create 17:29 UTC, delete 18:01 UTC) |
| A14 | Prompt releases in Langfuse | screenshot of `navy/qualifier` and `navy/drafter` under `production` |

Questions to prepare:

1. *Is the endpoint up right now? Which model does it serve, and how do you know it is the registered one?* (gap 1; checksum in `flow/config.toml`.)
2. *Where are the evaluation metrics in the pipeline?* The pipeline's Metrics artifact holds losses and trainable parameters; task metrics are computed by `ml/qualifier/scripts/score_predictions.py` on the predictions file the pipeline writes, and logged to MLflow. `evaluation_component.py` is an empty placeholder. Say it plainly.
3. *The "validation loss" is measured on what?* On a slice held out of the training file inside the component (`train_test_split`, `fine_tuning_component.py` line 73), not on `val.csv`; `val.csv` is used for the scored predictions.
4. *Why Qwen2.5-3B and not the course model or a smaller one?* Better in French than the course's Phi-3-mini (notebook 03 header: a stated reason, no measurement in the repo); smaller models cancelled with the reasoning of `docs/compact_variants.md` section 2.
5. *The 4-bit model scores better than the full one on test: is that real?* 4 tickets against 12 of 610; D is better on the traps. The difference between variants is a few tickets; the claim is "no visible loss", not "better" (`docs/scoring_protocol.md` section 8).
6. *Your data is synthetic and labelled by models. What do the scores mean?* Absolute scores are optimistic; the comparison between systems is the finding. On 50 hand-written tickets valid outputs fell to 88 % (`/evals/report_v0.md`).
7. *Runtime uses constrained JSON decoding; the benchmark did not. Same system?* No, and the docs say so (`docs/compact_variants.md` step 4); runtime scores are not reported as benchmark scores.
8. *What does Langfuse give you that your own logs do not? Do you track cost and quality there?* Honest answer depends on gap 2: today spans, latency and prompt versions; Drafter cost and business counts are in the local store; no quality score is pushed to Langfuse.
9. *What happens if Langfuse or the Qualifier is down?* Local prompt fallback marked as such; Qualifier `unavailable` sends the ticket to the Re-router (`flow/qualifier.py`).
10. *How do you know the guardrails work?* Unit tests exist; the seeded-violation catch rate on an evaluation set is not measured (`docs/design/flow-v2/node_table_v1.md` section 5, column "Measured").
11. *What did the whole thing cost on GCP?* 24 pipeline submissions and one 32-minute endpoint appear in the audit log; the repo records GPU hours for the full run and 0.54 euro for the compression job, not a total.
12. *Why a workflow and not an agent?* `/04_architecture.md` section 1.
13. *Does the course require an evaluation harness in CI, model routing, semantic caching, a readiness checklist?* Issue #16 lists them from the shared brief as unconfirmed and unbuilt (#19, #21, #22 open). Have one sentence ready for each.

## 5. Gaps between the course requirements and the repo today

Ordered by risk for the grade.

1. **No endpoint is deployed on GCP today.** `docs/roadmap.md` G8 and `docs/scoring_protocol.md` both say "no endpoint standing". The untracked `audit_logs_equipe_navy.csv` shows one Vertex endpoint created on 2 November at 17:29 UTC and deleted at 18:01 UTC; the registry upload that produced the final model ID came at 18:49, after the deletion, so that endpoint most likely served an earlier upload (the GPU adapter with `ml/qualifier/src/handler.py`), not the registered D-q4 version. This is an inference from timestamps, to confirm with whoever ran it. No screenshot or request/response of that endpoint is in the repo. What runs today is `flow/deploy/compose.demo.yml` on a laptop. The Cloud Run deployment planned in `docs/roadmap.md` and issue #40 is not started; `flow/deploy/Dockerfile.api` and `Dockerfile.qualifier` are ready for it, but nothing in the repo pushes an image to Artifact Registry.
   **Before the slides:** decide between (a) a Vertex endpoint serving the registered D-q4 version, or (b) the Cloud Run service of the roadmap with images in Artifact Registry. Either way: go of the project lead, a stated cost and teardown time, deploy, send one real ticket, capture the console screenshot and the response, record the demo against it, then keep it up for the oral only or delete it. Without this, slide 12 can only show the registry and the 2 November audit lines, and the mandatory item is argued, not shown.
2. **Langfuse monitoring is thin and unverified.** The code sends spans with input and output capture off, plus prompt-version metadata. It sends no token usage, no cost, no quality score, and sets no trace or session identifier per ticket; in the API path each observed function may appear as its own trace rather than one trace per ticket (issue #41, "one correlated trace per ticket", is open, as are #20 and #42). I could not open the Langfuse project, so what the UI shows is unknown.
   **Before the slides:** run a demo session with keys set and look. If spans are scattered, group them under one trace per flow id; mark the two model calls as generations with model name and, for the Drafter, the cost already returned by the provider (`flow/drafter.py` `_cost`); push one score per ticket from the human outcome (approved unchanged, edited, re-routed). Then capture the trace view, and a dashboard view for the appendix.
3. **"With metrics" on Kubeflow is covered only by losses.** The pipeline logs `train_loss`, `eval_loss`, `trainable_params`; `evaluation_component.py` is an empty placeholder and no pipeline computes task metrics. Acceptable if said plainly (question 2). Wiring the existing scorer as a component would need a new billed run; not recommended this late.
4. **No evidence is captured yet for any screenshot slide** (5, 7, 11, 12, 13) nor the demo video. The five charts of slides 6, 8, 9, 10 exist under `.local/figures/` (untracked, regenerated by the notebooks); three charts are to make (slides 2, 3, 14) and one diagram to redraw (slide 4).
5. **The full flow as it runs today has no evaluation.** The only end-to-end numbers (`/evals/report_v0.md`) come from commit `e9ed0d9`, before the evidence tools, the policy check and the change of Drafter model (`flow/config.toml`: `mistral-small-3.2`). A rerun on `evals/eval_set_v1.csv` would give slide 14 a current number; it calls the external Drafter (small cost, synthetic data).
6. **The repo documents contradict the code in places a lecturer may open.** `README.md` (sub-project) still says "only the Qualifier Model exists today" and "The API does not exist yet"; `/04_architecture.md` marks nodes 3, 5, 6, 7, 8, 10, 14, 15 "To build" although `flow/langgraph_app.py` runs them; `/README.md` says the persistent API and UI remain to build. Align them with the slides before the oral.
7. **Confidence study unfinished:** the two test replays were launched on 7 November and never fetched (`ml/confidence/README.md`). The slide claims only the validation result.
8. **Course scope unconfirmed:** issue #16 (own use case accepted, team of 4, CI harness, caching, readiness checklist) is open. The exam list given by the team does not mention these; keep question 13 ready.
9. **The registry state was not rechecked** (`/README.md`: "no current cloud state is certified here"). Open the console once before capturing slide 12.
10. **The audit CSV holds a personal e-mail address and IP addresses** and is untracked: redact before it appears on appendix slide A13, and do not commit it as is.

Not verified by me: the container demo was not started (Docker memory, no billed or heavy run in this task); the 306 test functions under `tests/` were counted, not run.

## 6. Timing table

| # | Slide | Seconds |
|---|---|---|
| 0 | Cover | 5 |
| 1 | Index | 10 |
| A | Divider Context | 3 |
| 2 | Context | 30 |
| B | Divider Framing | 3 |
| 3 | Framing: gates | 30 |
| C | Divider Workflow | 3 |
| 4 | Workflow | 40 |
| 5 | Interface | 20 |
| D | Divider Model | 3 |
| 6 | Task and data | 30 |
| 7 | Kubeflow pipeline | 40 |
| 8 | Training | 40 |
| 9 | Results | 40 |
| 10 | Trade-off | 35 |
| E | Divider Guardrails | 3 |
| 11 | Guardrails | 40 |
| F | Divider Deployment | 3 |
| 12 | Registry and endpoint | 35 |
| G | Divider Monitoring | 3 |
| 13 | Langfuse | 35 |
| H | Divider Conclusion | 3 |
| 14 | Method, economics, gates | 40 |
| 15 | Demo video | 45 |
| | **Total** | **539 s = 8 min 59 s** |

13 content slides (2 to 14), 8 dividers (24 s), cover, index, demo. Content alone: 455 s, of which 295 s (65 %) on the model, guardrails, deployment and monitoring. The total leaves about one minute of margin inside the 10-minute upper bound; if it is used, give it to the demo video (60 s) and to slides 12 and 13.
