# Final presentation: storyline, slide content and plan

Status: **draft v1, to be validated by the team** (2026-11-16). Nothing is produced (charts, screenshots, slides) before this document is validated.

## 0. Frame

**What the course requires (must be visible on screen):**

| Requirement | Where it is proven | State today |
|---|---|---|
| LLM fine-tuned on Kubeflow, with metrics | slides 9 and 10 | done (Qwen2.5-3B + LoRA, KFP pipeline on Vertex, scored) |
| Endpoint deployed on GCP, with a registry | slide 12 | model registered (`keelpay-router-json`, alias `qwen3b-lora-q4`); **no endpoint standing**, container demo runs locally only |
| Interface to use the flow | slide 16 (demo) | done locally (mailbox, dashboard, review) |
| Monitoring with Langfuse | slide 13 | traces and versioned prompts in code; **no dashboard populated from a deployed run** |

**What raises the grade:** a detailed explanation of the fine-tuning R&D (how, not only scores) and of the guardrails.

**Format:** 15 min = about 9 min of talk and demo, then 5-7 min of Q&A. Slides carry charts and screenshots; text is one or two short sentences per slide.

**Writing rules for every slide**
- One idea per slide, stated as one plain sentence. No title / subtitle / sub-subtitle stacks.
- One visual that explains itself (chart, screenshot, schema). If the visual needs a legend paragraph, redraw it.
- No KPI tiles and no number-dropping. A number appears only inside a sentence or a chart that gives it meaning ("B2 routes 92 % of tickets right and still gets 1 in 3 wrong without telling anyone").
- A progress bar on every slide (6 sections), the current section highlighted.
- Divider slides (section title only, airy, contrasting) introduce each section and are passed in 2-3 seconds.

## 1. The thesis (the thread of the whole talk)

> In payment support, a visible mistake costs a person one minute. A silent mistake reaches the merchant. We did not chase the best accuracy; we built a system that prefers to say "I don't know" rather than be wrong without saying so.

Every section refers back to it:
- **Problem:** why silent errors are the cost that matters.
- **Workflow:** two models, everything else rules or people.
- **Model:** the output contract lets the model say `UNDEFINED`; the fine-tuning is judged on silent errors, and the accuracy-only view would have chosen the wrong system.
- **Guardrails:** the model is overconfident (confidence study), so the safety comes from rules and people, not from a probability threshold.
- **Deploy / monitor:** the run is traced so that a silent error can be found after the fact.
- **Next:** each gate toward production is a silent-error and value check.

**Key evidence for the thesis (test_natural, 610 tickets, read once):** the TF-IDF baseline B2 meets the 90 % desk-accuracy bar (91.6 %) and still makes **33.9 silent errors per 100 tickets** (mostly wrong payment references with the right desk). The fine-tuned D-q4 makes **0.7**. Accuracy does not separate them; silent errors do. Source: `docs/scoring_protocol.md` section 8.

## 2. Slide by slide

Budget: about 9 min 30 of talk + 1 min of demo. Times are targets for the rehearsal.

Legend for "material": **exists** (file in the repo), **to make** (chart from existing data), **to capture** (screenshot or video, needs a running system).

### Slide 1 · Cover (5 s)
Project name, one-line description, course, date. No team list here (it is on slide 2).

### Slide 2 · Index and team (15 s)
- The six sections as the progress bar itself (Context, Workflow, Model, Deployment, Monitoring, Next), so the audience learns the bar here.
- Team names under it.

---
*Divider 1 · Context*

### Slide 3 · The problem (40 s)
- **Sentence:** "Keelpay's support agents read 36,000 merchant emails a month, in French and English; one in seven first lands in the wrong desk."
- **Visual:** screenshot of a real-looking merchant email in our mailbox (French, payment delay, ID buried in the text). The audience reads the ticket the way an agent does.
- **Say:** reading and routing take 15 % of handling time, lookup and drafting 45 %. Scenario figures (fictional fintech), say so once.
- **Material:** screenshot to capture (Mailbox view). Figures: `00_pitch.md`.

