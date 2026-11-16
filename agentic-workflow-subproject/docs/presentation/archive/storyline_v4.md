# Storyline v4: final oral, NAVY / Keelpay Support Copilot

Written on 16 November 2026 from the repository on branch `feat/container-demo`, independently of the other versions. Lens of this version: a listener who has never seen a payment company, a support desk or an LLM pipeline follows every step, and each technical choice is introduced by the decision rule that caused it (a gate, a measure taken before spending, a person kept in control). Governance is never a separate chapter: it is the "because" of each slide.

Paths are relative to the repository root. `sub/` stands for `agentic-workflow-subproject/`.

## 1. Storyline in 5 lines

1. A payment company's support team answers 36,000 merchant messages a month by hand; most of the time goes into reading, finding the payment and writing, and one message in seven first reaches the wrong team.
2. Before building, we priced the project against two cheaper options and fixed what would make us stop: it is worth it only above about 13 % of handling time saved, and the one error we refuse is the "silent" one, a wrong reading that nobody flags.
3. So the product is a fixed workflow, not an autonomous agent: a small model reads the message, rules route it, read-only tools fetch facts, a second model drafts, and a person approves and sends every reply.
4. The reading model was fine-tuned on Vertex AI through nine gates (dataset, baselines, smoke run, full run, validation, CPU variant, tests read once, registry): it makes 0.7 silent errors per 100 tickets against 33.9 for classical ML, and runs on a CPU for about 20 euros a month.
5. A test on tickets we wrote by hand met the product criterion and failed a stricter gate; each fault became a rule in the code. We stop at a containerised MVP with a registered model, and the pilot stays conditional on gates that are not yet passed.

## 2. Slide by slide

Fourteen content slides. Vocabulary rule for the whole deck: say "message" or "ticket" (defined once on slide 1), "team" for desk, "reading model" for Qualifier, "writing model" for Drafter, "wrong reading that nobody flags" for silent error. The project names appear once in small type so the jury can match them with the repository.

### Cover

- Text: "Keelpay Support Copilot. Reading, routing and drafting merchant support tickets, with a person sending every reply." Team NAVY, course name, date.
- Visual: none, or the product screenshot of slide 4 dimmed.
- Time: 10 s. Status: to make.

### Index

- Text: the eight topics (Context, Framing, Workflow, Model, Guardrails, Deployment, Monitoring, Conclusion and demo) and the four names: Alexandre Waerniers, Vincent Lamy, Nahel Bachiri, Yoni Mahieddine (`README.md`).
- Visual: the progress bar that every following slide repeats.
- Time: 10 s. Status: to make.

### Divider: Context (3 s)

### Slide 1. One ticket, handled by hand today

- Section: Context.
- Purpose: the jury knows who the company is, who the user is, and what the work looks like, with no prior knowledge.
- Text on slide: "Keelpay is a fictional payment company: 2,500 merchants send its support team 36,000 messages a month. A support agent spends about 10 minutes on each one, and one message in seven first lands with the wrong team."
- Visual: one horizontal bar of 10 minutes split in three labelled parts: "read and send to the right team" 15 %, "find the payment and write the reply" 45 %, "check, act, send" 40 %; above it, a three-line real example of a ticket in French (taken from `sub/data/dataset/train.csv`); beside the first part, the note "1 in 7 goes to the wrong team first". Sources: shares and 1 in 7 are scenario data, `README.md` section "Shared scenario" and `01_problem_statement.md` section 1; 10 minutes is an assumption, `02_sizing.xlsx` `Inputs!G7`.
- Speaker: "The course gave us a scenario: a B2B payment company whose merchants write when a payment is late, a customer disputes a charge, the API fails, or a compliance document is missing. Four teams answer. Today an agent reads the message, decides which team it belongs to, looks up the payment, writes, and sends. The first two blocks are where the time goes. These figures are the scenario's, not our measurements."
- Time: 40 s. Status: chart to make (simple bar); ticket text exists.

### Divider: Framing the need (3 s)

### Slide 2. We priced it before building it

