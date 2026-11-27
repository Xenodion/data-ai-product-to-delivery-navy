# 07 · Operations — NAVY · Keelpay support copilot

> Session 7 deliverable, pitch beat 9. What can go wrong once the copilot runs, how we see it, when we change the model, how we switch it off, and who owns each decision. Written on 23 November 2026 for the Keelpay pilot (CONDITIONAL GO, `02_investment_memo.md`), completed on 27 November 2026. The course demo runs on synthetic data and has no live monitoring. Thresholds come from [`evals/07_monitoring.ipynb`](evals/07_monitoring.ipynb), `06_ab_protocol.md` and `05_metrics.md`; they are starting values from synthetic data, re-set on the first four pilot weeks. Each line says what is built today and what the pilot still requires.

## 1 · Adverse effects

What the copilot can do wrong, who it hurts, and what catches it. Ordered by harm, not by frequency.

| # | Adverse effect | Who is hurt | How we see it | Barrier in the flow |
|---|---|---|---|---|
| 1 | **Urgent ticket sent to the wrong desk** (1 of 167 on the synthetic test set): a dispute misses its chargeback deadline | merchant (money), Keelpay (penalty) | Re-router correction of an urgent ticket; alert on the age of urgent tickets in the queue (pilot) | urgency shown on every ticket; floor 0, one case = incident (§7) |
| 2 | **Wrong payment fact in a sent reply** (amount, status, date of another transaction) | merchant, then Keelpay | QA sample, seeded wrong drafts, merchant's reply | Evidence gate: a factual reply only with exact ledger facts of that merchant; the Policy check blocks any figure absent from the evidence |
| 3 | **Data of another merchant in a draft** | the other merchant (privacy) | final gate block count; audit log | hard block on another merchant's identifier, cannot be overridden; ledger reads limited to the merchant of the ticket |
| 4 | **Automation bias**: agents approve drafts unread to go faster | merchants, then quality | counter-metric "drafts on the wrong payment validated unread" (`05_metrics.md` §3); seeded wrong drafts | an unchanged draft needs an explicit confirmation (`governance.md` Session 4) |
| 5 | **Promise or legal statement** (refund, fee quote, legal advice) | Keelpay (liability) | Policy check block rate; QA sample | Policy check on the draft and again on the final text |
| 6 | **Unequal quality by language or desk**: English or Belgian formal letters get fewer drafts or more errors | merchants of that segment | draft share and error rates by segment (`05_metrics.md` §3; offline baseline in `evals/05_segment_fairness.ipynb`: 72.5 % FR vs 66.1 % EN draft-eligible on the 100-case eval-set, all 4 silent errors of the synthetic test set in FR, 0 % silent errors on `payments` vs 16.0 % on `disputes`) | harm threshold of `governance.md` Session 5: drafting off on that segment |
| 7 | **Silent drift**: new product, new fraud wording, new language; the Qualifier keeps answering, wrongly | everyone, slowly | shift of the predicted mix and share of invalid or `UNDEFINED` outputs (§2, drift row); audit sample (quality row) | an invalid or `UNDEFINED` intent goes to the Re-router with no draft |
| 8 | **Re-router overload**: abstentions grow, people wait | merchants (delay), agents | Re-router queue age, `UNDEFINED` share | oldest-first queue with visible waiting time (`spec.md` §6) |
| 9 | **Deskilling**: new agents never learn to route or write | Keelpay, long term | A/B arm × period and seniority segment (`06_ab_protocol.md` §5); manual-week QA | copilot off still usable (§7, L3); periodic manual weeks for new agents |
| 10 | **Hidden cost**: Drafter tokens, retries, cloud endpoint left on | Keelpay | cost per ticket in the traces; billing alert | three retries at most; the cloud endpoint is emptied after each use |

The copilot never sends, refunds, unfreezes or writes to the ledger: those harms are excluded by design, not monitored.

## 2 · Monitoring: four layers, a threshold, a clock, an owner

From seconds to months. Each row has one owner and one action. The drift row needs no labels; the quality row needs people; the business row is read after the A/B.