### Slide 4 · What we optimise: silent errors (50 s)
- **Sentence:** "A ticket can end three ways. Only one of them is dangerous."
- **Visual:** three outcomes side by side, same ticket: **right** (green) / **handed to a person** (grey, costs a minute) / **silent error**: routed with a wrong desk or a wrong payment reference, nobody is warned (red, reaches the merchant). Under it, the severity scale as a simple bar (1 point, 3, 5, 10).
- **Say:** this is the rationale of the whole project. A system that hands everything to a person has no silent error and no use, so we always read silent errors together with the share handed to a person.
- **Material:** to make (schema). Source: `docs/scoring_protocol.md` sections 2-3.

### Slide 5 · Our answer and the go/no-go gates (45 s)
- **Sentence:** "A copilot that prepares each ticket and never sends alone. We gave ourselves gates before spending."
- **Visual:** horizontal timeline of the gates already passed, each a short label and a tick: problem sized and investment memo (GO to build the demo, pilot conditional) · dataset frozen · baselines scored · smoke run · full run · compression · test sets read once · model registered. The next gates (pilot) shown greyed, announcing slide 15.
- **Say:** this comes from the AI Product course (sizing, memo, governance); here it is one slide.
- **Material:** to make. Sources: `02_investment_memo.md`, `docs/roadmap.md` G1-G9, `governance.md`.

---
*Divider 2 · Workflow*

### Slide 6 · The workflow (60 s)
- **Sentence:** "Two language models. Everything else is rules or people."
- **Visual:** simplified flow, left to right, colour by kind: **model** (Qualifier, Drafter), **rule** (field check, routing, context plan, evidence gate, policy check, final gate), **person** (Re-router, Validator, Send). Merchant email in, reply out. A dashed loop for the merchant's next turn.
- **Say:** a workflow, not an agent: no model chooses a tool or the next step; cost per ticket is bounded (2 to 7 model calls); no tool can send, write to the ledger or refund.
- **Material:** to make from `docs/design/flow-v2/flow_v2.svg` (too detailed for a slide: redraw with about 8 boxes). Source: `04_architecture.md` sections 1-3.

---
*Divider 3 · The model*

### Slide 7 · The Qualifier: what goes in, what comes out (40 s)
- **Sentence:** "It reads one email and returns a strict JSON. When it cannot tell, it says so."
- **Visual:** left, the French SEPA email; right, the 7-field JSON (`intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`). Below, a second, smaller pair where the ID is ambiguous and the JSON says `"UNDEFINED"`: this is the contract that makes "I don't know" possible.
- **Say:** closed value lists (4 intents x 4 sub-intents, `OTHER`, `UNDEFINED`); the code checks the output against the contract; an invalid output goes to a person, never to a desk.
- **Material:** exists (`initial_brief.md` examples, `ml/qualifier/src/dataset_build/schema.py`); the `UNDEFINED` example to pick from `data/dataset/test_traps.csv`.

### Slide 8 · The training data (45 s)
- **Sentence:** "No real tickets: we generated 3,200 labelled emails for about 3 dollars, and we checked them before trusting them."
- **Visual:** a funnel/chain: scenario card (fixes the label) → writer model (writes only the text) → two blind readers → judge if they disagree → accepted or quarantined (never repaired). Next to it, the four splits as proportional bars: train 1,922 · val 293 · test_natural 610 · test_traps 380 (23 trap families: lowercase IDs, two amounts, polite but urgent, prompt injection...).
- **Say:** labels are known by construction, so no label noise; the test sets are written by a different model than the training set, so the model is not scored on its own writer's style.
- **Material:** to make. Source: notebook `01_dataset_build.ipynb`, `docs/methodology.md` section 2.

