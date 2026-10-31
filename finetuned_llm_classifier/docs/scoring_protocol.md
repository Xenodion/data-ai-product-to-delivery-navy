# Scoring protocol

**Frozen on 2026-10-31, before any model is scored.** If a metric or a rule changes after results are seen, the change is written at the end of this file with its date and its reason, and the results are reported under both versions.

## 1. What is scored, on what

| Set | Role | Used for |
|---|---|---|
| `test_natural` (500) | the natural mix of tickets | **all headline numbers** and the cost per ticket |
| `test_traps` (about 390) | at least 20 tickets per trap type | per-trap diagnosis only, never an overall score |
| `val` (300) | same mix as train | choosing hyperparameters and the baselines' settings; never reported as a result |
| `train` (2,000) | fine-tuning | nothing is scored on it |

Every model and every baseline is scored on the **same tickets**, so comparisons are paired. Only tickets accepted by the dataset chain are scored; the quarantine is never scored.

## 2. Metrics and why

A metric is in the table because a decision of the product depends on it (the copilot routes automatically, a human takes `UNDEFINED` and `OTHER`, an urgent ticket in the wrong desk is the costly error).

| # | Metric | Definition | Why |
|---|---|---|---|
| 1 | Valid JSON rate | share of outputs that parse and pass `TicketLabel` | an invalid output cannot be routed; it must be about 100 % |
| 2 | Desk accuracy | the desk (`payment_status` to payments, `dispute` to disputes, `technical_api` to technical, `compliance` to compliance; `OTHER` and `UNDEFINED` to human triage) equals the desk of the label | this is what the decision table acts on |
| 3 | **Urgent tickets in the wrong desk** | among labelled `urgency = high`, share whose predicted desk is a wrong *desk* (not triage) | the trap of the brief and its costliest error |
| 4 | Confident-and-wrong rate | among outputs that are neither `OTHER` nor `UNDEFINED` for `intent`, share whose `intent` is wrong | a confident wrong reading is worse than an abstention |
| 5 | Abstention | share of `OTHER` or `UNDEFINED` predicted, and precision of the answers that are not abstentions | measures how much work goes to humans and how reliable the rest is |
| 6 | Exact match, reference fields | `transaction_id`, `amount`, `currency`: exact string equality, `""` and `UNDEFINED` included | an extraction is right or wrong; the lookup that follows needs the exact value |
| 7 | Macro-F1 | `intent` and `sub_intent` | classes are balanced by design, so macro averaging shows weak classes |
| 8 | Recall on `high` urgency | share of labelled `high` predicted `high` | missing an urgent ticket is the costly side of urgency |
| 9 | Accuracy on `urgency` and `sentiment` | secondary | subjective fields, agreed at about 84 % and 93 % by the dataset chain: the ceiling is not 100 % |
| 10 | **Expected cost per ticket** | mean of the cost matrix below | one number for the sizing and the investment memo |

### Cost matrix (ASSUMPTION: relative weights, to be replaced by the euro values of `02_sizing.xlsx` when the memo is updated)

| Outcome | Weight |
|---|---|
| Correct | 0 |
| Prediction goes to human triage (`OTHER`, `UNDEFINED`) while the label has a desk | 1 |
| Wrong desk, ticket not urgent | 3 |
| Wrong `transaction_id`, `amount` or `currency` with a desk (the draft would use a wrong payment) | 5 |
| Wrong desk, ticket labelled `high` | 10 |

A ticket carries the largest weight among its errors. Metric 10 is reported with the weights above and with the weights doubled for the last row, to show how sensitive it is.

## 3. Compared systems

All run on the same inputs and the same output contract.

| Id | System | Notes |
|---|---|---|
| B0 | Majority class | floor |
| B1 | Rules: keywords and regular expressions | the "cheap" option of the brief |
| B2 | TF-IDF + logistic regression, one model per field | the classical ML option |
| B3 | The base small LLM, prompted (instruction of `src/prompt.py`), no fine-tuning | what LoRA must beat to be worth it |
| D | The same small LLM with the LoRA adapter | the candidate |

Baselines are tuned on `val` only.

## 4. Uncertainty and decision rule

- Paired bootstrap on the tickets of `test_natural`, 2,000 resamples, fixed seed, 95 % interval for every difference with the best baseline.
- Per-trap numbers on `test_traps` are counts with their denominators, with no interval claimed below 20 tickets.
- **D is kept if**, against the best of B1 to B3: expected cost per ticket is lower with an interval that excludes 0, **and** urgent tickets in the wrong desk (metric 3) are not worse, **and** valid JSON is at least 99 %. Otherwise the project reports that the simpler option is kept (ASSUMPTION of the margin: any difference with an interval excluding 0, no minimum size; to be revisited with the team before the run).

## 5. Known limits to state with the results

- Labels come from scenario cards and were checked by language models, not by humans; the tests were written by a different model than the train set, and a hand-written out-of-distribution set of about 30 tickets is reported separately.
- Tickets accepted by the chain are those on which independent readers agreed; on urgency and tone they are somewhat easier than real mail.
- Synthetic tickets are cleaner than real ones: absolute scores are optimistic, comparisons between systems are the finding.