- Section: Framing.
- Purpose: the project has a break-even point stated in the user's own unit (time saved), and two cheaper alternatives it must beat.
- Text on slide: "The copilot beats the cheaper option, a rule that only attaches the payment to the ticket, only if agents save more than 13 % of their handling time. Our base assumption is 20 %; nothing proves it yet."
- Visual: line chart, x = share of handling time saved (10 to 30 %), y = net value per year in euros, five points: 55 k at 10 %, 123 k at 15 %, 191 k at 20 %, 259 k at 25 %, 326 k at 30 % (`02_sizing.xlsx` `Decision!C32:C36`); one horizontal line at 100 k, "rules only, no AI" (`Decision!D23`); one vertical marker at 13.3 % (`Decision!D57`) and one at our base assumption 20.3 % (`Flow!D15`).
- Speaker: "Before any model we built a sizing sheet with three scenarios. The pessimistic one loses 78,000 euros a year, the base one earns 194,000, and the probability-weighted value is 214,000. The decision was not 'go': it was 'go to build and measure a demo, conditional go for a pilot'. That 13 % line is the reason every later slide measures something."
- Numbers spoken: −78,444, +194,298, +214,308 (`02_sizing.xlsx` `Decision!C17`, `D17`, `D19`; also `02_investment_memo.md`).
- Time: 35 s. Status: chart to make from the workbook.

### Slide 3. The error we chose to measure

- Section: Framing.
- Purpose: introduce the single concept that drives the model work, in plain words, and the rule that scores were fixed before results.
- Text on slide: "A ticket can end three ways. The one we count first is the third: sent to a team with a wrong team or a wrong payment reference, and nothing says so."
- Visual: a three-branch diagram from one ticket: "read correctly" (no cost), "handed to a person" (a few minutes, no damage), "wrong reading that nobody flags" (the draft is built on it, the merchant may act on it; 150 to 400 euros in the sizing). Sources: outcome definitions `sub/docs/scoring_protocol.md` section 2; hand-over about 3 euros `02_sizing.xlsx` `Flow!D28`; error cost 150 / 400 / 300 euros `Inputs!D30:D32` (assumptions).
- Speaker: "Accuracy would have hidden the problem: a model that hands every doubt to a person is safe, a model that guesses is not. So the main score is the rate of wrong readings that nobody flags, and the model is told to answer 'undefined' rather than guess. Three bars came from the product brief and were written before any training: at least half of the tickets routed without a person, the right team nine times in ten, and no urgent ticket in a wrong team. Settings are chosen on a validation set; the test sets are read once."
- Sources for the bars: `sub/docs/scoring_protocol.md` section 4; `03_product_brief.md` section 7; rule "read once" `sub/docs/roadmap.md` "Rules that stay fixed".
- Time: 30 s. Status: diagram to make.

### Divider: The workflow (3 s)

### Slide 4. The workflow: models propose, rules decide the path, people send