### Slide 9 · How we fine-tuned (75 s)
- **Sentence:** "Qwen2.5-3B with LoRA, in a Kubeflow pipeline on Vertex AI: two cheap tests decided the settings before the expensive run."
- **Visual, left:** screenshot of the training pipeline DAG in the Vertex console (data → fine-tuning → inference → evaluation). **Right:** the training and validation loss curve over 1,296 steps (3 epochs), validation minimum at step 1,250, no overfitting.
- **Recipe, as 4 short lines under the chart:** LoRA rank 8, alpha 16, dropout 0.05, learning rate 3e-4, 3 epochs on a 4-bit base · sequences of 1,024 tokens: 41 % of our chats exceeded the default 512 and the JSON answer would have been cut · loss on the answer only · float16: same losses, 3.1x faster on the T4 (measured on a 40-step smoke run).
- **Say:** the order of work: measure locally (token lengths), smoke run (200 tickets, 40 steps), one full run (2 h 06 on a T4), read the loss curve, then score. The best checkpoint is kept automatically. The hyperparameter sweep pipeline is written but was not run: the first run already left only a handful of errors, and the remaining ones are data cases (malformed IDs), not settings.
- **Material:** loss curve to make from `docs/results/d_qwen2.5-3b_full_run_log_history.json`; DAG screenshot to capture in the Vertex console (finished pipeline runs are kept, no cost). Sources: notebook `03_finetuning_vertex.ipynb`, `ml/qualifier/src/pipeline_components/fine_tuning_component.py`.

### Slide 10 · How we chose (75 s), the key slide of the R&D
- **Sentence:** "Accuracy would have chosen the wrong system. Silent errors and cost chose for us."
- **Visual A (left), the thesis chart:** for each system (B1 rules, B2 TF-IDF, B3 same Qwen without fine-tuning, D, D-q4), two bars on test_natural: desk accuracy and silent errors per 100. B2: 92 % / 34. B3: 53 % / 10.5, and 40 % of its answers break the JSON. D-q4: 97.5 % / 0.7.
- **Visual B (right), the trade-off:** silent errors per 100 (y) against monthly infrastructure cost for 36,000 tickets (x, log scale), one point per system: B2 near zero cost but 34 errors; D on a T4 endpoint about 255 €/month; D-q4 on CPU about 20 €/month with the fewest errors. The chosen point is circled.
- **Say:** after fine-tuning, we merged the adapter and quantised the model to 4 bits (GGUF): 1.9 GB, runs on a CPU at about 6 s per ticket, which is invisible in an email workflow. Compression lost nothing measurable on realistic tickets and a little on the trap tickets. The selection rule was written before scoring: keep the fine-tuned model only if its silent errors and severity are lower than the best baseline with a 95 % interval excluding zero. They are.
- **Material:** both charts to make from `docs/results/*_predictions.csv` and the tables of `docs/scoring_protocol.md` section 8; costs are assumptions, labelled as such on the chart. Shared theme: `ml/qualifier/notebooks/_viz.py`.

### Slide 11 · Guardrails (60 s)
- **Sentence:** "The model is confident even when it is wrong, so we do not rely on its confidence."
- **Visual:** left, a small chart from the confidence study: token probability of right vs wrong answers, both around 0.999 (AUC 0.60 on intent). Right, the guardrails as layers a ticket passes through, each with one example of what it stops:
  1. **Output contract:** malformed ID → `UNDEFINED` → a person.
  2. **Field check:** an amount the email does not contain is flagged.
  3. **Read-only tools scoped to the merchant of the envelope**, never to an ID read from the text (prompt-injection trap).
  4. **Evidence gate:** no evidence, no factual claim; the draft becomes a clarification question.
  5. **Policy check and final gate:** no figure that is not in the evidence, no promise, no other merchant's data.
  6. **Human-only topics** (legal threat, refund, fraud, data request): no draft at all.
  7. **A person approves every send**, and a switch turns the copilot down by levels.
- **Say:** one urgent ticket in 167 still lands in a wrong desk on the model alone; this is why people stay in the loop. A negative result (probabilities are useless here) changed the design.
- **Material:** chart to make from `.local/runs/confidence/val.jsonl` (check it is present locally; otherwise from the numbers in `ml/confidence/README.md`). Each guardrail must be checked as **built** in code before the slide claims it (`flow/policy.py`, `field_check.py`, `evidence.py`, `human_actions.py`); anything not built is shown as "planned" or dropped.

---
*Divider 4 · Deployment*

