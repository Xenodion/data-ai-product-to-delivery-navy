# Scoring protocol

Version of 2026-11-02. Historical model/scorer criteria below are retained as originally evaluated. Current product behavior is defined in the root `spec.md` and `docs/design/copilot-workflow.md`; the Routing Node has not yet been implemented. Test sets were read once, with the same predictions as in the journals; no system was re-trained after reading them.

## 1. What is scored, on what

| Set | Tickets | Role | Used for |
|---|---|---|---|
| `test_natural` | 610 | the natural mix of tickets | **all headline numbers** |
| `test_traps` | 380 | at least 20 tickets per trap type, 23 types | per-trap diagnosis only, never an overall score |
| `val` | 293 | same mix as train | choosing hyperparameters and the baselines' settings; never reported as a result |
| `train` | 1,922 | fine-tuning | nothing is scored on it |

Every system is scored on the **same tickets**, so comparisons are paired. Only tickets accepted by the dataset chain are scored; the quarantine is never scored.

## 2. What can happen to a ticket

The historical scorer used intent-to-desk mapping and counted unsupported/undecidable intents or malformed output as handed to a person. It did not execute the current dependency-aware Routing Node. A person was assumed to read every draft. Thus the historical model outcome had three scored costs:

| Outcome | What happens | How bad |
|---|---|---|
| **Right** | right desk, right references | none |
| **Sent to a human** (triage) | a person routes it by hand | small: extra work, no damage |
| **Silent error** | routed to a desk with a wrong desk or a wrong `transaction_id`, `amount` or `currency` | the worst: nothing flags it, the draft is built on a wrong reading, the reviewer may miss it and the merchant acts on it |

An urgent ticket in the wrong desk is a serious model-level failure in this benchmark. Current product policy allows draft preparation to continue while priority is surfaced; a Support Agent reviews every draft. The benchmark does not measure actual urgency handling or human recovery.

## 3. Metrics

Every metric is in the table because a decision of the product depends on it.

| # | Metric | Definition | Why |
|---|---|---|---|
| 1 | **Silent error rate** (main metric) | share of all tickets that are routed to a desk with a wrong desk or a wrong reference field | the error that can reach a merchant unnoticed |
| 2 | **Urgent tickets in the wrong desk** | among tickets labelled `urgency = high`, share routed to a wrong desk (triage is not a wrong desk) | the trap of the brief and its guardrail |
| 3 | **Sent to a human without need** | share of all tickets sent to triage although the label has a desk (invalid outputs included) | the price of caution: more work for the agents, no damage. Read it together with metric 1: a system that sends everything to a human has no silent error and no use |
| 4 | **Auto-routed rate** | share of all tickets routed to a desk by the system (at most 84 % on `test_natural`: 16 % of the labels are `OTHER` or `UNDEFINED`) | the product needs at least half of the tickets routed without a human |
| 5 | **Desk accuracy** | predicted desk equals the label's desk (`payment_status` to payments, `dispute` to disputes, `technical_api` to technical, `compliance` to compliance; `OTHER` and `UNDEFINED` to triage) | first-pass routing, the bar of the brief |
| 6 | **Error severity score** | mean of the severity matrix below, in points | one number summarising how bad the errors are; breaks ties between systems |
| 7 | Exact match, reference fields | `transaction_id`, `amount`, `currency`: exact string equality, `""` and `UNDEFINED` included | the lookup that follows needs the exact value |
| 8 | Macro-F1 | `intent` and `sub_intent` | classes are balanced by design, so macro averaging shows weak classes |
| 9 | Recall on `high` urgency | share of labelled `high` predicted `high` | missing an urgent ticket is the costly side of urgency |
| 10 | Accuracy on `urgency` and `sentiment` | secondary | subjective fields, agreed at about 84 % and 93 % by the dataset chain: the ceiling is not 100 % |
| 11 | Valid JSON rate | share of outputs that parse and pass `TicketLabel` | diagnostic only: an invalid output is routed to a human, so it counts in metric 3, not as a silent error |

### Error severity score (points; ASSUMPTION: relative weights, not euros)

