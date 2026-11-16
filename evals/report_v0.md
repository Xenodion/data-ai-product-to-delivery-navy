# Eval report v0 — NAVY · Keelpay support copilot

**Date:** 13 November 2026   **Eval-set:** `evals/eval_set_v0.csv`, 50 cases, labelled by hand before the run   **Prototype:** `agentic-workflow-subproject/flow/` at commit `e9ed0d9` with the `--tickets` option of `flow/runner.py`; Qualifier D-q4 (`model-q4.gguf`, md5 `b23b4f30…`, CPU), Routing Node `routing-node-v1`, Drafter `mistralai/mistral-nemo` (`drafter-v1`). Run file: `.local/runs/20261113T094306Z_eval_set_v0.jsonl` (local).

Command: `uv run python -m flow.runner --tickets ../evals/eval_set_v0.csv` — one run, no setting changed before or after.

## 1. The number against the criterion
| | Value |
|---|---|
| Success criterion (`03_product_brief.md` §7) | *"…routing at least 50 % of tickets automatically with misrouting significantly below the 14 % manual baseline, while 0 urgent tickets are auto-routed to the wrong desk."* |
| **Routed automatically** (not sent to the Re-router) | 37 / 50 = **74 %** — bar ≥ 50 % |
| **Misrouted among the tickets routed automatically** | 1 / 37 = **2.7 %** (NAVY-EV-16) — baseline 1 in 7 = 14.3 % (`02_sizing.xlsx` `Flow!D26`); exact one-sided binomial test p = 0.024; 95 % interval 0.5 %–13.8 % |
| **Urgent tickets auto-routed to the wrong desk** | **0** of 8 urgent tickets routed automatically — bar 0 |
| Right desk first time (Re-router hand-overs count as not right) | 39 / 50 = 78 % — the stage-2 gate of `02_investment_memo.md` asks ≥ 90 % |
| Qualifier output valid against the contract | 44 / 50 = 88 % — the scoring protocol asks ≥ 98.5 % |
| Drafts produced | 50 / 50; none grounded (lookup and retrieval are not built: the Drafter has no evidence) |
| Drafts on tickets that belong to a person (labelled `OTHER` / `UNDEFINED`) | 4 of 4 (should be 0); and all 13 tickets sent to the Re-router also got a draft |
| Policy blocks | not measurable: the policy check is not built |
| Drafts two graders would send without editing | **2 / 30 = 7 %** (30-case sample of `evals/eval_set_v1.csv`; one grader passed 2, the other 8) |
| Qualifier latency | median 6.8 s, max 18.8 s (first ticket, model warming up) |

**Verdict:** the criterion of the brief is **met** — on 50 hand-written tickets, three quarters are routed automatically, misrouting among them is significantly below the manual baseline, and no urgent ticket reached a wrong desk; every Qualifier failure fell back to the Re-router. The sample is small: the upper end of the interval (13.8 %) sits just under the baseline. The **stage-2 gate of the memo is not met** (78 % right first time against 90 %; 88 % valid outputs against 98.5 %): the router is safe but hands over too much.

Field-level accuracy of the Qualifier (exact match, 50 tickets): intent 39, sub-intent 33, transaction ID 44, amount 41, currency 43, urgency 31, sentiment 34. Urgency is wrong in both directions (a webhook outage, NAVY-EV-04, read as `low`); it never changes the route, but agents would see the wrong priority.

These tickets are hand-written and messier than the synthetic test sets of the sub-project, whose scoring protocol warns that its own scores are optimistic.

## 2. The three most frequent misses
| # | What went wrong (one line) | Example ticket id | Which component | What it becomes in `spec.md` v2 |
|---|---|---|---|---|
| 1 | The Qualifier output is rejected by the contract (6 of 50): a malformed reference copied as is (`TX-712O44`, `TX-70A118`), a sub-intent from another desk (`amount_mismatch` under payments), an invented sub-intent (`retrocharge` for a French chargeback), a missing key | NAVY-EV-38 (urgent French chargeback), EV-07, EV-26, EV-32, EV-46, EV-47 | Qualifier (the contract check worked: each went to the Re-router) | A field check before routing: a malformed reference becomes `UNDEFINED` instead of rejecting the whole output, and a valid intent with an invalid sub-intent still routes on the intent |
| 2 | The Qualifier abstains (`UNDEFINED`) on tickets with a clear desk (4 of 50) | NAVY-EV-23 ("where is my money"), EV-19, EV-25, EV-43 | Qualifier | Abstention is measured on the hand-written eval-set, not only on synthetic val; French and English dispute vocabulary without the word "chargeback" is added to the training and evaluation data |
| 3 | A draft is written for every ticket, including the 13 sent to the Re-router and the 4 that belong to a person | NAVY-EV-14, EV-15, EV-18 (labelled `OTHER` / `UNDEFINED`) | Flow (`flow/pipeline.py`: "The Drafter attempts every ticket") | A ticket sent to the Re-router gets no draft until a person confirms its desk — `spec.md` §4 aligned with flow v2 and the grading guideline |

## 3. Who graded, and how
Two team members, Yoni and Nahel, graded the drafts of the 30-case sample listed in `evals/README.md`, alone, with the verdicts PASS / FAIL / ESCALATE and the six criteria of the grading guideline (`evals/grading/`). They agree on 24 of 30 verdicts (80 %, Cohen's kappa 0.33); the 6 disagreements are all FAIL against PASS, on two boundaries the guideline leaves open (C5 and C6, `evals/README.md`) — not resolved by discussion, so that the rate stays as measured; the guideline is clarified after the judge run. The routing numbers in §1 need no grader: they compare the run with the hand labels. The 15 sample cases beyond row 50 come from a second run on 13 November (`--tickets ../evals/eval_set_v1.csv --ids …`).

## 4. What is demo data and what is eval data
No prompt, rule or threshold was tuned before or after the run; the labels were written before it (rows 1–20 on 2 November, rows 21–50 on 13 November) and not changed since. Tickets read in detail after the run: NAVY-EV-01 (first-line check while the run was going) and the six invalid outputs (EV-07, EV-26, EV-32, EV-38, EV-46, EV-47), to find the cause of the misses. They stay in the eval-set; if any change is tuned while looking at them, they become demo data and are named here.

## 5. Next step (one line)
Turn the three misses into `spec.md` v2 lines, have two people grade the 30-case sample, then rerun once on `evals/eval_set_v1.csv` (100 cases) after the fixes.