### Slide 12 · From registry to a running endpoint (60 s)
- **Sentence:** "The model goes from the registry to a container, and the container to a public endpoint on GCP."
- **Visual:** a short chain with a screenshot under each step: Vertex AI Model Registry (`keelpay-router-json`, alias `qwen3b-lora-q4`) → container image in Artifact Registry → running service (Cloud Run console, URL) → the app in the browser.
- **Say:** why CPU: the 4-bit model fits in 2.4 GB of RAM; a GPU endpoint bills 24/7 even idle, about 255 €/month, against about 20 for CPU. Secrets stay out of images. Demo data are synthetic only; in production the models run in Keelpay's own cloud.
- **Material:** to capture **after the deployment is done** (workstream C). Decision to confirm with the lecturer: is a Cloud Run service accepted as "endpoint", or is a Vertex AI endpoint expected (see section 4, decision D1).

---
*Divider 5 · Monitoring*

### Slide 13 · What Langfuse shows us (45 s)
- **Sentence:** "Every ticket leaves a trace: what each model received, answered, how long it took and what it cost."
- **Visual:** one Langfuse trace of one ticket (Qualifier span, Drafter span, latency, tokens, prompt version) and next to it the dashboard over the injected run (latency and cost per ticket over time).
- **Say:** prompts are versioned in Langfuse with a `production` label, with a local fallback if Langfuse is down. In production, silent errors have no label: the signals we would watch are Re-router corrections, drafts edited by agents, policy blocks, and a weekly QA sample of 5 % of routed tickets.
- **Material:** to capture after injecting synthetic tickets into the deployed app (`flow/inject_dataset.py`).

---
*Divider 6 · Next*

### Slide 14 · Method and economics (45 s)
- **Sentence:** "Cheap tests before expensive ones, a rule written before the results, and a project that pays off from about 6 % of agent time saved."
- **Visual, left:** the method as a single line of steps (contract → protocol → data with gates → baselines → smoke → full run → choose on val → test once → compress → register → deploy → trace). **Right:** one bar chart, active time saved: break-even 5.9 %, beat the next-best option 13.3 %, our base assumption 20 %, with "assumption, not measured" written on the bar.
- **Say:** total compute spent on the model is about 2 h of T4 and 1 h 30 of CPU; the dataset cost about 3 dollars. The value case is an assumption until the pilot measures time saved.
- **Material:** to make. Sources: `02_investment_memo.md`, `02_sizing.xlsx`, `docs/compact_variants.md`.

### Slide 15 · The gates to production (45 s)
- **Sentence:** "We stop at a deployed MVP. Each next step opens only if its check passes."
- **Visual:** a staircase, one check per step:
  1. **Shadow mode** in Keelpay's cloud on real tickets, nothing shown to agents: silent errors and urgent misses measured on a labelled sample.
  2. **Pilot on one desk**, drafts shown, a person sends: time per ticket at constant QA score.
  3. **Extension by desk**, with the switch tested before each step.
  4. **Routine:** weekly QA sample, rollback rule (one serious error sent → switch down).
- **Say:** each step has a stop criterion; "no-go" is a valid result.
- **Material:** to make. Sources: `governance.md`, `spec.md`, issues #63-#65 (A/B protocol, operations, launch memo).

### Slide 16 · Demo (60-75 s, video)
- Pre-recorded video, no live demo. Path: a ticket arrives in the mailbox → the dashboard shows the flow step by step → the Qualifier's JSON → the draft with its sources → the agent edits and approves → the policy check passes → simulated send → the trace appears in Langfuse.
- **Material:** to capture on the deployed app (workstream E). Keep the recording silent, we comment live.

### Hidden appendix (for Q&A, never shown unless asked)
- A1 · Per-trap heatmap: B2 vs B3 vs D-q4 on the 23 trap families (`test_traps`).
- A2 · Full results table, all systems, all measures, with bootstrap intervals.
- A3 · Dataset quality chain in numbers (pass rates 61 → 70 → 75 %, cost per ticket, quarantine).
- A4 · Hyperparameters and why the sweep was not run.
- A5 · Confidence study details (AUC per field, why `transaction_id` is the only usable signal).
- A6 · Cost details and assumptions (CPU price, ticket volume, T4 endpoint).
- A7 · Limits: synthetic tickets are cleaner than real ones (absolute scores optimistic, comparisons hold), labels checked by models not humans, severity points are assumptions.