| Layer | Metric (from `05_metrics.md`) | Watch → threshold that pages | Clock | Owner | Tool — startup | Tool — large company | Built today |
|---|---|---|---|---|---|---|---|
| **Infrastructure** | Qualifier p95 latency (11.8 s measured on CPU); timeouts / calls; Drafter errors / calls; cost per ticket | p95 > 18 s for an hour → timeouts > 5 % of an hour: new tickets at L1 | real time | NAVY on call | Cloud Run metrics · Sentry | Cloud Monitoring · Datadog | latency and cost per step recorded and in the traces; no alerting yet |
| **Model quality — drift, no labels** | shift (PSI) of predicted intent, urgency and ticket language against the validation set; invalid outputs; `UNDEFINED` share | PSI 0.10–0.25 → PSI > 0.25 two days running; invalid > 3.4 % → > 5 %; `UNDEFINED` > 11.6 % → > 15 % | daily | NAVY, read with the Head of Support | Langfuse | Langfuse self-hosted in Keelpay's cloud · Datadog LLM | computed in the notebook on stored predictions; not scheduled |
| **Model quality — labels** | silent errors in 200 audited auto-routed tickets a week, rolling 4 weeks; every urgent Re-router correction; QA score of 35 sent replies a week (`06_ab_protocol.md` §3); seeded errors caught | 10–12 of 800 → ≥ 13 of 800 (under 1 % false alarms, catches a tripling 86 % of the time); urgent correction: 1 = incident | weekly | Head of Support; Head of Compliance for serious errors | Langfuse annotation queue + sheet | Langfuse self-hosted + QA tool | scorer and eval-set replay exist; the weekly sample is a process to set up |
| **Product & guardrails** | Policy-check and final-gate blocks; Re-router correction rate; drafts validated unchanged; direct-send rate (who wrote each sent reply) | correction rate above 1 in 7 on a segment two weeks running (harm threshold) | daily | Head of Support | metrics table + Metabase / Looker Studio | warehouse + Looker / Power BI | recorded per ticket in the metrics store; report script, no dashboard tool yet |
| **Business** | hands-on minutes per ticket, repeat contact within 7 days, hand-overs, uncaught serious errors per category (`05_metrics.md` §4) | serious errors above the pessimistic value of a category (`02_sizing.xlsx` `Flow!C19:C21`) → stop | weekly, decided monthly | Head of Support, with finance | weekly query + sheet | BI dashboard | after the A/B (`06_ab_protocol.md`) |
| **Paging** | — | — | — | NAVY on call (night), Head of Support (day) | Slack webhook | PagerDuty / Opsgenie | not built |

**Why the drift bands hold on our data** (notebook §1): on the synthetic test set, written by another model than the training data, every PSI stays under 0.02, so the bands do not fire on a normal week. On the stress set of traps, the predicted intent reaches 0.39 and urgency 0.21, and invalid outputs reach 4.7 % (1.4 % on validation). The bands separate a normal week from a shifted one.

**Why a 4-week window for the labelled quality** (notebook §2): at a reference rate of 0.7 silent errors per 100, one week of 200 labels catches a tripling only one time in four. The rolling window trades speed for power. Fast, severe failures are not left to the sample: urgent corrections, gate blocks and complaints are counted one by one, every day.

**What never enters monitoring:** ticket text, draft text, merchant or ticket identifiers as metric labels. Traces carry step names, versions, durations and outcomes.

## 3 · Where it runs and how a change reaches production

**Where our FastAPI runs.** For the course demo: on our laptop, in one local container (API, front end and the CPU Qualifier), with synthetic tickets and simulated sends; the Qualifier can also be served from a Vertex AI endpoint that we empty after each demo, because it is billed by the hour. For the pilot: Cloud Run inside Keelpay's cloud, so that real tickets, models and traces stay with Keelpay (`governance.md` Session 3). Secrets live in `.env` files, never in Git.

**Release path and gates.**

| Step | What runs there | Gate to pass |
|---|---|---|
| **dev** — every commit | unit tests, and a regression check of the Qualifier on 100 eval-set cases, run automatically on GitHub | all tests green; no regression on silent errors or urgent wrong desk |
| **staging** — our laptop, at every change of prompt, model, rule or approved content | replay of the 100-case eval-set with two graders and the judge; rollback test at the three levels (§7); on the pilot, a first shadow week where drafts are produced but not shown | eval-set no worse than the live version; rollback verified; the change is dated in `governance.md` |
| **production by steps** | internal agents → the A/B (half the conversations, `06_ab_protocol.md`) → rollout one desk at a time, payments first, disputes last (15 % → 35 % → 55 % → 70 % of tickets by quarter, `02_sizing.xlsx` `Inputs!D39:D42`) | each step needs four quiet weeks on the labelled quality row and no open incident |

**First drift we expect:** data drift — a new product, a new fee or a new fraud wording that the Qualifier has never seen. Signal: the predicted mix shifts and the `UNDEFINED` share rises (drift row of §2). Close behind it, knowledge drift: a fee or policy page changes and drafts quote the old one; signal: Policy-check blocks and QA failures on that topic. What we re-run: the frozen 100-case eval-set (`evals/eval_set_v1.csv`) and the frozen synthetic test sets, at every model, prompt, rule or content change and every quarter.