| Outcome | Points |
|---|---|
| Correct | 0 |
| Sent to a human while the label has a desk (`OTHER`, `UNDEFINED`, invalid output) | 1 |
| Wrong desk, ticket not urgent | 3 |
| Wrong `transaction_id`, `amount` or `currency` with a desk (the draft would use a wrong payment) | 5 |
| Wrong desk, ticket labelled `high` | 10 |

A ticket carries the largest weight among its errors. The score is also reported with the last row doubled (20 points) to show how sensitive it is. The points are in the order of the costs of the investment memo (a hand-over costs a few euros, an uncaught serious error 150 to 400 euros, `02_investment_memo.md`), but they are not euros; the euro translation belongs to the memo.

## 4. Acceptance criteria (from the product brief)

The first three rows are component bars carried by the historical benchmark. The last row is a separate product risk proposal from governance, not a Qualifier score.

| Criterion | Threshold | Source |
|---|---|---|
| First-pass routing | desk accuracy of at least 90 % | sizing flip point (about 90 %); today about 86 % (scenario) |
| Automatic routing | auto-routed rate of at least 50 % | sizing base case 55 % |
| Guardrail, urgent | no urgent ticket routed automatically to a wrong desk | brief |
| Post-deployment risk proposal | incremental serious errors reaching merchants below 0.1 % of tickets versus control; denominator and protocol still to approve | governance; not measurable by the model-only scorer |

Only the first three rows can be inspected in this model-only benchmark. Current product behavior permits draft preparation for high-priority tickets while surfacing priority; every draft still receives Human Review. A model-level miss does not establish full-flow failure, and a model-level pass would not prove the integrated flow is safe. The end-to-end demo evaluation is future work and requires separate fixtures/oracles; it is not an already executed S4 result.

## 5. Model selection rule

The candidate is compared with the best of the baselines B1 to B3 on `test_natural`, paired bootstrap, 2,000 resamples, fixed seed, 95 % interval.

**The fine-tuned model is kept if** (1) its silent error rate and its error severity score are lower, with an interval of the difference that excludes 0, **and** (2) its urgent tickets in the wrong desk are not worse. Otherwise the project reports that the simpler option is kept; this is a valid result. Among the fine-tuned variants (D, D-q8, D-q4) the champion is the one with the fewest silent errors and the lowest severity score on `test_natural`, at the lowest infrastructure cost.

Per-trap numbers on `test_traps` are counts with their denominators, with no interval claimed below 20 tickets.

## 6. Systems compared

All run on the same inputs and the same output contract.

| Id | System | Runs on | State |
|---|---|---|---|
| B0 | Majority class (floor) | CPU | scored |
| B1 | Rules: keywords and regular expressions (the "cheap" option) | CPU | scored |
| B2 | TF-IDF + logistic regression, one model per field (classical ML) | CPU | scored |
| B3 | Base Qwen2.5-3B, prompted, no fine-tuning | T4 (Vertex) | historical inference run; local val export available and row-order validated; test exports and job provenance still missing |
| D | Qwen2.5-3B + LoRA, float16 | T4 (Vertex) | scored |
| D-q8, D-q4 | D merged, then GGUF 8 and 4 bits | CPU | scored |
| S-1.5B, S-0.5B | the same recipe on Qwen2.5-1.5B and 0.5B | CPU after GGUF | cancelled (`docs/compact_variants.md`) |

