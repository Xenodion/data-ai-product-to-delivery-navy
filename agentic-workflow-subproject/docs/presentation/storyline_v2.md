# Storyline v2 — final oral, NAVY / Keelpay support copilot

Version written on 16 November 2026 from the repository state of branch `feat/container-demo` (commit `9b8f7f9`). Lens: an engineer presenting the work to an informed audience that has never heard of the project. One causal chain: what an error costs → what we measured → what we built → what we chose → how it runs → what is still unproven.

Paths are relative to the repository root unless they start with `sub/`, which stands for `agentic-workflow-subproject/`.

## 1. Storyline in 5 lines

1. Keelpay (fictional B2B payments company) answers 36,000 merchant tickets a month by hand; reading, routing, searching and writing take 60 % of the handling time and 1 ticket in 7 first lands in the wrong desk.
2. Before building, we fixed what an error costs, one main metric (the silent error: a confident wrong answer nobody flags) and go/no-go gates, so that a model is kept only if it beats cheaper options.
3. We built a fixed workflow, not an agent: a fine-tuned small model reads the ticket into 7 fields, Python rules route it, read-only tools fetch facts, a second model drafts from those facts only, and a person approves and sends.
4. The fine-tuned model (Qwen2.5-3B + LoRA, trained as a Kubeflow pipeline on Vertex AI, then quantised to run on a CPU) makes 0.7 silent errors per 100 tickets against 33.9 for the best classical baseline, for about 20 euros a month instead of about 255 on a GPU endpoint.
5. The model alone does not meet every bar (1 urgent ticket of 167 in a wrong desk), so rules and people carry the guarantees; we stop at a deployed, traced MVP, and the business value (time saved at constant quality) is still to be measured by the gates that follow.

## 2. Slide by slide

Fourteen content slides (C1–C14), plus cover, index, seven dividers and the demo. Every slide after the index carries the progress bar. Dividers hold a section name only and are passed in 3 seconds.

Speakers: four members, one block each (A: context and framing, B: workflow and guardrails, C: model, D: deployment, monitoring, conclusion). To be assigned by the team.

---

### Cover

- **Section:** opening.
- **Purpose:** name the project and the two courses.
- **Text:** "Keelpay support copilot. A fine-tuned ticket reader inside a human-approved reply workflow." Team NAVY, the two course names, date.
- **Visual:** none (or the flow diagram, dimmed).
- **Speaker:** one sentence: who we are, what the 9 minutes cover.
- **Time:** 5 s. **Material:** exists (text from `README.md`).

### Index

- **Section:** opening.
- **Purpose:** show the path of the talk and who speaks.
- **Text:** seven topics: Context · Framing · Workflow · Model · Guardrails · Deployment and monitoring · Conclusion and demo. Four names (`README.md`, team table).
- **Visual:** the progress bar itself, full length, with the seven labels.
- **Speaker:** "We go from the problem to the running system, and we end with what is not proven yet."
- **Time:** 15 s. **Material:** to make (slide template).

---

### Divider — Context (3 s)

### C1 · Who asked what

- **Section:** Context.
- **Purpose:** the jury knows the company, the users and the problem in 40 seconds.
- **Text:** "Keelpay, a fictional B2B payments company: 2,500 merchants, 36,000 support tickets a month, in French and English. Support agents do everything by hand."
- **Visual:** the path of one ticket today as a horizontal bar of handling time split in three parts: read and route 15 %, find the payment and write 45 %, other actions and send 40 %; a side arrow "1 ticket in 7 goes to the wrong desk first". Data: `01_problem_statement.md` §1 (table, all tagged "given": scenario data, not measured by us).
- **Speaker:** The scenario comes from the AI Product course (project P2). The users are the support agents of four desks: payments, disputes, technical, compliance. The numbers are the scenario's starting data, not our measurements. The request: reduce handling time without lowering quality.
- **Time:** 40 s. **Material:** chart to make.

---

### Divider — Framing (3 s)

### C2 · What an error costs decides what we measure