## 4 · Drift triggers and retraining

A trigger starts a **re-evaluation**, not a retraining. Retraining is the last of four answers, after checking the rules, the prompt and the data.

| Trigger | First check | Possible answers, in order |
|---|---|---|
| Drift row: PSI > 0.25 two days running, or invalid > 5 %, or `UNDEFINED` > 15 % | label 200 tickets of the drifting days and score them | 1 nothing (benign mix change, note it) · 2 routing rule or configuration · 3 prompt version · 4 retraining |
| Labelled quality alarm (≥ 13 silent errors of 800) | replay the eval-set and the frozen test sets on the live model version | same order |
| One urgent ticket in a wrong desk | that ticket's trace and the routing rule that applied | rule or keyword list first; retraining only if the field is wrong across several cases |
| New category (new product, new desk) | change of the seven-field contract, versioned (`spec.md` §3) | retraining is required: the contract is the model's output |
| Scheduled | every quarter, and at each model, prompt, rule or threshold change (3 a year, `02_sizing.xlsx` `Inputs!D55`) | eval-set and judge replay, `05_metrics.md` §5 |

**Retraining in four steps** (the pipeline has been run once: about 2 hours on one cloud GPU):

1. New tickets from the drift period are labelled blind by a person who does not tune the model (`evals/README.md`). Corrections made in the Re-router are candidates, never trusted labels by themselves (`governance.md` Session 3).
2. They are added to the training set only; the validation and test sets stay frozen, so old and new models are compared on the same tickets.
3. Short trial run, then the full run, then compression of the model so that it runs on CPU.
4. **Promotion gate**: the new version is promoted only if, on both frozen test sets, silent errors and urgent wrong-desk cases are **no worse** than the live version, contract validity is not lower, and it fixes the drifting sample. Each version is kept in a model registry; the live version changes only after the gate.

## 5 · The trace and the dashboard

**One trace per ticket, one span per step**, following the OpenTelemetry model; today they are sent to Langfuse, with one session per ticket.

| Span | Attributes kept |
|---|---|
| `intake` | ticket id, received at, language, turn number, versions of model, prompts, rules and approved content |
| `qualify` | the seven fields, valid against the contract or not, fields left `UNDEFINED`, latency |
| `field_check` | fields repaired or rejected |
| `route` | desk or Re-router, rule applied, urgency |
| `context` | ledger facts and help pages used (ids), no-hit |
| `evidence_gate` | reply type allowed: factual, documentary or clarification |
| `draft` | Drafter model, prompt version, tokens, cost, latency |
| `policy_check` | pass, or the block and its reason |
| `human_decision` | Re-router correction; Validator approved unchanged, edited, rewritten or handed over; QA grade when sampled |
| `final_gate_and_send` | pass or block, who wrote the reply, send time |

Ticket text and draft text are masked in the traces; only step names, outcomes, versions, durations and costs leave the system. Stored in Langfuse for the demo; for the pilot, in Langfuse self-hosted in Keelpay's cloud, for 90 days (proposal awaiting the DPO, `governance.md`).

**The one-page dashboard: five panels, one question each.**

| Panel | Question it answers |
|---|---|
| Stat tiles with thresholds: urgent tickets in a wrong desk, uncaught serious errors, p95 latency, current copilot level | Am I paged? |
| Lines over time: hands-on minutes, Re-router correction rate, `UNDEFINED` share | Is it getting better or worse, and when did it change? |
| Predicted intent this week vs last week | Is the input drifting? |
| Bars by segment: draft share and errors by language and desk | Is one group of merchants served worse? |
| Worst cases of the week: blocked drafts, corrected urgent tickets, merchant complaints | What do we fix on Monday? |

Built today: the Overview page of the demo shows the live queues and the flow; the metrics report reads the metrics store. For the pilot: Metabase or Looker Studio on the metrics table.

## 6 · Incident classes

The harm threshold of `governance.md` Session 5 is the line between "sent wrong" and "harmful".

| Class | Example on our copilot | Action |
|---|---|---|
| **Caught** | the Policy check blocks a draft that quotes a fee absent from the evidence; an agent corrects a ticket's desk in the Re-router | counted; weekly review; a spec line or a new eval-set case if it repeats |
| **Sent wrong** | an approved reply links the wrong help page, or asks for a reference the merchant already gave; the merchant writes again | correct reply to the merchant; case added to the eval-set; weekly review by the Head of Support |
| **Harmful** (above the harm threshold) | a reply quotes the status or amount of another transaction; an urgent dispute waits in the wrong desk past its deadline; another merchant's data appears | rollback now (§7); incident report within 24 h; the DPO is told at once if data of another merchant is involved |
| **Outage** | the Qualifier endpoint is down or times out on more than 5 % of an hour | a ticket without a valid Qualifier output goes to the Re-router with no draft (built); new tickets at L1 until recovered; queued tickets keep their state and age |

