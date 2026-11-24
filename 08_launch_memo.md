# 08 · Launch memo — NAVY · Keelpay support copilot

> Session 8 deliverable. Draft of 23 November 2026, to be signed off by the team before the `v1.0` tag. It closes the series 00–07: every number below is already in one of those files; none is new. Keelpay is fictional; the demo runs on synthetic data only.

## 1 · Decision

| Scope | Decision | Why, in one line |
|---|---|---|
| Course demo (synthetic tickets, simulated send) | **GO — delivered** | The full flow runs end to end in a local container demo with a human on every send (PR #72); the Qualifier is the measured champion D-q4. |
| Keelpay pilot (real tickets, 46 agents) | **CONDITIONAL GO** | The routing criterion of the brief is met, `copilot_mode` (#60) is verified, and three pre-pilot conditions (§3) remain open while value awaits A/B measurement. |
| Production rollout | **NO-GO today** | Decided only by the pre-registered A/B (`06_ab_protocol.md` §7), never before. |

Same decision as the investment memo of Session 2 (`02_investment_memo.md`); what changed since is the evidence behind it.

## 2 · What we know, and how sure

| Level (`05_metrics.md` §1) | Evidence | Strength |
|---|---|---|
| Model | D-q4 on test_natural: 0.7 silent errors per 100 against 33.9 for the best classical baseline, 1 urgent ticket of 167 in a wrong desk, 97.9 % valid outputs (`scoring_protocol.md` §8) | strong on synthetic tickets; frozen tests read once |
| Model, hand-written tickets | runtime Qualifier on the 100 cases of `evals/eval_set_v1.csv` (23 Nov): 97 % valid against the contract, 83 % desk accuracy, 79 % auto-routed, 1 urgent ticket of 19 in a wrong desk, 12 % silent errors (after the reference repair; 94 % / 80 % / 76 % before); 15.8 % silent errors among auto-routed tickets, above the 1-in-7 manual baseline (`data/runs/regression/`, CI gate `qualifier-regression`) | **does not meet the bars** on an adversarial set; the gap to the synthetic test is the open question |
| Cost | D-q4 on CPU: €0.59 per 1,000 tickets, about €21 a month; on the efficiency front with B2, and dominates every other candidate (`02_investment_memo.md`) | strong |
| Workflow | 50 hand-written tickets: 74 % routed automatically, 2.7 % misrouted (p = 0.024 against 1 in 7), 0 urgent misroute: **the success criterion of the brief is met** (`evals/report_v0.md`) | moderate: 50 cases, interval up to 13.8 % |
| Drafts | 2 of 30 sendable for both graders before grounding; grounded drafts, Evidence gate and Policy check built since, **not yet re-measured** | weak: the open question |
| Judge | human–judge agreement 95.8 %, human–human 80 % (κ 0.33) (`05_metrics.md` §5) | moderate |
| Segments & fairness | `eval_set_v1.csv` (100 cases): FR vs EN draft-eligible 72.5 % vs 66.1 % (p = 0.656), misrouting 12.1 % vs 11.9 %; `payments` has 0 % silent errors (0/25) vs 16.0 % on `disputes` (`evals/05_segment_fairness.ipynb` §2) | moderate: supports starting Stage 2 on `payments` and disputes last |
| Value | +€194k base, +€214k expected net in year 1; beats the next-best project only if total time saved ≥ 13.32 % (`02_sizing.xlsx` `Decision!D57`) | **assumption**: measured only by the A/B |
| Rare serious errors | not certifiable at this sample size (`governance.md` Session 2) | controlled by stopping and rollback rules, not by evidence |

The stage-2 gate of the investment memo is **not met** on the eval-set (78 % right first time against 90 %; 88 % valid outputs against 98.5 %): the router is safe but hands too much to people. Field check (repairing one bad field instead of rejecting the output) is the answer in `spec.md` v2; it must be re-measured.

## 3 · Launch plan

**Stage 0 — before the pilot (conditions of the CONDITIONAL GO).** Each has an owner and a closing proof; three remain open (#60 closed on 24 November 2026), and the pilot does not start with one open.

| # | Condition | Proof | Owner |
|---|---|---|---|
| 1 | Draft quality re-measured with grounding: eval-set v1 replay, two graders + judge | sendable share and zero drafts on tickets that belong to a person | NAVY |
| 2 | `copilot_mode` switch built and tested at L1 and L3 (#60) | **Closed (24 Nov):** 100-case eval-set at `l1_drafting_off` produces 0 drafts; FIFO manual queue verified at `l3_copilot_off` (`flow/rollback_check.py`) | NAVY |
| 3 | Merchant isolation, idempotent send, persistence across restart tested in the backend (#31) | tests in the sub-project | Tech lead |
| 4 | Legal basis, retention and provider terms for real tickets; models and traces inside Keelpay cloud | DPO decision in `governance.md` | DPO / Legal |

**Stage 1 — pilot = the A/B** (`06_ab_protocol.md`): one copilot-off baseline week, then six weeks of staggered crossover over the 46 agents, half the conversations in the copilot stream. Monitoring layers 0–2 of `07_operations.md` run from day one; any rollback criterion applies at once.

**Stage 2 — rollout, only on GO at week 7:** the adoption ramp of the sizing (15 % → 35 % → 55 % → 70 % of tickets by quarter, `Inputs!D39:D42`), one desk at a time, payments first (largest share, fewest deadlines), disputes last. Each step needs four quiet weeks of layer 2 and no open incident.

| A/B result (`06_ab_protocol.md` §7) | Next |
|---|---|
| Reduction ≥ 13.32 %, guardrails held | Stage 2 |
| Between 5.93 % and 13.32 % | iterate on drafting, re-test; no rollout |
| Below 5.93 % or interval includes 0 | stop; build the rules-only context attach (next-best) |

**Rollback:** by prompt, model or copilot level, criteria and owners in `07_operations.md` §4. Any one criterion is enough.

## 4 · What we will not claim

That the copilot saves time (sized, not measured); that serious errors are rare (not certifiable here); that synthetic scores transfer to Keelpay mail (synthetic tickets are cleaner, `scoring_protocol.md` §7); that a person on every send makes the system safe on its own (automation bias, `07_operations.md` §1).

## 5 · Who did what

From the Git history of `main` and open pull requests on 23 November 2026, and from the files that name their authors. **Each member confirms or corrects their line before the tag.**

| Member | Git handle | Main contributions (files) |
|---|---|---|
| Vincent Lamy | Vincent-20-100 | Case redefinition and sizing (00–03, PR #3, #4); LLMOps sub-project: dataset, scoring and baselines, fine-tuning and compact variants of the Qualifier, Vertex registration; flow v2 design and build, API, front end, container demo (PR #18, #23, #28, #29, #46, #69, #70, #72); presentation storyline; Vertex endpoint and demo agent (in progress) |
| Alexandre Waerniers | Xenodion | First pitch, sizing and investment memo (PR #1, #2); course deliverables: problem statement, product brief, lean canvas, prototype, spec v2, governance (Sessions 3–5), `05_metrics.md`, eval-set v0/v1, eval report v0, judge prompt and grading (PR #26, #27, #71) |
| Yoni Mahieddine | InoyDev | Grader in the two-grader agreement (`05_metrics.md` §5); `06_ab_protocol.md` and its sample-size notebook (PR #85); `07_operations.md` and its monitoring notebook (PR #86); efficiency front in `02_investment_memo.md` (PR #87); this memo |
| Nahel Bachiri | nbachiri-oss | Grader in the two-grader agreement (`05_metrics.md` §5, `evals/grading/`); `copilot_mode` rollback switch and 100-case L1/L2/L3 verification (`flow/rollback_check.py`, #60); FR/EN fairness and desk segment audit (`evals/05_segment_fairness.ipynb`, `05_metrics.md` §3); rollback and segment alignment across `03`, `04`, `06`, `07` and this memo |

The course rule — commits in at least four numbered files per member, from the member's own account — is checked on `main` before the tag (#65).

## 6 · Before the tag `v1.0`

- [ ] Pull requests of the S6–S8 deliverables merged; READMEs match the code (#82).
- [x] `spec.md` and `03_product_brief.md` final, with the rollback plan of `07_operations.md`.
- [ ] Section 5 confirmed by all four members.
- [ ] Tag `v1.0` on `main` by the team, before the first oral of the cohort (human sign-off; not automated).