Baselines are tuned on `val` only (B2's regularisation `C`, by lowest severity score on val).

### Efficiency

Reported next to the quality; the result is a front, not a ranking.

- **Seconds per ticket**: measured one ticket at a time, model already loaded, on a named machine (val: AMD EPYC 7B12; test: Intel Xeon, both 8 vCPU).
- **Infrastructure cost per month** = mean seconds per ticket x 36,000 tickets x price per second of the CPU. ASSUMPTIONS: 36,000 tickets a month (scenario), 0.00008 euro per second (serverless CPU, 4 vCPU / 4 GB); the GPU alternative is a T4 endpoint on 24/7 at about 255 euros a month.
- **Training cost** once, as GPU hours x price, not spread over tickets.

## 7. Known limits

- Labels come from scenario cards and were checked by language models, not by humans; the tests were written by a different model than the train set.
- Tickets accepted by the chain are those on which independent readers agreed; on urgency and tone they are somewhat easier than real mail.
- Synthetic tickets are cleaner than real ones: absolute scores are optimistic, comparisons between systems are the finding. The "today" figure of the brief (1 ticket in 7 first routed to a wrong desk) comes from real operations: do not compare it with a score on synthetic tickets.
- The severity points are assumptions.

## 8. Results on the test sets (read once, Journal 5)

### `test_natural` (610 tickets, 167 urgent)

| System | Silent errors per 100 | Urgent wrong desk | Sent to a human without need, per 100 | Auto-routed | Desk accuracy | Severity score | Valid JSON |
|---|---|---|---|---|---|---|---|
| B0 majority | 78.5 | 77.8 % | 0.0 | 100.0 % | 23.6 % | 3.890 | 100.0 % |
| B1 rules | 40.3 | 33.5 % | 24.1 | 68.5 % | 44.6 % | 2.274 | 100.0 % |
| B2 TF-IDF + LR | 33.9 | 6.6 % (11) | 0.3 | 90.5 % | 91.6 % | 1.666 | 100.0 % |
| D (GPU) | 2.0 | 1.2 % (2) | 1.0 | 83.9 % | 98.0 % | 0.111 | 98.9 % |
| D-q8 | 1.0 | 0.6 % (1) | 1.6 | 82.8 % | 97.9 % | 0.067 | 98.2 % |
| **D-q4 (champion)** | **0.7** | **0.6 % (1)** | 2.0 | 82.5 % | 97.5 % | **0.054** | 97.9 % |

Paired bootstrap against B2, difference per ticket and 95 % interval: silent errors D -0.320 [-0.359, -0.280], D-q8 -0.330 [-0.369, -0.290], D-q4 -0.333 [-0.372, -0.295]; severity score D -1.554 [-1.756, -1.367], D-q8 -1.598 [-1.798, -1.415], D-q4 -1.611 [-1.811, -1.425]. All exclude 0.

### `test_traps` (380 tickets, diagnosis per trap family)

| System | Silent errors per 100 | Urgent wrong desk | Sent to a human without need, per 100 | Auto-routed | Desk accuracy | Severity score | Valid JSON |
|---|---|---|---|---|---|---|---|
| B0 majority | 92.6 | 88.4 % | 0.0 | 100.0 % | 12.6 % | 5.261 | 100.0 % |
| B1 rules | 44.7 | 28.8 % | 35.8 | 62.4 % | 37.9 % | 2.842 | 100.0 % |
| B2 TF-IDF + LR | 58.7 | 5.5 % | 1.1 | 95.8 % | 92.9 % | 2.971 | 100.0 % |
| D (GPU) | 1.3 | 0.7 % | 1.1 | 91.8 % | 98.7 % | 0.089 | 98.2 % |
| D-q8 | 1.3 | 0.0 % | 3.7 | 88.9 % | 96.3 % | 0.103 | 95.5 % |
| D-q4 | 1.3 | 0.7 % | 3.9 | 88.9 % | 95.8 % | 0.118 | 95.3 % |

On the traps D is a little better than D-q4 (fewer tickets sent to a human, more valid JSON): the compression costs some robustness on malformed ids, while `test_natural` favours D-q4.

### Reading against the acceptance criteria (D-q4, `test_natural`)

| Criterion | Threshold | D-q4 | B2 |
|---|---|---|---|
| Desk accuracy | at least 90 % | 97.5 %: met | 91.6 %: met |
| Auto-routed | at least 50 % | 82.5 %: met | 90.5 %: met |
| Urgent in a wrong desk | none | 1 of 167 (0.6 %): not met on the model alone | 11 of 167 (6.6 %) |
| Model-only silent errors (diagnostic, no 0.1 % gate) | lower than comparator under the selection rule | 0.7 % (4 tickets of 610) | 33.9 % |

The two first bars do not separate B2 from the fine-tuned models; silent errors do. The urgent guardrail fails on the model alone. The proposed 0.1 % limit concerns incremental serious errors after the complete flow versus a control, so this synthetic test cannot score it. The 0.075 % of uncaught serious errors in the investment memo is an assumption, not a measured reviewer catch rate.

### Registration

The champion D-q4 is registered in the Vertex AI Model Registry: `keelpay-router-json`, ID `7308774847222382592`, alias `qwen3b-lora-q4`, region `europe-west2`. No endpoint is standing.