- **Section:** Framing.
- **Purpose:** the main metric comes from the use case, not from a leaderboard.
- **Text:** "A ticket sent to a person costs a little work. A confident wrong answer can reach the merchant. We count the second first: the silent error."
- **Visual:** three boxes for the three outcomes of a ticket: right (no cost) · sent to a person (about 3 euros of hand-over) · silent error: wrong desk or wrong payment reference, nothing flags it (150 to 400 euros if it reaches a merchant). Data: outcomes in `sub/docs/scoring_protocol.md` §2; costs in `01_problem_statement.md` §3 (assumptions of the sizing, `02_sizing.xlsx`).
- **Speaker:** Accuracy alone hides this: the classical baseline reaches 91.6 % desk accuracy and still makes 33.9 silent errors per 100 tickets (`sub/docs/scoring_protocol.md` §8). The silent error is always read with the share sent to a person, because a system that hands everything over has no error and no use. The euro amounts are assumptions.
- **Time:** 30 s. **Material:** chart to make.

### C3 · Gates fixed before building

- **Section:** Framing.
- **Purpose:** show the governance: each step had a written check, and a failed check is reported as failed.
- **Text:** "Each step had a written check. The fine-tuned model is kept only if it beats the best cheaper option."
- **Visual:** a ladder of gates with a status mark on each rung:
  1. Dataset frozen, splits disjoint — passed.
  2. Cheap baselines scored first — passed.
  3. Fine-tuned model has fewer silent errors than the best baseline, interval of the difference excludes 0 — passed.
  4. Component bars of the product brief: desk accuracy at least 90 % — met (97.5 %); at least 50 % routed automatically — met (82.5 %); no urgent ticket in a wrong desk — not met by the model alone (1 of 167).
  5. Hand-written tickets, whole prototype: brief criterion met; "right desk first time at least 90 %" not met (78 %).
  6. Next (greyed): full-flow evaluation at constant quality, then A/B on time saved.
  Data: gates in `sub/docs/roadmap.md`; selection rule in `sub/docs/scoring_protocol.md` §5; bars and results §4 and §8; rung 5 in `evals/report_v0.md` §1; rung 6 in `02_investment_memo.md`.
- **Speaker:** Test sets were read once, after every setting was chosen on validation. Two rungs are not green and we show them: they are the reason for the guardrails and for the conclusion. The decision of the investment memo is "go for the demo, conditional go for a pilot".
- **Time:** 30 s. **Material:** chart to make.

---

### Divider — Workflow (3 s)

### C4 · The complete workflow

- **Section:** Workflow.
- **Purpose:** one picture of the whole system; the jury sees where the fine-tuned model sits and where people decide.
- **Text:** "A fixed path, not an agent: two models read and write, Python rules decide, a person approves and sends."
- **Visual:** the flow diagram `sub/docs/design/flow-v2/flow_v2.svg`, simplified to the nodes that run today, in order: Intake → Qualifier (fine-tuned, local CPU) → Field check → Routing rules → Context plan → SQL ledger and text search (read-only) → Evidence gate → Drafter (external model) → Policy check → Validator (person) → explicit send, final gate → simulated send; side exit to the Re-router (person) for tickets the flow cannot route. Nodes not built (Judge and redraft loop, override switch) greyed or removed. Source of the built list: `sub/flow/langgraph_app.py` (graph nodes, lines 475–490); status column of `sub/docs/design/flow-v2/node_table_v1.md`.
- **Speaker:** The orchestration is LangGraph with a durable checkpoint: the graph stops at each human step and resumes on the person's action. No model chooses a tool: the context plan is a closed table by desk and sub-intent. The Qualifier is our fine-tuned model; the Drafter is Mistral Small 3.2 through an external API, allowed here because every ticket is synthetic (`sub/flow/config.toml`, `governance.md` Session 3). Nothing is sent to a merchant: the send is simulated.
- **Time:** 45 s. **Material:** exists as SVG; a simplified "as built" version is to make (the SVG is the target flow and is noted as not updated in `node_table_v1.md`).

---

### Divider — Model (3 s)

### C5 · The task: one ticket in, seven fields out

- **Section:** Model.
- **Purpose:** input and output format of the fine-tuned model.
- **Text:** "The model returns one strict JSON object with closed values. When it cannot tell, it answers UNDEFINED and a person takes the ticket."
- **Visual:** left, the French ticket of example 1 ("le virement de 12 500 € … ref: TX-994821 … C'est urgent"); right, its JSON: `intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`. Source: `sub/initial_brief.md` §3, example 1; contract in `sub/ml/qualifier/src/dataset_build/schema.py`.
- **Speaker:** Four intents map to the four desks, with four sub-intents each. Two sentinels: `OTHER` (understood, no class fits) and `UNDEFINED` (cannot tell). An output that breaks the contract is rejected and the ticket goes to a person: the safe failure. The same instruction is used in training, evaluation and serving (`sub/ml/qualifier/src/prompt.py`).
- **Time:** 20 s. **Material:** exists (text); slide layout to make.