- Section: Workflow.
- Purpose: the jury sees the whole chain once, understands that it is a fixed path and where the two people stand.
- Text on slide: "The path is drawn in advance. Two models read and write; rules choose the team and check the text; two people correct and approve. Nothing is sent, refunded or written to the ledger by the system."
- Visual: the flow diagram, simplified to eight boxes in one line with three colours (model, rule or tool, person): ticket in → reading model → field check and routing rule → read-only lookups (payment ledger, approved policies) → evidence gate → writing model → policy check → Validator (person) → final check and simulated send; one side lane "Re-router (person)" fed by "unclear, invalid, sensitive". Base: `sub/docs/design/flow-v2/flow_v2.svg`, redrawn lighter. Built state to mark honestly on the drawing: every box up to the simulated send exists in `sub/flow/langgraph_app.py` (nodes intake, qualifier, field_check, routing, context_plan, tools, evidence_gate, drafter, policy_check, human_review, simulated_send); the optional Judge and the override switch are designed, not built (`04_architecture.md` sections 3 and 6; issues #59, #60).
- Speaker: "We chose a workflow, not an agent: no model picks a tool or a next step, so the cost per ticket is bounded and every step can be explained and switched off. The interviews gave the last box: 'I would never let any tool send an email about money without my final review.' A ticket the system cannot place goes to a person with no draft."
- Sources: `04_architecture.md` section 1; quote `03_user_research.md` "What we heard" row 4 (classmates playing support roles, say so if asked).
- Time: 45 s. Status: diagram to redraw from the SVG.

### Divider: The model (3 s)

### Slide 5. What the fine-tuned model does: a message in, seven fields out

- Section: ML.
- Purpose: the input and output formats, concretely.
- Text on slide: "Input: the raw message, French or English. Output: one JSON object with seven fields, from closed lists. 'UNDEFINED' means 'I cannot tell': it sends the ticket to a person instead of guessing."
- Visual: side by side, a real ticket and its JSON (`intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`), with two callouts: "team is derived from intent by a rule" and "the reference is used to look up the payment". Source: example in `spec.md` section 3; contract `sub/ml/qualifier/src/dataset_build/schema.py`; instruction `sub/ml/qualifier/src/prompt.py`.
- Speaker: "The same instruction is used for training, evaluation and serving, built from the same file as the validator, so the two cannot drift. An answer that breaks the contract is not repaired silently; it goes to a person."
- Time: 25 s. Status: screenshot to compose from existing text.

### Slide 6. A dataset we could trust enough, for three dollars

- Section: ML.
- Purpose: there was no data; show how labels were made and checked, and the limit.
- Text on slide: "No real tickets exist, so we generated them: a scenario card fixes the label, one model writes the message, two others read it blind, a judge settles disagreements, and a ticket that fails is set aside, never repaired. The test tickets are written by a different model than the training ones."
- Visual: funnel chart per split, generated → accepted, ending in train 1,922 / validation 293 / test 610 / traps 380 (`sub/.local/figures/01_split_funnel.png`, built in `sub/ml/qualifier/notebooks/01_dataset_build.ipynb`).
- Speaker: "3,205 tickets for about 3 dollars. About a third were rejected by the review chain. The limit is stated in our governance file: labels come from agreement between models, not from human annotation, so absolute scores are optimistic and only comparisons between systems count. That is why we later wrote 100 tickets by hand."
- Sources: counts `sub/docs/roadmap.md` G1; cost and acceptance rates (72 / 65 / 64 / 59 %) `sub/ml/qualifier/notebooks/01_dataset_build.ipynb` sections 5; limit `governance.md` Session 3 and `sub/docs/scoring_protocol.md` section 7.
- Time: 30 s. Status: figure exists (check legibility at slide size).

### Slide 7. Fine-tuning: three checks before paying for the GPU

- Section: ML.
- Purpose: show the process, not only the score: what was verified at each paid step.
- Text on slide: "Qwen2.5-3B with LoRA adapters, as a Kubeflow pipeline on Vertex AI. A trial run of a few minutes came first; the full run took 2 h 06 on one T4 GPU. Validation loss was still falling at the end: no overfitting."
- Visual: the loss curve, training and validation loss by step, minimum 0.0030 at step 1250 (`sub/.local/figures/03_loss_curve.png`; data `sub/docs/results/d_qwen2.5-3b_full_run_log_history.json`).
- Speaker: "We kept the course settings: 3 epochs, rank 8, learning rate 3e-4, 4-bit base model. We changed three things after measuring our data: sequences of 1,024 tokens because 41 % of our examples were longer than 512 and the answer comes last; the loss computed on the answer only; and float16, which a trial run on 200 tickets showed to be three times faster with the same loss. The best checkpoint on validation loss is kept. The pipeline logs training loss, validation loss and the curve as artifacts."
- Sources: settings `sub/ml/qualifier/src/pipeline_components/fine_tuning_component.py` and `sub/README.md` "Training settings"; 41 %, smoke runs 654 s vs 213 s `sub/ml/qualifier/notebooks/03_finetuning_vertex.ipynb` sections 1-2; 2 h 06 `sub/docs/roadmap.md` G4 (7,568 s in the log history).
- Time: 40 s. Status: figure exists. A screenshot of the pipeline graph in the Vertex console would be a better proof of "on Kubeflow": to capture (reading the console is free).

### Slide 8. Compared with simpler options on the same 610 tickets

- Section: ML.
- Purpose: fine-tuning was not assumed to be needed; it was compared with cheaper rungs and with the same model without fine-tuning.
- Text on slide: "Wrong readings that nobody flags, per 100 tickets: keyword rules 40, classical ML 34, the same model only prompted 10.5, fine-tuned 0.7. The prompted model also breaks the output format four times in ten."
- Visual: horizontal bar chart of silent errors per 100 tickets for B0, B1, B2, B3, D, D-q8, D-q4 with 95 % intervals (`sub/.local/figures/05_test_silent.png`; table `sub/docs/scoring_protocol.md` section 8).
- Speaker: "Each system is scored once on tickets written by another model than the training set. The selection rule was written before: keep the fine-tuned model only if its interval against the best baseline excludes zero. It does. Classical ML meets our first two bars, the right team and the share routed alone, and still gets one reference in three wrong: that is why the bars alone were not the criterion. One bar is not met: one urgent ticket of 167 lands in a wrong team; we say so and cover it with the human checks."
- Sources: 40.3 / 33.9 / 10.5 / 0.7, valid JSON 60.3 %, 1 of 167, bootstrap intervals: `sub/docs/scoring_protocol.md` section 8; rule section 5.
- Time: 30 s. Status: figure exists.

### Slide 9. The trade-off that chose the deployed model

- Section: ML.
- Purpose: the champion is chosen on quality against running cost, and a planned experiment was cancelled for a stated reason.
- Text on slide: "Compressed to 4 bits, the model keeps its quality and runs on a plain CPU: about 20 euros a month for 36,000 tickets, against about 255 for a GPU kept on. We cancelled the smaller models: at most 9 euros a month to save, and more errors on references to risk."
- Visual: scatter, x = estimated monthly serving cost, y = silent errors per 100 tickets, points B2, B3, D, D-q8, D-q4 (`sub/.local/figures/04_quality_vs_cost.png`, validation set; cost is a scenario assumption, as the figure subtitle says).
- Speaker: "The answer is 35 tokens of JSON, and support mail is not a live chat: 6 seconds per ticket is invisible. So the lower-left point wins. This choice is what makes the deployment cheap enough to leave running during a demo, and it keeps the model inside the company's own cloud, which the scenario requires for real tickets."
- Sources: 6.43 s, 2.4 GB, 20 and 255 euros, cancellation reasons: `sub/docs/compact_variants.md` sections 1-2; data boundary `governance.md` Session 3 "Location".
- Time: 30 s. Status: figure exists. The figure is on validation; say "validation" aloud, the test reading is slide 8.

### Divider: Guardrails (3 s)

### Slide 10. Then we tested the chain on tickets we wrote by hand

- Section: Guardrails.
- Purpose: the model score is not the product; a harder, human-labelled test met the product criterion, failed a stricter gate, and found three faults.
- Text on slide: "50 tickets written and labelled by hand before the run. Product criterion met: 74 % routed without a person, 1 wrong team in 37, no urgent ticket misrouted. Stricter gate for the pilot not met: 78 % right first time against 90 % asked."
- Visual: paired bars "measured vs required" for four lines: routed automatically 74 % (bar ≥ 50 %); wrong team among those 2.7 % (today 14.3 %); urgent in wrong team 0 of 8 (bar 0); right team first time 78 % (gate 90 %), the last one in a different colour because it fails. Source: `evals/report_v0.md` section 1.
- Speaker: "These tickets are messier than the generated ones: phone one-liners, forwarded threads, instructions hidden in a log. The run found three faults. The model's whole answer was rejected for one bad field, six times. It abstained on four clear tickets. And the flow wrote a draft for every ticket, including the four that only a person should answer. Two of us then graded 30 drafts separately: both would send only two as they were. The sample is small, and the interval on the 2.7 % reaches 13.8 %, just under today's rate."
- Sources: `evals/report_v0.md` sections 1-3; graders and agreement 24 of 30 `05_metrics.md` section 5.
- Time: 30 s. Status: chart to make. Important caveat for the speaker: this run is on the flow at commit `e9ed0d9`, before the fixes of slide 11; the rerun on the 100-case set is not done (see Gaps).

### Slide 11. Each fault became a rule in the code

- Section: Guardrails.
- Purpose: guardrails are specific, deterministic, and traced to a measured fault or a stated risk.
- Text on slide: "Five places where the flow stops itself: a field check before routing; no draft for unclear or sensitive tickets; no fact without evidence from the ledger or an approved policy; a policy check that blocks promises and figures not in the evidence; a person who approves, and a last check on the exact text sent."
- Visual: screenshot of the Workspace on one ticket where a guardrail fired: either a ticket with no draft and the reason `HUMAN_ONLY_TOPIC`, or a draft marked blocked with its reason, next to the Approve and Send buttons (front end `sub/frontend/src/App.tsx`; run with `sub/flow/deploy/demo.ps1`).
- Speaker: "The first two rules are the direct answers to the hand-written test; they are lines of the product specification, version 2. The policy check is the same code before the reviewer and on the final text, whoever wrote it: it blocks a refund promise, a price, a statement about an account, a figure that is not in the evidence, and any other merchant's identifier. A blocked draft cannot be approved. These are pattern rules, not a judge of meaning: the person remains the check on meaning. One planned control is not built yet: the single switch that turns drafting off and leaves manual work usable."
- Sources: `spec.md` section 10 (miss → spec line); `sub/flow/field_check.py`, `sub/flow/evidence.py`, `sub/flow/policy.py`, `sub/flow/human_actions.py`; rules described in `sub/docs/design/flow-v2/policy-check.md` and `drafter.md`; human-only list `sub/flow/config.toml` (`human_only_sub_intents`, `human_only_keywords`); switch `04_architecture.md` section 6 and issue #60; 424 local tests pass (`uv run pytest`, run on 16 November 2026 for this document).
- Time: 40 s. Status: screenshot to capture.

### Divider: Deployment (3 s)

### Slide 12. From the pipeline to a running service

- Section: Deployment.
- Purpose: the chain training → registry → served model → application is real and reproducible, and cost discipline is part of it.
- Text on slide: "The chosen model is registered in the Vertex AI Model Registry. The service is two containers: the model on CPU with a checksum on its file, and the API that also serves the interface. A GPU endpoint was deployed for a test and deleted the same day: an endpoint bills while idle."
- Visual: a four-box chain with one screenshot inside: Kubeflow pipeline on Vertex → Model Registry (screenshot of `keelpay-router-json`, alias `qwen3b-lora-q4`, region `europe-west2`) → model container (`llama.cpp`, file checked by md5) → API container with the built front end. The last box carries the real hosting state on the day of the talk (see Gaps: nothing is standing on GCP today).
- Speaker: "No endpoint was allowed before the test sets were read and a model chosen: that is gate 8. Every billed command states what it costs and what stops it. The container image holds only synthetic data and no secret. The same two containers start with one command locally; on GCP they go to Cloud Run on CPU, which scales to zero."
- Sources: registry ID `7308774847222382592` `sub/docs/scoring_protocol.md` "Registration" and `sub/docs/roadmap.md` G8; containers `sub/flow/deploy/Dockerfile.qualifier`, `Dockerfile.api`, `compose.demo.yml`, `demo.ps1`; md5 `sub/flow/config.toml`; cost rule `sub/README.md` "Cost and teardown"; endpoint created 2 November 17:29 UTC and deleted 18:01 UTC in `sub/audit_logs_equipe_navy.csv` (untracked file with a personal e-mail: cite it, do not show it).
- Time: 35 s. Status: diagram to make; registry screenshot to capture; endpoint or Cloud Run screenshot depends on the gap below.

### Divider: Monitoring (3 s)

### Slide 13. Monitoring: what Langfuse sees, and what it is not allowed to see

- Section: Monitoring.
- Purpose: each ticket leaves a trace per step with the versions used; prompts are released like code; the trace store is not the source of truth.
- Text on slide: "Each ticket is one trace: one span per step, with its duration, the model and the prompt version. Prompts are published in Langfuse under a 'production' label. Ticket text and drafts are not sent to it."
- Visual: screenshot of one Langfuse trace of a ticket (spans qualifier, drafter, human action, with the metadata `prompt_name`, `prompt_version`), cropped to be readable.
- Speaker: "Langfuse answers 'how long, how much, which version'. The counts that matter for operations, tickets waiting, approved, sent, are kept in our own database, because a monitoring outage must not lose a ticket: if Langfuse is down, the flow uses a marked local copy of the prompt and continues. Inputs and outputs are excluded from the traces on purpose: in the scenario, real tickets never leave the company's cloud."
- Sources: `sub/flow/prompt_management.py`; `@observe(capture_input=False, capture_output=False)` in `sub/flow/qualifier.py`, `drafter.py`, `pipeline.py`, `human_actions.py`; prompt releases `sub/docs/design/flow-v2/prompt-management.md`; local metrics `sub/flow/metrics_store.py`; design `sub/docs/design/flow-v2/measures-and-gates.md` "Metric storage and delivery".
- Time: 25 s. Status: screenshot to capture; no Langfuse screenshot exists in the repository (see Gaps).

### Divider: Conclusion (3 s)

### Slide 14. Where we stop, what it should earn, what must be true next

- Section: Conclusion.
- Purpose: recap the method as a sequence of gates with their real verdicts, restate the economics as a condition, and name the next gates.
- Text on slide: "We stop at a working MVP on synthetic data. The expected value, about 214,000 euros a year, holds only if agents save more than 13 % of their time at equal quality. Routing alone is estimated at about 9 %; drafting is not measured yet."
- Visual: one gate track, left to right, each gate with a verdict mark. Passed: dataset; baselines; trial run; full run; better than baselines on validation; CPU variant; tests read once; model registered; product criterion on 50 hand-written tickets. Not passed: no urgent ticket in a wrong team on the model alone (1 of 167); right team first time 78 % against 90 %. Next, in order: rerun on the 100 hand-written tickets after the fixes; test the switch at "drafting off"; cloud deployment with teardown; a pilot that alternates weeks with and without the copilot and reads handling time, quality score and repeat contacts.
- Speaker: "The method was the same at every step: write the bar, measure on data we did not tune on, then spend. It made us keep a 3-billion-parameter model on a CPU, cancel two experiments, and say which gates are not passed. The pilot decision belongs to the head of support and compliance, with a stop rule already written: if repeat contacts rise two weeks in a row for a language or a team, drafting drops to context only for that segment."
- Sources: gates `sub/docs/roadmap.md`; verdicts `sub/docs/scoring_protocol.md` section 8 and `evals/report_v0.md` section 1; 214,308 `02_sizing.xlsx` `Decision!D19`; 13.32 % `Decision!D57`; 8.9 % routing estimate (15 % × 74 % × assumed 80 % cut) `05_metrics.md` sections 2 and 4; harm threshold `governance.md` Session 5; pilot design `05_metrics.md` section 3.
- Time: 40 s. Status: diagram to make.

### Divider: Demo (3 s)

### Demo video

- Content, 45 s, no sound needed: (1) Dashboard with tickets arriving and the animated flow; (2) Workspace: open one payment ticket, the merchant's earlier conversations, the draft with its cited sources; (3) edit one sentence, approve, choose "leave open" or "close", send; (4) one ticket that arrived in the Re-router with no draft and its reason; (5) back to the Dashboard, counts updated.
- Speaker: one line per step, no new claim.
- Status: video to record on the container demo (`sub/flow/deploy/demo.ps1 -Inject 6`), or on the cloud URL if it exists by then.

## 3. What we deliberately do not show, and why

| Left out of the main deck | Why |
|---|---|
| The 16-node table, trust levels L1 to L5, reason codes | Correct, but a newcomer needs eight boxes and three colours. Kept in the appendix. |
| Error severity score, macro-F1, exact match per field | One metric carries the model story. More scores would look like number-dropping. |
| The trap test set (380 tickets, 23 families) | It is a diagnosis, never an overall score (`sub/docs/scoring_protocol.md` section 1). Appendix. |
| The token-probability confidence study | A valid negative result on validation only; the test splits were not analysed (`sub/ml/confidence/README.md`). One line in the Q&A, not a slide. |
| Three-scenario table, build / buy / orchestrate scoring, lean canvas, RICE | The single line "worth it above 13 % of time saved" does the job of the whole memo for this jury. Appendix. |
| Inter-grader agreement, kappa and the LLM judge agreement | The Judge node is not built; showing 95.8 % agreement would suggest it is. Appendix. |
| AI Act and GDPR positions | Stated in `governance.md` as working hypotheses to check with Legal; nothing verified to present. One Q&A answer. |
| The world database build (60 merchants, history threads) | Needed for a credible demo, but it is plumbing for this audience; it appears inside the demo video. |
| The fictional press release and customer quotes of `01_problem_statement.md` | Written as an exercise; shown as fact they would mislead. |
| MLflow tracking and lineage | Local only and partly unfinished (`sub/docs/llmops_recovery_tasks.md`); Langfuse is the required monitoring. Appendix. |
| The override switch as a slide | Designed with an owner and a test, not in the code (issue #60). It is one honest sentence on slide 11 and a next gate on slide 14. |

## 4. Appendix slides and questions to prepare

Appendix (hidden), one visual each:

- A1. Full target flow `sub/docs/design/flow-v2/flow_v2.svg` with the node table "built / partial / to build" updated to the code.
- A2. Human checkpoints: who, which actions, service level (assumptions), and the four positions of the switch (`04_architecture.md` sections 5-6), marked "designed".
- A3. Sizing: three scenarios, do-nothing and rules-only (`02_investment_memo.md` table; `02_sizing.xlsx` `Decision`), and the cost lines.
- A4. Training settings table, read from `fine_tuning_component.py`; sequence-length histogram if available.
- A5. All systems, all measures on the test set (`sub/.local/figures/05_scorecard.png`) and the full table of `scoring_protocol.md` section 8.
- A6. Trap families (`sub/.local/figures/05_traps.png`) and urgent failure modes (`05_urgent_failure_modes.png`).
- A7. Latency and memory of the CPU variants (`04_latency_mean_p95.png`, `04_file_size_and_ram.png`).
- A8. Dataset review chain and where rejections come from (`01_chain_pass_rate.png`).
- A9. Hand-written evaluation: the three misses and their spec lines (`evals/report_v0.md` section 2, `spec.md` section 10); graders and judge agreement (`05_metrics.md` section 5).
- A10. Confidence study: probabilities do not separate right from wrong on team or urgency (AUC 0.60 to 0.64, validation only; `sub/ml/confidence/README.md`).
- A11. Demo and production boundaries: what data may go where (`spec.md` section 7).
- A12. Metric hierarchy for the pilot: primary, guardrails, counter-metrics, harm threshold (`05_metrics.md` section 3).

Questions to prepare, with the honest short answer:

1. "Is the endpoint live now?" See Gaps; answer with what is standing on the day and why an endpoint was deleted.
2. "Why fine-tune instead of prompting a bigger model?" Same 3B model prompted: 10.5 against 0.7, 60 % valid JSON. A bigger hosted model was excluded by the data rule (tickets stay in the company's cloud) and priced for reference in `02_sizing.xlsx` `Read options`.
3. "Did you tune hyperparameters?" No sweep was run: the sweep pipeline compiles, the single run passed the validation gate, and seven chained trainings were not justified. Say it plainly.
4. "Your labels are made by models. Why believe the scores?" Comparisons are paired on the same tickets; the tests have another writer; the 100 hand-written tickets exist for this reason and gave lower numbers (88 % valid outputs).
5. "One urgent ticket in 167 is misrouted. Is that acceptable?" Not against our own bar. Urgency never changes the path; the planned controls are the Re-router, a weekly sample and a queue-age alert, none measured yet.
6. "Is the 20 % time saving real?" No. It is an assumption. Only the routing share has a partial estimate; drafting quality was 2 sendable drafts of 30 on the first version.
7. "What does the policy check miss?" Paraphrases. It is a pattern rule set; the reviewer is the check on meaning (`sub/docs/design/flow-v2/policy-check.md`).
8. "Why LangGraph if it is not an agent?" For checkpoints: a ticket waits for a person and resumes from a saved checkpoint (SQLite). Recovery after an API restart is not yet accepted as tested (`sub/specs/roadmap.md`).
9. "What does a ticket cost to process?" Reading model on CPU about 20 euros a month in the scenario; one draft about 0.00001 dollar in one measured run (`node_table_v1.md` section 5), both to re-measure.
10. "Who are your users?" Classmates playing support roles; two usability testers (`03_user_research.md`). No real support agent was interviewed.
11. "What happens if Langfuse or the model is down?" Local prompt fallback; a ticket whose reading fails goes to the Re-router with a reason; nothing is lost.
12. "Does the benchmark describe the deployed model exactly?" Not exactly: the runtime adds constrained JSON output, so runtime results must be measured separately (`sub/docs/compact_variants.md` step 4).

## 5. Gaps between the course requirements and the repository today

| Requirement | State found | To do before the slides |
|---|---|---|
| LLM fine-tuned on Kubeflow, with metrics | Done: training pipeline (`sub/ml/qualifier/src/pipelines/model_training_pipeline.py`), run of 1 November, loss metrics logged, predictions scored locally with the protocol. The evaluation step is not a pipeline component (comment at the end of the pipeline file); the sweep never ran. | Capture the pipeline graph and the metrics panel in the Vertex console (free). Do not say "hyperparameter search". |
| Registry | Done for the model: Vertex Model Registry entry (`sub/docs/scoring_protocol.md`). No container image registry is used: images are built locally. The docs say they do not certify the current cloud state. | Open the console, confirm the entry still exists, capture it. |
| Endpoint deployed on GCP | **Nothing is standing.** A Vertex endpoint was created, served a model for about 30 minutes and was deleted on 2 November (`sub/audit_logs_equipe_navy.csv`); which model version it served is not written anywhere. The planned Cloud Run deployment is not done (issue #40); no deploy script exists beyond the local Compose file. | Decision for the project lead: push the two images to Artifact Registry and deploy to Cloud Run for the talk, with a written teardown, or redeploy a Vertex endpoint for a screenshot and delete it the same day. Without one of these, slide 12 can only show a past, deleted endpoint, which is weak against a mandatory item. Both options are billed: need an explicit go. |
| Interface to use the flow | Built locally: API (`sub/flow/api.py`), Dashboard and Workspace with approve, edit, hand over, send (`sub/frontend/src/`). Uncommitted front-end changes are in the working tree. Single user, no authentication. The READMEs still say the API and screens do not exist. | Commit or stash the front-end work, record the video on a clean run, update the two status paragraphs so the repository matches the slides. |
| Monitoring with Langfuse | Code is instrumented and prompts are versioned; no trace screenshot, no dashboard, and issues #41 and #20 (latency, cost, quality) are open. From the repository alone it cannot be confirmed that traces arrive. Cost and token usage are not attached to spans as far as the code shows. | Run six tickets with Langfuse keys set, check the trace, capture it. If cost and latency per step are not visible, say "traces and prompt versions", not "cost monitoring". |
| Guardrails | Field check, evidence gate, policy check, human-only list, approval and final check are in code and tested. Not built: Judge and redraft (issue #59), override switch (issue #60). Not measured: seeded violations caught, false blocks. | Keep the wording "designed, not built" for the switch. If time allows, the switch at "drafting off" is small and would turn a sentence into a proof. |
| Evidence after the fixes | The only full-chain measurement is the 13 November run on the old flow. The rerun on `evals/eval_set_v1.csv` (100 cases) is not done; the stage-2 gate is not met; "drafts on tickets that belong to a person" was 4 of 4 and is fixed in code but not re-measured. | One rerun on the 100 cases would give slide 10 a before / after. Calls go to an external API on synthetic data: small cost, needs a go. If not rerun, slide 11 must say "fixed in code, not yet re-measured". |
| Economics | The sizing is complete; all values are assumptions, and the workbook base volume is 36,900 a month while the scenario says 36,000. The 8.9 % routing estimate multiplies a measured 74 % by an assumed 80 % cut. | Say "estimated" for 8.9 %; use 36,000 on slide 1 and cite the workbook for euro values. |
| Product course files | `06_ab_protocol.md`, `07_operations.md`, `08_launch_memo.md` do not exist (issues #63 to #65). | The "next gates" of slide 14 rely on `05_metrics.md` and `governance.md` only; do not cite a protocol that is not written. |
| Figures | All ML charts exist under `sub/.local/figures/` (untracked, rebuilt by the notebooks). | Check font size at slide scale; rebuild from the notebooks if a label is too small. |

Two points of wording to settle as a team: the audit log file contains a personal e-mail and should stay out of the slides and out of Git; user research was done with classmates in role and must be presented as such.

## 6. Timing table

| Part | Slides | Time |
|---|---|---|
| Cover and index | 2 | 0:20 |
| Dividers (Context, Framing, Workflow, Model, Guardrails, Deployment, Monitoring, Conclusion, Demo) | 9 | 0:27 |
| Context | slide 1 | 0:40 |
| Framing | slides 2-3 | 1:05 |
| Workflow | slide 4 | 0:45 |
| Model | slides 5-9 | 2:35 |
| Guardrails | slides 10-11 | 1:10 |
| Deployment | slide 12 | 0:35 |
| Monitoring | slide 13 | 0:25 |
| Conclusion | slide 14 | 0:40 |
| Demo video | 1 | 0:45 |
| **Total** | 14 content slides | **9:27** |

Content slides alone: 40 + 35 + 30 + 45 + 25 + 30 + 40 + 30 + 30 + 30 + 40 + 35 + 25 + 40 = 475 s (7:55). If the talk runs long, cut the speech of slide 6 to its first sentence and shorten the demo to 30 s; do not cut slides 3, 10 or 14, which carry the reasoning.