## 7 · Rollback plan

**The plan in six fields.**

| Field | Ours |
|---|---|
| 1 · Trigger | any one criterion of the table below; no vote needed |
| 2 · Who decides | day: Head of Support, Head of Compliance for serious errors; night: NAVY on call, who informs the Head of Support the next morning |
| 3 · The action | one switch with four positions (below), or the previous version of a prompt or of the Qualifier |
| 4 · Time to execute | switch: immediate, on configuration reload; prompt: minutes; Qualifier version: under an hour |
| 5 · What people see | agents get tickets without a draft (L1), in manual triage (L2) or in the plain manual queue, oldest first with waiting time (L3); a ticket already drafted keeps its draft for review; merchants still get a reply written or checked by a person |
| 6 · Last tested | **24 November 2026**, on our laptop (our staging for the project), by Nahel Bachiri, on the 100 cases of `evals/eval_set_v1.csv`. Next test: before the oral demo of 27 November 2026, then before every release and before the first pilot week |

**Three things can be rolled back separately:** the prompt (Qualifier or Drafter: the previous version is restored in minutes), the Qualifier model (the previous registered version, under an hour), and the copilot level (the switch below, immediate).

**The four positions of the switch** (`full` is normal operation; the copilot is suggest-only in every position, since a person sends every reply):

| Position | What stays | What stops |
|---|---|---|
| Judge off | everything else | the optional Judge and Redraft (not built yet) |
| **L1 · drafting off** | fields, desk, context, human writing | every model draft |
| L2 · routing off | fields as hints | automatic desk: every ticket goes to manual triage |
| **L3 · copilot off** | the manual queue, oldest first, with waiting time | the whole copilot: no model or tool call |

**Rollback criteria — any one is enough:**

| Criterion | Rollback | Who decides |
|---|---|---|
| One uncaught serious error caused by the copilot reaches a merchant | L1 on the affected desk at once; review within 24 h | Head of Compliance |
| Serious errors above the pessimistic value of a category (`02_sizing.xlsx` `Flow!C19:C21`) | L3 | Head of Compliance |
| Second urgent ticket in a wrong desk within 4 weeks | L2 for urgent tickets | Head of Support |
| Labelled quality alarm confirmed by the eval-set replay | previous model or prompt version | Head of Support; NAVY executes |
| Harm threshold of `governance.md` Session 5 on a segment | L1 on that segment | Head of Support |
| Timeouts > 5 % of an hour, or the Qualifier endpoint down | L1 for new tickets until recovered | NAVY on call |

**Procedure.** The decider triggers, NAVY executes and writes the line in `governance.md` (date, trigger, position, owner). No ticket is lost: new tickets follow the new position, receipt time and total age are kept (`governance.md` Session 4). **Return** to the previous position only after the cause is named, the fix passes the eval-set replay, and the decider signs it off.

**What the test of 24 November showed**, on all 100 eval-set cases: drafting off produces **0 drafts** (79 tickets routed, 21 to the Re-router); routing off sends **100 of 100** to manual triage with 0 drafts; copilot off makes **0 model or tool calls**, keeps the oldest-first order on 100 of 100 tickets, and a person can still write and send the reply end to end. A rollback that was never tested is not a rollback.

## 8 · The five owners

| Decision | Owner (role) | Written where |
|---|---|---|
| Run an experiment on real users | Head of Support and Head of Compliance sign; the DPO reads the protocol first | `06_ab_protocol.md` · `governance.md` Sessions 6–8 |
| Read the weekly numbers and act | Head of Support (Head of Compliance for serious errors) | §2 of this file |
| Press the switch | day: Head of Support, with a named backup; night: NAVY on call | §7 · `governance.md` Sessions 4 and 7 |
| Approve a release (prompt, model, rules, approved content) | Head of Support, after NAVY's gate of §3; Head of Compliance when a policy rule changes | §3 · `evals/README.md` |
| Keep the trace; answer a merchant or a regulator | Tech lead keeps the trace; Head of Compliance answers, with the DPO for any data request | §5 · `governance.md` Session 7 |

## 9 · What this plan does not cover

The rate of rare serious errors cannot be certified by these samples (`governance.md` Session 2). The demo has no 24/7 on-call, no hosted alerting and no durable hosted state. Retention of traces and audit logs awaits the DPO decision (90 days is a proposal). These are requirements for the pilot, not claims about the demo.