### C6 · The dataset: labels known by construction

- **Section:** Model.
- **Purpose:** how 3,205 labelled tickets were obtained and why the labels can be trusted, with the limit stated.
- **Text:** "A scenario card fixes the label, a language model only writes the text. Two blind readers check it; a ticket that fails is set aside, never repaired."
- **Visual:** the funnel per split, attempted against accepted: train 2,657 → 1,922; validation 450 → 293; test_natural 950 → 610; test_traps 645 → 380. Figure `sub/.local/figures/01_split_funnel.png` (rebuilt by `sub/ml/qualifier/notebooks/01_dataset_build.ipynb`, section 5).
- **Speaker:** The whole dataset cost about 3 USD of API calls (journal 1, section 5). The test tickets are written by a different model than the training tickets, so the model is not scored on the style of its own writer. `test_traps` holds 23 families of difficult cases (odd payment references, two amounts, polite but urgent, prompt injection) and is used for diagnosis only. Limit: the labels are checked by language models, not annotated by people.
- **Time:** 30 s. **Material:** exists (local figure, regenerate from the notebook).

### C7 · Fine-tuning as a Kubeflow pipeline on Vertex AI

- **Section:** Model.
- **Purpose:** the mandatory item "fine-tuned on Kubeflow with metrics", shown as it ran.
- **Text:** "Three pipeline steps on Vertex AI: prepare the data, fine-tune with LoRA on one T4 GPU, predict the validation tickets. The run took 2 h 06."
- **Visual:** screenshot of the pipeline run graph in the Vertex AI console, run `keelpay-router-training-pipeline-20261101173631`, with the Metrics artifact of the fine-tuning step open (`train_loss`, `eval_loss`, `trainable_params`). Sources: pipeline `sub/ml/qualifier/src/pipelines/model_training_pipeline.py`; metrics logged in `sub/ml/qualifier/src/pipeline_components/fine_tuning_component.py` (lines 146–148); run name in `sub/docs/compact_variants.md`; duration in `sub/docs/roadmap.md` (G4).
- **Speaker:** Model: Qwen2.5-3B-Instruct, chosen over the course's Phi-3-mini for French. Settings: 3 epochs, LoRA rank 8, alpha 16, dropout 0.05, learning rate 3e-4, 4-bit base, batch 2 with accumulation 2, sequences of 1,024 tokens, loss on the answer only (journal 3, settings table read from the component). The pipeline logs the losses; the use-case metrics are computed by our scorer on the predictions the pipeline writes, and tracked in MLflow.
- **Time:** 25 s. **Material:** screenshot to capture (console read only, nothing billed). See gap G2 for the wording on metrics.

### C8 · What we checked before paying for the run

- **Section:** Model.
- **Purpose:** the R&D: settings were changed for measured reasons, and the curve was read before any score.
- **Text:** "Two free measurements and two short trial runs changed three course settings. The validation loss was still falling at the end: no overfitting."
- **Visual:** the loss curve of the full run, training and validation loss by step; validation loss from 0.045 at step 50 to its minimum 0.0030 at step 1,250, the last evaluation. Figure `sub/.local/figures/03_loss_curve.png`; data `sub/docs/results/d_qwen2.5-3b_full_run_log_history.json` (25 evaluations).
- **Speaker:** Measured with the real tokenizer: 41 % of the training chats (790 of 1,922) are longer than the course's 512 tokens, which would have cut the JSON answer; we set 1,024. The loss is computed on the answer only, about 30 to 50 tokens of 500. On a 40-step trial, float16 gave the same losses as float32 and ran 3.1 times faster (213 s against 654 s), which turned a run of about six hours into two (journal 3, sections 1 and 2). The best checkpoint on validation loss is kept automatically.
- **Time:** 30 s. **Material:** exists (local figure, regenerate from `03_finetuning_vertex.ipynb`).

### C9 · Result: against four cheaper options, on tickets read once

