# 06 · A/B protocol — NAVY · Keelpay support copilot

> Session 6 deliverable, pitch beat 8. **Pre-registered on 23 November 2026, before any pilot data exists.** The test runs only inside the Keelpay pilot (CONDITIONAL GO, `02_investment_memo.md`), after Support and Compliance sign-off; the course demo runs on synthetic tickets and produces no A/B data. Every number is a cell of `02_sizing.xlsx` (cited `Sheet!Cell`), a result of `05_metrics.md`, or a named assumption that the baseline week replaces. Sample size and duration: [`evals/06_ab_sample_size.ipynb`](evals/06_ab_sample_size.ipynb).

## 1 · Hypothesis

**H1:** for the same agents, tickets handled with the copilot (qualified fields, desk from the Routing Node, merchant-scoped facts, cited draft, Validator) take **less hands-on time** than tickets handled the current way, **at a quality no lower**.
**H0:** no difference in hands-on minutes per ticket.

| | Metric (definitions in `05_metrics.md` §3) | Test | Decision bar |
|---|---|---|---|
| **Primary** | Hands-on minutes per ticket, queue waiting excluded | two-sided, α = 0.05 | relative reduction, read against 5.93 % · 12.79 % · 13.32 % (`Decision!D56`, `D58`, `D57`) |
| Guardrail | Urgent tickets routed automatically to the wrong desk | none: a floor | 0 |
| Guardrail | QA score of sent replies (weekly sample) | non-inferiority, one-sided α = 0.05 | margin 0.25 SD of the QA rubric |
| Guardrail | Uncaught serious errors, per category | not powered: stopping rule (§6) | ≤ pessimistic values 0.075 % · 0.18 % · 0.12 % (`Flow!C19:C21`) |
| Counter-metric | Repeat contact within 7 days | non-inferiority, one-sided α = 0.05 | margin +1.5 points |
| Counter-metric | Drafts on the wrong payment validated unread | descriptive, with seeded wrong drafts | reported per arm |

Only the primary decides the effect; guardrails and counter-metrics can only stop or veto. No other metric is promoted after the fact.

## 2 · Unit of randomisation and design

`05_metrics.md` fixed the principle: **copilot-on and copilot-off weeks for the same agents**. We make it a **staggered crossover** so that every week has both arms and every agent works in both:

- **Agents** (46, `Inputs!D7`) are randomised into two groups of 23, stratified by desk and seniority (new · experienced). Group 1 is copilot-on in odd weeks, group 2 in even weeks. A fixed seed, recorded before the start, draws the groups.
- **Conversations** are split 50/50 at arrival by a hash of the first `ticket_id` of the thread: a **copilot stream** (Routing Node, draft, Validator) and a **manual stream** (today's triage and writing). Later turns of the same thread keep their stream, so a merchant's issue is never handled half by each arm and repeat contacts stay in their arm.
- An agent in a copilot-on week takes only copilot-stream tickets; in a copilot-off week, only manual-stream tickets. The two streams and the two groups are the same size, so load stays balanced.

**Unit of randomisation:** the agent, for the week sequence, and the conversation, for the stream. **Unit of analysis:** the ticket, with errors clustered by agent-week. **Model:** linear model of hands-on minutes (no log transform, so the effect stays in minutes) on arm, agent and week fixed effects, minutes capped at the 99th percentile of the baseline week (cap fixed before the first copilot-on week). The effect is reported as a relative reduction with its 95 % interval.

Why not simpler designs: tickets alone would let one agent see both arms within a day and hide the learning effect; whole weeks for the whole team would leave six units and confound the arm with the calendar; agents alone (two fixed groups) would confound the arm with the agents. Spillover remains: agents learn from drafts and may write faster in copilot-off weeks. It biases the effect **towards zero**, so the test is conservative; it is checked by the arm × period interaction (§5).

## 3 · Minimum detectable effect and sample size

**MDE = 6 % relative (0.6 min on ~10 min, `Inputs!G7`)** — the break-even saving (5.93 %, `Decision!D56`). A smaller effect loses money whatever else happens, so the test must be able to see an effect of that size. Power 0.80, α = 0.05 two-sided.

| Input | Value | Source |
|---|---|---|
| Volume | 36,900 tickets a month → 8,515 a week, 4,258 per arm | `Inputs!D6` |
| Cluster size | 191 tickets per agent-week | `Inputs!D11` × 5 days |
| Spread of hands-on time | CV = 1.0 | **assumption** (right-skewed service times) |
| Clustering | ICC = 0.02 between agent-weeks | **assumption** |

| Result (notebook §1–§2) | Value |
|---|---|
| Tickets per arm, independent | 4,360 |
| Design effect `1 + (m − 1) × ICC` | 4.8 |
| **Tickets per arm** | **≈ 20,900, i.e. 4.9 weeks** |
| MDE reachable in 6 weeks | 2.5 % (ICC 0) · 4.2 % (0.01) · 5.4 % (0.02) · 8.0 % (0.05) |
| QA sample | 198 scored replies per arm → **35 per arm per week** |
| Repeat contact, margin +1.5 points on a 10 % base (assumption) | 14,300 tickets per arm, within the 25,500 available |
| Uncaught serious errors, doubling of 0.0745 % (`Decision!D59`) | 31,600 tickets per arm (7.4 weeks) *and* every error found: **not powered** |

## 4 · Duration

| Week | What happens |
|---|---|
| 0 | **Baseline week, copilot off for everyone.** Agents are trained on the copilot outside production. Measures CV, ICC, the 99th-percentile cap, the repeat-contact base and the SD of the QA score. These nuisance values replace the assumptions **once**; the horizon is recomputed with the notebook and capped at 10 weeks. No treatment data is looked at. |
| 1–6 | Staggered crossover: 3 copilot-on and 3 copilot-off weeks per agent. Weekly checks of §6 only. |
| 7 | 7-day repeat-contact window closes for tickets of week 6; **single read of the primary**. |

Six crossover weeks cover the 4.9 weeks of the base case and keep the MDE under the 12.8–13.3 % thresholds even at ICC 0.05. Whole weeks only: no read at a day count, and holiday weeks are excluded in pairs (one of each group sequence).

## 5 · Segments

Pre-registered segments, from `05_metrics.md` §3 and the S3 data audit: **language** (French · English · other) · **desk** (payments · disputes · technical / API · compliance · Re-router) · **ticket difficulty** (clean · hard) · **urgency** (`high` · other) · **agent seniority** (new · experienced).

- Each segment effect is reported with its interval; **no segment decides the launch**, none is powered on its own, and none is searched for after the read.
- Fairness, named and baselined offline in `05_metrics.md` §3 (`evals/05_segment_fairness.ipynb` §2): selection-rate parity (share of tickets that get a draft, by language — offline on `eval_set_v1.csv`: `72.5 %` in French vs `66.1 %` in English, Fisher `p = 0.656`; on `test_natural`: `71.2 %` vs `70.1 %`) and equal error rates (misrouting among auto-routed tickets `12.1 %` FR vs `11.9 %` EN on `eval_set_v1.csv`, whereas `payments` has `0 %` silent errors against `16.0 %` on `disputes`).
- Checks reported with the primary: arm × period (learning and carry-over), first three weeks against last three (novelty).

## 6 · Stopping rules

**No early stop for success.** The primary is read once, at week 7. Weekly reviews look only at the rules below; any of them stops or narrows the test, whatever the primary looks like.

| Trigger | Action | Owner |
|---|---|---|
| One urgent ticket routed automatically to the wrong desk | review that ticket within 24 h; second case → routing off for urgent tickets (`copilot_mode = l2_routing_off`) | Head of Support |
| One uncaught serious error caused by the copilot reaches a merchant | immediate review; affected desk to L1 (`copilot_mode = l1_drafting_off`, no draft) until explained | Head of Compliance |
| Serious errors above the pessimistic value of a category (`Flow!C19:C21`) | **stop the test**: copilot off (`copilot_mode = l3_copilot_off`) | Head of Compliance |
| Harm threshold of `governance.md` Session 5 (repeat contact higher in copilot-on weeks two weeks in a row, or Re-router corrections above 1 in 7) | drafting off on that segment (`l1_drafting_off`) | Head of Support |
| QA score of copilot replies below the margin two weeks in a row | drafting off (`l1_drafting_off`); test paused | Head of Support |
| Sample-ratio mismatch on the stream split (χ², p < 0.001) | pause the analysis; fix the assignment; affected week discarded | NAVY |
| Copilot unavailable for more than 10 % of a week's copilot-stream tickets, or a model, prompt, rule or threshold changes | the week does not count; it is replaced at the end | NAVY |

A paused or narrowed test restarts only on the owner's decision, written in `governance.md`.

## 7 · Decision at week 7

| Result on the primary (guardrails held) | Decision |
|---|---|
| Interval excludes 0 and the reduction is ≥ 13.32 % | GO to the staged rollout of `Inputs!D39:D42` |
| Reduction between 5.93 % and 13.32 % | ITERATE: the copilot pays but loses to the next-best project; work on drafting, re-test |
| Interval includes 0, or reduction < 5.93 % | NO-GO: keep the rules-only context attach (the next-best) |
| Any stopping rule fired | the stop decides, not the primary |

What this test cannot tell: rare serious-error rates (governance Session 2), effects on merchants beyond repeat contact, and effects after the novelty wears off. Those go to the monitoring of `07_operations.md`.
