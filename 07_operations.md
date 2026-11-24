# 07 · Operations — NAVY · Keelpay support copilot

> Session 7 deliverable, pitch beat 9. What can go wrong once the copilot runs, how we see it, when we change the model, and how we switch it off. Written on 23 November 2026 for the Keelpay pilot (CONDITIONAL GO, `02_investment_memo.md`); the course demo runs on synthetic data and has no live monitoring. Thresholds come from [`evals/07_monitoring.ipynb`](evals/07_monitoring.ipynb), `06_ab_protocol.md` and `05_metrics.md`; they are starting values from synthetic data, re-set on the first four pilot weeks. Built today vs required is said on every line.

## 1 · Adverse effects

What the copilot can do wrong, who it hurts, and what catches it. Ordered by harm, not by frequency.

| # | Adverse effect | Who is hurt | How we see it | Barrier in the flow |
|---|---|---|---|---|
| 1 | **Urgent ticket sent to the wrong desk** (1 of 167 on test_natural, `scoring_protocol.md` §8): a dispute misses its chargeback deadline | merchant (money), Keelpay (penalty) | Re-router correction of an urgent ticket; queue-age alert on urgent tickets (#41) | urgency shown on every ticket; floor 0, one case = incident (§4) |
| 2 | **Wrong payment fact in a sent reply** (amount, status, date of another transaction) | merchant, then Keelpay | QA sample, seeded wrong drafts, merchant's reply | Evidence gate (node 8): factual only with exact, merchant-scoped ledger facts; Policy check blocks figures absent from the evidence (`flow/policy.py`) |
| 3 | **Data of another merchant in a draft** | the other merchant (privacy) | final gate block count; audit log | hard block on foreign `M-####` identifiers, cannot be overridden (`policy-check.md`); ledger scoped by `merchant_id` from the envelope |
| 4 | **Automation bias**: agents approve drafts unread to go faster | merchants, then quality | counter-metric "drafts on the wrong payment validated unread" (`05_metrics.md` §3); seeded wrong drafts | unchanged draft needs an explicit confirmation (`governance.md` Session 4) |
| 5 | **Promise or legal statement** (refund, fee quote, legal advice) | Keelpay (liability) | Policy check block rate; QA sample | Policy check on the draft (node 10) and on the final text (node 14) |
| 6 | **Unequal quality by language or desk**: English or Belgian formal letters get fewer drafts or more errors | merchants of that segment | selection-rate parity and error rates by segment (`05_metrics.md` §3; offline baseline in `evals/05_segment_fairness.ipynb` §2: `72.5 %` FR vs `66.1 %` EN draft-eligible on `eval_set_v1.csv`, all 4 silent errors of `test_natural` in FR, `0 %` silent errors on `payments` vs `16.0 %` on `disputes`) | harm threshold of `governance.md` Session 5: drafting off on that segment |
| 7 | **Silent drift**: new product, new fraud wording, new language; the Qualifier keeps answering, wrongly | everyone, slowly | PSI and invalid / `UNDEFINED` shares (§2, layer 1); audit sample (layer 2) | invalid or `UNDEFINED` intent goes to the Re-router with no draft |
| 8 | **Re-router overload**: abstentions grow, people wait | merchants (delay), agents | Re-router queue age, `UNDEFINED` share | FIFO and waiting time visible (`spec.md` §6) |
| 9 | **Deskilling**: new agents never learn to route or write | Keelpay, long term | A/B arm × period and seniority segment (`06_ab_protocol.md` §5); manual-week QA | copilot-off still usable (§4, L3); periodic manual weeks for new agents |
| 10 | **Hidden cost**: Drafter tokens, retries, endpoint left on | Keelpay | cost per ticket in traces; billing alert | `transient_retries = 3`, endpoint teardown rule (sub-project README) |

The copilot never sends, refunds, unfreezes or writes to the ledger: those harms are excluded by design, not monitored.

## 2 · Monitoring layers

Four layers, from seconds to months. Each has one reader and one action. Layers 0–1 need no labels; layer 2 needs people; layer 3 is the business.

| Layer | Clock | Signal (numerator / denominator) | Watch → Act | Reader | Built today |
|---|---|---|---|---|---|
| **0 · Service** | live | Qualifier p95 latency (11.8 s measured on CPU); timeouts / calls; Drafter errors / calls; cost per ticket | p95 > 18 s for an hour → timeouts > 5 % of an hour: new tickets at L1 | NAVY on call | node latency and Drafter cost in `flow/metrics_store.py` and Langfuse traces; no alerting yet (#41, #20) |
| **1 · Drift, no labels** | daily | PSI of predicted intent, urgency, ticket language against the validation reference; invalid outputs / outputs; predicted `UNDEFINED` / outputs | PSI 0.10–0.25 → PSI > 0.25 two days running; invalid > 3.4 % → > 5 %; `UNDEFINED` > 11.6 % → > 15 % | NAVY + Head of Support | computed in the notebook on stored predictions; not scheduled |
| **2 · Quality, labels** | weekly | silent errors in 200 audited auto-routed tickets, rolling 4 weeks (alarm at ≥ 13 of 800, under 1 % false alarms, catches a tripling 86 % of the time); every urgent Re-router correction; QA score of 35 sent replies a week (`06_ab_protocol.md` §3); Policy-check blocks; seeded errors caught / seeded | 10–12 of 800 → ≥ 13; urgent correction: 1 = incident | Head of Support; Head of Compliance for serious errors | the scorer (`ml/qualifier/src/scoring.py`) and the eval-set replay exist; the weekly sample is a process to set up |
| **3 · Business** | monthly | hands-on minutes per ticket, repeat contact within 7 days, hand-overs, uncaught serious errors per category (`05_metrics.md` §4) | serious errors above `Flow!C19:C21` → stop | Head of Support, finance | after the A/B (`06_ab_protocol.md`) |

**Why the layer-1 bands hold on our data** (notebook §1): on `test_natural`, written by another model than the training data, every PSI stays under 0.02, so the bands do not fire on a normal week. On `test_traps`, a stress set, the predicted intent reaches 0.39 and urgency 0.21, and invalid outputs reach 4.7 % (1.4 % on val). The bands separate a normal week from a shifted one.

**Why a 4-week window for layer 2** (notebook §2): at a reference rate of 0.7 silent errors per 100, one week of 200 labels catches a tripling only one time in four. The rolling window trades speed for power. Fast, severe failures are not left to the sample: urgent corrections, gate blocks and complaints are counted one by one, every day.

**What never enters monitoring:** ticket text, draft text, merchant or ticket IDs as metric labels (`measures-and-gates.md`). Traces carry node names, versions, durations, outcomes.

## 3 · Drift triggers and retraining

A trigger starts a **re-evaluation**, not a retraining. Retraining is the last of four answers, after checking the rules, the prompt and the data.

| Trigger | First check | Possible answers, in order |
|---|---|---|
| Layer 1 PSI > 0.25 two days running, or invalid > 5 %, or `UNDEFINED` > 15 % | label 200 tickets of the drifting days, score them with `score_predictions.py` | 1 nothing (benign mix change, note it) · 2 Routing rule or config (`flow/config.toml`) · 3 prompt version (Langfuse) · 4 retraining |
| Layer 2 alarm (≥ 13 silent errors of 800) | replay the eval-set v1 and the frozen test sets on the live model version | same order |
| One urgent ticket in a wrong desk | that ticket's trace and the Routing Node rule | rule or keyword list first (`human_only_keywords`); retraining only if the field is wrong across several cases |
| New taxonomy value (new product, new desk) | contract change: versioned migration (`spec.md` §3) | retraining is required: the seven-field contract is the model's output |
| Scheduled | every quarter, and at each model, prompt, rule or threshold change (`Inputs!D55`, 3 a year) | eval-set + judge replay, `05_metrics.md` §5 |

**Retraining procedure** (the course pipeline, already run once: 2 h 06 of T4, sub-project README):

1. New labelled tickets from the drift period, labelled blind by a person who does not tune the model (`evals/README.md`); human corrections in the Re-router are candidates, never trusted labels by themselves (`governance.md` Session 3).
2. Added to the training split only; validation and test sets stay frozen so that old and new models are compared on the same tickets.
3. `pipeline_runner.py training --smoke`, then the full run, then the GGUF q4 compaction.
4. **Promotion gate**: the candidate is promoted only if, on test_natural and test_traps, silent errors and urgent wrong-desk are **no worse** than the live version, and contract validity is not lower; and if it fixes the drifting sample. Registered in the Vertex AI Model Registry under a new version; the live alias moves only after the gate. Cost: one T4 run, about 2 h, billed to school credits; the endpoint teardown rule applies.

## 4 · Rollback plan and criterion

**Three things can be rolled back, separately:**

| What | How | Time | Built today |
|---|---|---|---|
| **Prompt** (Qualifier or Drafter) | move the Langfuse `production` label back to the previous immutable version (`prompt-management.md`) | minutes | yes |
| **Qualifier model** | point `qualifier_model_uri` / `qualifier_model_version` (and its MD5) in `flow/config.toml`, or the Registry alias, to the previous version; restart | under an hour | yes, by configuration; no one-click |
| **Copilot level** | `copilot_mode` switch (`flow/config.toml` or `NAVY_COPILOT_MODE`) with four fallback positions (`governance.md` Session 4, #60) | immediate on env/config reload | **yes (#60):** `flow/pipeline_steps.py`, verified by `uv run python -m flow.rollback_check` alongside `ledger_enabled` / `knowledge_enabled` |

**The four levels of `copilot_mode`** (`full` is nominal), from least to most:

| Level (`copilot_mode`) | What stays | What stops |
|---|---|---|
| `judge_off` | everything else | the optional Judge / Redraft (nodes 11–12) |
| **`l1_drafting_off` (L1 · drafting off)** | qualified fields, desk, context, human writing | every model draft (`DRAFTING_OFF`) |
| `l2_routing_off` (L2 · routing off) | qualified fields as hints | automatic desk (`ROUTING_OFF`): every ticket to manual routing |
| **`l3_copilot_off` (L3 · copilot off)** | the manual queue (FIFO, waiting time) | the whole copilot (`COPILOT_OFF`, `0` model or tool calls) |

**Rollback criteria — any one is enough, no vote needed:**

| Criterion | Rollback | Who decides |
|---|---|---|
| One uncaught serious error caused by the copilot reaches a merchant | L1 on the affected desk at once; review within 24 h | Head of Compliance |
| Serious errors above the pessimistic value of a category (`Flow!C19:C21`) | L3 | Head of Compliance |
| Second urgent ticket in a wrong desk within 4 weeks | L2 for urgent tickets | Head of Support |
| Layer 2 alarm confirmed by the eval-set replay | previous model or prompt version | Head of Support, NAVY executes |
| Harm threshold of `governance.md` Session 5 on a segment | L1 on that segment | Head of Support |
| Timeouts > 5 % of an hour, or the Qualifier endpoint down | L1 for new tickets until recovered; tickets already queued keep their state | NAVY on call |

**Procedure.** The decider triggers, NAVY executes and writes the line in `governance.md` (date, trigger, level, owner). Tickets in flight are never lost: a ticket already drafted keeps its draft for human review, new tickets follow the new level, receipt time and total age are preserved (`governance.md` Session 4). **Return** to the previous level only after the cause is named, the fix passes the eval-set replay, and the decider signs it off.

**Tested before every demo and every release** (`uv run python -m flow.rollback_check`, `tests/flow/test_copilot_mode_eval_replay.py`, #60): replayed on all 100 cases of `evals/eval_set_v1.csv` (24 November 2026) — `l1_drafting_off` produces **0 model drafts** (`79` routed with `69` tool runs, `21` to Re-router); `l2_routing_off` routes `100/100` to manual triage with **0 drafts**; `l3_copilot_off` makes **0 Qualifier, tool or Drafter calls**, preserves FIFO order on `100/100` tickets, and completes human reply/send end to end. A rollback that was never tested is not a rollback.

## 5 · What this plan does not cover

The rate of rare serious errors cannot be certified by these samples (`governance.md` Session 2). The demo has no 24/7 on-call, no hosted alerting and no durable hosted state (#74). Retention of traces and audit logs awaits the DPO decision (90 days is a proposal). These are requirements for the pilot, not claims about the demo.