- **Section:** Model.
- **Purpose:** the fine-tuned model is worth keeping, and fine-tuning (not only the model size) is what makes it usable.
- **Text:** "On 610 test tickets, the fine-tuned model makes 0.7 silent errors per 100, against 33.9 for the best classical baseline and 10.5 for the same model without fine-tuning."
- **Visual:** bar chart of silent errors per 100 tickets on `test_natural`, seven systems: majority 78.5 · rules 40.3 · TF-IDF + logistic regression 33.9 · base Qwen prompted 10.5 · fine-tuned GPU 2.0 · 8-bit 1.0 · 4-bit 0.7. Figure `sub/.local/figures/05_test_silent.png`; table `sub/docs/scoring_protocol.md` §8; predictions in `sub/docs/results/*_test_natural_predictions.csv`.
- **Speaker:** All systems are scored on the same tickets; the difference with the best baseline is 0.33 silent error per ticket, 95 % interval 0.30 to 0.37 (paired bootstrap, §8). The prompted base model looks close, but 40 % of its answers break the JSON contract, so it routes only 43 % of tickets by itself. Synthetic tickets are cleaner than real ones: the comparison between systems is the finding, not the absolute score.
- **Time:** 40 s. **Material:** exists (local figure, regenerate from `05_final_evaluation.ipynb`).

### C10 · The choice: same quality on a CPU

- **Section:** Model.
- **Purpose:** the trade-off chart that selected the served model, and that explains the deployment.
- **Text:** "Merged and quantised to 4 bits, the model keeps its quality and runs on a plain CPU: about 20 euros a month for 36,000 tickets, against about 255 for a GPU endpoint that never stops."
- **Visual:** scatter of silent errors per 100 tickets (y) against infrastructure cost per month (x), one point per system: TF-IDF baseline, fine-tuned on GPU, 8-bit, 4-bit. Figure `sub/.local/figures/04_quality_vs_cost.png` (validation split; say so on the chart). Data: `sub/docs/compact_variants.md` §1 and §2; timings `sub/docs/results/d_compact_full_run_timings.json`.
- **Speaker:** The 4-bit file is 1.9 GB, uses about 2.4 GB of RAM and answers in 6.4 seconds per ticket on 8 vCPU, which does not matter for email support. The cost is an estimate: measured seconds times an assumed CPU price. We cancelled the smaller 1.5B and 0.5B models: at most 9 euros a month more to save, for less capacity to copy exact references. The choice was made on validation and confirmed on the test set of the previous slide.
- **Time:** 30 s. **Material:** exists (local figure). Optional: redraw on `test_natural` so that C9 and C10 use the same split (data in `scoring_protocol.md` §8 and `d_compact_test_natural_timings.json`).

---

### Divider — Guardrails (3 s)

### C11 · What the model does not guarantee, and what stops it

- **Section:** Guardrails.
- **Purpose:** guarantees come from rules and people placed around the models; each one answers an observed failure.
- **Text:** "The model's own confidence cannot be the safety net. Each risk has a rule or a person in front of it."
- **Visual:** the flow of C4 as a thin strip, with six stops marked and one short label each:
  1. Contract check: invalid output → Re-router, no draft (`sub/flow/qualifier.py`, `sub/flow/router.py`).
  2. `OTHER` / `UNDEFINED` intent → Re-router; urgency is shown and never changes the path (`sub/flow/router.py`).
  3. Human-only topics (account hold, complaint, regulator, fraud, legal threat) → no draft (`sub/flow/config.toml`, `human_only_*`).
  4. Evidence gate: no verified fact, no factual claim; the draft becomes a clarification question (`sub/flow/evidence.py`).
  5. Policy check on the draft: refund promise, price commitment, legal advice, account-state claim, figure absent from the evidence, another merchant's identifier (`sub/flow/policy.py`).
  6. A person approves, the send is an explicit action, and the same policy code runs again on the final text (`sub/flow/langgraph_app.py`, `human_review` and `simulated_send` nodes).
- **Speaker:** Two findings drove this. On 50 hand-written tickets, 6 Qualifier outputs broke the contract; all 6 landed with a person, none in a desk (`evals/report_v0.md` §1 and §2). And we tested whether token probabilities could flag doubtful answers: on validation they do not separate right from wrong on intent (AUC 0.60), the model is overconfident, so we adopted no threshold (`sub/ml/confidence/README.md`). The read tools are scoped to the merchant of the ticket and can write nothing. The whole set is covered by 306 automated tests (`sub/tests/`).
- **Time:** 40 s. **Material:** chart to make. The effect of stops 3 to 6 on the hand-written set is not measured yet (gap G5): say "built and unit-tested", not "validated".

---

### Divider — Deployment and monitoring (3 s)

### C12 · From the registry to a running service