**Questions to prepare:** why not a large model through an API (data residency, cost, format reliability: B3 shows it) · why Qwen 3B and LoRA · why synthetic data and how we avoid scoring the writer's style · is D-q4 really better than D (difference of a few tickets, not significant; chosen on cost) · how to detect silent errors in production without labels · what happens when Langfuse or the Qualifier is down · why a workflow and not an agent.

## 3. Gaps to close before the slides

| Gap | Blocks | Workstream |
|---|---|---|
| No endpoint standing on GCP | slides 12, 13, 16 | C |
| Langfuse has no traces from a deployed run | slide 13 | D |
| Guardrail list not verified against the code | slide 11 | B |
| Confidence data on the test sets not fetched (val only) | slide 11, A5 (val is enough for the slide) | B, optional |
| No chart in the presentation theme | slides 4-6, 8-11, 14-15 | B |
| Demo not recorded | slide 16 | E |

## 4. Decisions needed from the team

- **D1 · Endpoint type.** Recommendation: Cloud Run (CPU, scales to zero, URL reachable by the jury) with the model pulled from the Vertex Model Registry, because it is the target of `docs/roadmap.md` G8 and costs little. Risk: the lecturer may expect a Vertex AI endpoint by name. Ask the lecturer this week; if needed, deploy a Vertex AI CPU endpoint for one hour, screenshot it, delete it the same day.
- **D2 · Slide tool.** Google Slides (shared editing for 4 people) vs a generated deck. Recommendation: Google Slides with one master (progress bar, divider layout), charts exported as SVG/PNG from code so they can be regenerated.
- **D3 · Language of the slides** (French or English).
- **D4 · Who presents which section,** and the presentation date (drives the roadmap dates).
- **D5 · Relation to the AI Product final oral** (issue #66): same deck or a separate one. Recommendation: separate decks, shared charts.

## 5. Roadmap

Workstreams can run in parallel once A is validated; C → D → E is the only chain.

| Step | Workstream | Output | Depends on | Done when |
|---|---|---|---|---|
| 1 | A · Storyline | this document validated, decisions D1-D5 taken | none | team agrees in writing on the issue |
| 2 | B · Charts | one script producing every chart in one theme (SVG + PNG), guardrails verified in code | 1 | charts of slides 4, 6, 8, 9, 10, 11, 14, 15 regenerate from one command |
| 2 | C · Deployment | images in Artifact Registry, service running on GCP, teardown command written | 1 (D1) | URL opens the app from another machine; cost and stop procedure written |
| 3 | D · Monitoring | synthetic tickets injected on the deployed app, Langfuse dashboard populated | C | trace and dashboard screenshots exist |
| 3 | E · Screenshots and demo | Vertex DAG, registry, Cloud Run, mailbox, Langfuse screenshots; demo video | C, D | all "to capture" material in one folder |
| 4 | F · Deck | slides 1-16 + appendix in the master | 2-3 | deck complete, no placeholder |
| 5 | G · Rehearsal and Q&A | two timed rehearsals, answers to the prepared questions | 4 | under 10 min twice in a row |
| after | Teardown | GCP service deleted after the oral | oral | console checked empty |

## 6. GitHub issues to create (after validation)

Reuse the existing issues where they already cover the work, create the rest, and link all of them from one tracker.

| Issue | Action |
|---|---|
| Tracker · Final LLMOps presentation | new, links everything below and this document |
| Storyline and decisions D1-D5 | new (workstream A) |
| Charts in the presentation theme + guardrail check against code | new (B) |
| Deploy the demo on GCP | reuse #40 (and #39 for the container), add the D1 decision and the teardown check |
| Langfuse traces from the deployed run | reuse #41, add "dashboard screenshots" as done criterion |
| Screenshots and demo video | new (E) |
| Slide deck | new (F) |
| Rehearsal and Q&A prep | new (G) |