- **Section:** Deployment.
- **Purpose:** the mandatory items "registry" and "endpoint on GCP", with the reasoning from C10.
- **Text:** "The chosen model is versioned in the Vertex AI Model Registry. It is served on CPU in a container, next to the API that runs the workflow and serves the interface."
- **Visual:** a chain of three screenshots: (1) Vertex AI Model Registry, model `keelpay-router-json`, alias `qwen3b-lora-q4`, region `europe-west2`; (2) the two container images (Qualifier: `llama.cpp` server with the model inside and its checksum verified at build; API: FastAPI + built front end) in Artifact Registry; (3) the running service on GCP with its URL and health check. Sources: registry ID in `sub/docs/scoring_protocol.md` §8; images in `sub/flow/deploy/Dockerfile.qualifier` and `Dockerfile.api`; composition in `sub/flow/deploy/compose.demo.yml`.
- **Speaker:** A Vertex endpoint bills per hour with no scale to zero; we deployed one on 2 November, tested it and deleted it within 32 minutes (`sub/audit_logs_equipe_navy.csv`, `CreateEndpoint` 17:29, `DeleteEndpoint` 18:01 UTC). The trade-off of C10 says CPU is enough, so the demo runs as containers. Teardown is part of the procedure: every billed resource has a stop command and a check.
- **Time:** 40 s. **Material:** screenshot 1 to capture (read only). Screenshots 2 and 3 do not exist: today the two images are built and run locally with Docker Compose only (`sub/flow/deploy/demo.ps1`); nothing is deployed on GCP (`sub/docs/roadmap.md`, G8). See gap G1: this slide cannot be finalised before the deployment decision.

### C13 · Monitoring with Langfuse

- **Section:** Monitoring.
- **Purpose:** the mandatory item "monitoring with Langfuse": what is traced, what is versioned, what is deliberately not sent.
- **Text:** "Every model call and every human action is a traced span. Prompts are versioned in Langfuse; ticket text is not sent to it."
- **Visual:** screenshot of one Langfuse trace of a ticket: the spans (flow, qualifier, drafter, human action) with their durations, and the metadata of a span showing prompt name, label and version (`navy/qualifier`, `production`, version 1). Sources: `@observe` decorators in `sub/flow/pipeline.py`, `qualifier.py`, `drafter.py`, `human_actions.py`; prompt identity recorded by `sub/flow/prompt_management.py`; prompt releases in `sub/docs/design/flow-v2/prompt-management.md` (published 9 November 2026).
- **Speaker:** Spans are recorded with `capture_input=False, capture_output=False`: a design choice, so that no ticket content leaves the system even in a demo. The prompt of each model is fetched by name and label; if Langfuse is down the flow uses a local copy and the trace says so. Latency per node, Drafter cost and gate outcomes are also stored in our own event table (`sub/flow/metrics_store.py`), which stays the source for business counts; Langfuse observes, it does not hold the queues.
- **Time:** 35 s. **Material:** screenshot to capture from a real run. Latency, cost and quality scores are not yet visible in Langfuse itself (gap G3).

---

### Divider — Conclusion (3 s)

### C14 · What it should earn, and what must be true first

- **Section:** Conclusion.
- **Purpose:** recap of the method, the economics as a range with its conditions, and the next gates.
- **Text:** "The sizing gives about +194,000 euros a year in the base case and a loss in the low case. The deciding number is time saved per ticket, and it is not measured yet."
- **Visual:** bar chart of the year-1 annualised net value by scenario: low −78,444 € · base +194,298 € · high +703,462 €, with two reference lines for the alternatives in the base case: do nothing 92,988 € and rules-only context attachment 100,183 €. Under the chart, one line: "Break-even at 5.93 % of handling time saved; 13.32 % to beat the rules-only alternative." Source: `02_investment_memo.md` (table and "How sure?"), computed in `02_sizing.xlsx`.
- **Speaker:** Method in one breath: cost of errors first, cheap baselines before the GPU, one reading of the test sets, the cheapest system that holds the quality, guarantees carried by rules and people. All euro figures are outputs of a model on scenario assumptions, not forecasts. Next gates, in order: rerun the hand-written evaluation on the full flow (the draft quality is not demonstrated: 2 of 30 drafts were sendable before grounding, `evals/report_v0.md`); then an A/B on handling time at constant quality score; a pilot only if time saved passes 13.32 % and no guardrail degrades. We stop today at a deployed MVP on synthetic data.
- **Time:** 45 s. **Material:** chart to make.

---

### Demo (video)

- **Section:** Demo.
- **Purpose:** the mandatory item "an interface to use the flow", seen working.
- **Text:** none; a caption per step.
- **Visual:** screen recording of the app (`sub/frontend/`, served by the API): (1) Dashboard: the workflow graph with live counts after injecting dev tickets; (2) Workspace: open a ticket in the Validator, with the merchant's mailbox, the draft, the facts and sources next to it; approve and send with the "leave open / close" choice; (3) a ticket in the Re-router: correct the desk, the flow re-enters once and a draft appears; (4) a human-only ticket: no draft, reason shown. Launch: `sub/flow/deploy/demo.ps1 -Inject 6`.
- **Speaker:** silent or one sentence per step; no new claim.
- **Time:** 60 s. **Material:** video to record, on the deployed service if G1 is closed, otherwise on the local containers and said so.

## 3. What we deliberately do not show, and why

| Left out of the main deck | Why |
|---|---|
| Macro-F1, per-field accuracy, severity score | One main metric is enough for the argument; the others confirm it and sit in the appendix. The severity points are assumptions. |
| The 23 trap families in detail | Diagnosis material; one sentence on C6 and an appendix chart. A stress-set average must not be read as production performance (`governance.md` Session 3). |
| The validation table next to the test table | Two splits on screen invite confusion. Validation is mentioned as "where settings were chosen"; only C10 is on validation and says so. |
| The full target flow with Judge, redraft loop and override switch | Not built. Showing the target as if it ran would be a false claim; the appendix has the target diagram with a built/not built legend. |
| Investment memo mechanics (probabilities, sensitivities, amortisation) | AI Product course content; the oral needs the range and the two thresholds only. |
| Lean canvas, press release, user research, AI Act table | Framing work that does not change any engineering decision shown here; governance appears through gates, human steps and data location. |
| MLflow tracking and lineage import | Real work, but local to one machine and partly a historical import (`sub/docs/mlops_tracking.md`); one spoken mention on C7. |
| The synthetic merchant world database (history threads, ledger) | Supports the demo; it is visible in the video through the mailbox. Explaining it costs a slide and proves little about the course subject. |
| Dataset generation internals (prompt versions, three calibration runs, stop rules) | One sentence on C6; appendix for the question "how do you know the labels are right". |
| Hyperparameter sweep | The pipeline compiles but never ran (`sub/README.md`, status table). We say "course settings plus three measured changes", not "tuned". |
| Drafter quality numbers on the main path | Measured once, before evidence and policy checks existed (2 of 30 sendable). It is stated in the conclusion as the open point rather than shown as a result. |

## 4. Appendix slides and the questions to prepare

Hidden slides, one visual each.

| # | Appendix slide | Visual and source | Question it answers |
|---|---|---|---|
| A1 | All measures, all systems | six-panel scorecard `sub/.local/figures/05_scorecard.png`; table `sub/docs/scoring_protocol.md` §8 | "What about accuracy, F1, valid JSON?" |
| A2 | Trap families | `sub/.local/figures/05_traps.png`; `05_final_evaluation.ipynb` §2 | "Where does the model still fail?" Odd ids and double amounts; malformed ids are mostly rejected by the contract. |
| A3 | Urgent tickets | `sub/.local/figures/05_urgent_failure_modes.png` | "You said zero urgent misroutes was the bar." 1 of 167 on the model alone; urgency never changes the path and every reply is reviewed. 167 tickets cannot prove zero. |
| A4 | Confidence study | AUC per field on validation, `sub/ml/confidence/README.md` (chart to make) | "Why not a confidence threshold?" Intent AUC 0.60; rejecting the one silent error would send 41 % of tickets to a person. Test-split replays were launched but are not analysed. |
| A5 | Hand-written evaluation | table of `evals/report_v0.md` §1 | "Does it hold on real-looking tickets?" 74 % routed automatically, 1 of 37 misrouted, 0 of 8 urgent; but 88 % valid outputs and 78 % right first time. |
| A6 | Two graders and an LLM judge | `05_metrics.md` §5 | "How do you grade drafts?" 80 % agreement, kappa 0.33; judge agrees with the humans on 23 of 24 but is more lenient. |
| A7 | Dataset review chain | pass rate over three calibration runs `sub/.local/figures/01_chain_pass_rate.png`; journal 1 §3–4 | "Who labelled the data?" Card fixes the label; two blind readers, a judge on disagreement; quarantine never reused. |
| A8 | Latency and memory | `sub/.local/figures/04_latency_mean_p95.png`, `04_file_size_and_ram.png` | "Is 6 seconds acceptable? What about load?" Asynchronous email; one request at a time per container today. |
| A9 | Cost of the project so far | small table: dataset about 3 USD (journal 1), training 2 h 06 of T4 (`roadmap.md` G4), quantisation job about 0.54 euro (`compact_variants.md`) | "What did it cost to build?" The euro price of the T4 run is not recorded in the repo: say so. |
| A10 | Target flow, built and not built | `flow_v2.svg` with a legend from `node_table_v1.md` | "What is missing from the target?" |
| A11 | Data location and the demo exception | two-column table from `governance.md` Session 3 and `README.md` (demo vs fictional production) | "You send tickets to an external API?" Synthetic only; in the scenario's production everything stays in Keelpay's cloud. |
| A12 | Metric hierarchy and rollback | the primary / guardrails / counter-metrics table of `05_metrics.md` §3; `copilot_mode` switch from `governance.md` Session 4 | "How would you know it harms in production, and how do you stop it?" The switch is specified, not built (issue #60). |
| A13 | Sizing sensitivity | 10 % saved → 55.1 k€; 30 % → 326.4 k€ (`02_investment_memo.md`) | "How fragile is the business case?" |

Other questions to prepare, with the honest answer:

- **"Is this an agent?"** No. A workflow with a fixed path; no model chooses a tool (`node_table_v1.md` §1). The course title is broader than what the use case needs.
- **"Why fine-tune instead of prompting a large model?"** The prompted 3B base breaks the contract on 40 % of tickets. A large hosted model was not benchmarked: the scenario keeps tickets in Keelpay's cloud. Say that the comparison with a large API model is missing.
- **"Why Qwen 3B and not smaller?"** Cancelled on cost reasoning, not measured (`compact_variants.md` §2). It is an argument, not a result.
- **"Are your scores inflated by synthetic data?"** Yes in absolute terms; the hand-written set shows it (88 % valid against 97.9 %). The ranking of systems is the claim.
- **"Does the benchmark model equal the served model?"** Same GGUF file (md5 checked at image build), but the runtime uses constrained structured output, which the benchmark did not; runtime results are not reported as benchmark results (`compact_variants.md` §1, step 4).
- **"What does the pipeline log as metrics?"** Train loss, eval loss, trainable parameters, TensorBoard files. The evaluation component is not in the pipeline; scoring is local (gap G2).
- **"What is in Langfuse exactly?"** Spans and prompt versions; no inputs or outputs by choice; no scores yet (gap G3).

## 5. Gaps between the requirements and the repository, and what to do before the slides

Ordered by risk for the grade.

| # | Requirement | State found in the repo | To do before the slides |
|---|---|---|---|
| G1 | "Un endpoint déployé GCP avec registry" | Model registered in Vertex AI Model Registry (`keelpay-router-json`, ID `7308774847222382592`, `scoring_protocol.md` §8). A Vertex endpoint was created and deleted on 2 November (audit log); no record in the docs of what it served or of its test, and no screenshot. Nothing is deployed today. The app runs in local containers only; images are not pushed to any registry; no Cloud Run or Artifact Registry file exists under `sub/flow/deploy/`. Issue #40 open. | Decide the endpoint type and get the project lead's go (billed): either the container demo on Cloud Run with both images in Artifact Registry, or a short-lived Vertex endpoint for the screenshots. Ask the lecturer whether Cloud Run counts as "endpoint". Write the teardown, capture the screenshots, record the demo on it. Until then C12 states "runs in local containers; registered on Vertex; endpoint deployed and removed on 2 November". Also check in the console which model the 2 November endpoint served. |
| G2 | "LLM fine-tuné sur Kubeflow avec metrics" | The pipeline ran on Vertex (training, base model, compact, inference, confidence). The fine-tuning component logs losses as a KFP Metrics artifact. `evaluation_component.py` is a one-line stub and the pipeline file says the evaluation step is "added once its design is agreed". Use-case metrics are computed locally by `scoring.py` and logged to a local MLflow. | No billed rerun needed. Capture the pipeline graph and the Metrics artifact. Word C7 exactly: losses in the pipeline, use-case metrics from the scorer. If time allows, implement the evaluation component so that the next run shows the scores in the pipeline; do not claim it before it has run. |
| G3 | "Monitoring avec Langfuse" | `@observe` spans on the flow entry, Qualifier, Drafter and human actions; prompts `navy/qualifier` and `navy/drafter` published under `production`; flush on API shutdown. No input/output capture (by design), no token or cost on the Langfuse spans (Drafter cost goes to the local SQLite store), no scores, no dashboard. Not verified here that the LangGraph API path produces one coherent trace per ticket. Issues #41 and #20 open. | Run the container demo with Langfuse keys, inject tickets, check the trace tree in the UI and capture it. Minimum addition worth doing: attach latency, Drafter cost and gate outcomes as span metadata, and the human action (approved unchanged / edited / rejected) as a Langfuse score; then a dashboard screenshot shows latency, cost and a quality signal, which is what issue #20 asks. |
| G4 | "Une interface pour utiliser le flow" | Built: FastAPI (`sub/flow/api.py`, tickets, queues, actions, send, overview) and React front end (Dashboard, Workspace with Re-router and Validator, merchant mailbox). Five front-end files are modified and two are untracked in the working tree; no authentication; single user. | Commit the front-end work, then record the video on a clean start (`demo.ps1 -Reset`). |
| G5 | Guardrails as a plus | Built and unit-tested (306 tests). Not measured end to end: the only whole-prototype evaluation (`evals/report_v0.md`, 13 November) predates the field check, evidence gate, policy check and human-only list; then, 4 of 4 tickets that belong to a person got a draft and no draft was grounded. Seeded-violation tests of the policy check are not reported. | Rerun `flow.runner --tickets ../evals/eval_set_v1.csv` once on the current flow (local Qualifier, Drafter API cost only) and report: drafts on Re-router tickets (expected 0), policy blocks, sendable drafts on the 30-case sample. Without the rerun, C11 says "built and tested", and the conclusion keeps draft quality as open. |
| G6 | Economics and next gates (conclusion) | Memo and metrics exist (`02_investment_memo.md`, `05_metrics.md`). `06_ab_protocol.md`, `07_operations.md`, `08_launch_memo.md` do not exist (issues #63, #64, #65); the override switch is specified only (#60). | The conclusion may name the next gates but must present the A/B protocol and the rollback switch as planned. If `06` is written before the oral, cite its sample size on C14. |
| G7 | Numbers must come from the repo | Charts live in `sub/.local/figures/` (untracked, one machine). `sub/audit_logs_equipe_navy.csv` is untracked and holds personal email addresses and IP addresses. Small inconsistencies: p99 token length 813 (`sub/README.md`) against 816 (journal 3); CPU cost 19 to 21 euros depending on the split. | Regenerate the figures from the notebooks into a tracked presentation folder. Do not commit the audit log as is; quote the two timestamps only. Use "41 % over 512 tokens" and "about 20 euros". |
| G8 | Consistency of the repository if the jury opens it | Stale status lines: root `README.md` says the API, UI and deployment "remain to be built"; `sub/README.md` says "only the Qualifier Model exists today" and "The API does not exist yet"; `flow_v2.svg` is the target, not the built flow; `spec.md` and `governance.md` still carry two rules replaced by flow v2 (`node_table_v1.md`). | Update the status paragraphs and tag the release before the oral (the course asks for a `v1.0` tag, root `README.md`). |
| G9 | Confidence study | Validation analysed; the two test replays were launched on 7 November and never fetched or analysed (`sub/ml/confidence/README.md`). | Either fetch and apply the frozen rule once, or present it as "validation only" (appendix A4 does this). |

## 6. Timing table

| Block | Slides | Seconds |
|---|---|---|
| Cover and index | 2 | 20 |
| Dividers | 7 × 3 s | 21 |
| Context | C1 | 40 |
| Framing | C2, C3 | 30 + 30 = 60 |
| Workflow | C4 | 45 |
| Model | C5, C6, C7, C8, C9, C10 | 20 + 30 + 25 + 30 + 40 + 30 = 175 |
| Guardrails | C11 | 40 |
| Deployment and monitoring | C12, C13 | 40 + 35 = 75 |
| Conclusion | C14 | 45 |
| Demo video | 1 | 60 |
| **Total** | 14 content slides, 25 slides shown | **581 s = 9 min 41 s** |

Content slides alone: 480 s (8 min). The model block is 36 % of the content time, which matches the weight the exam gives to the fine-tuning R&D. If the talk must fit 9 minutes, cut the demo to 30 s and C6 to 20 s (581 − 30 − 10 = 541 s, 9 min 01 s) rather than removing a slide.
