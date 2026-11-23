# 02 — Investment Memo

**Decision: GO to build and evaluate the synthetic end-to-end demo; CONDITIONAL GO for a Keelpay pilot only after full-flow value, constant QA, residual-risk controls, and governance are validated.** No production rollout is approved. External Drafter Model and Langfuse use are demo-only for non-critical synthetic data.

Keelpay volume and workflow figures are fictional scenario inputs. Costs, adoption, errors, and savings are assumptions in [the sizing workbook](02_sizing.xlsx), not observed outcomes.

| Year 1 annualized net value | Low | Base | High | Weighted EV |
|---|---:|---:|---:|---:|
| Copilot | −€78,444 | +€194,298 | +€703,462 | **+€214,308** |
| Probability | 30% | 50% | 20% | — |
| Do-nothing | €51,840 | €92,988 | €181,440 | €98,334 EV |
| Next-best: rules-only context attach | €11,656 | €100,183 | €236,274 | €100,843 EV |

## How much?

Base year-one cash illustration is **€137,631**, distinct from €194,298 annualized net after amortization. Holding Q4 adoption for a full year yields €355,476 annualized net. These are model outputs, not forecasts. The year-one ramp handles an assumed 39,253 time-saved ticket equivalents. At full adoption, assumed active-time savings are 20.262%: 6.6 percentage points from reading/assignment and 13.662 from lookup/drafting. Gross capacity value is €274.8k plus €36.5k avoided handover cost.

## How sure?

The 20.262% saving and 0.0745% weighted serious-error input are assumptions, not measured full-flow or post-review outcomes. Base annualized costs include €41.4k assumed serious-error cost, €1.3k processing, and €74.3k fixed/semi-fixed costs. D-q4 has a useful synthetic component benchmark, but does not validate routing policy, reply quality, human review, or time saved; it also beats the prompted base model (10.5 silent errors per 100 for B3 against 0.7).

Under fixed base assumptions, total active-time savings must reach 5.93% to break even, 13.32% to beat the base next-best, and 12.79% to beat base do-nothing. These thresholds move when assumptions change; they are not accuracy targets.

## What if we’re wrong?

The Low case loses €78,444 and misses the Base next-best hurdle. A one-variable sensitivity gives €55.1k net at 10% saving and €326.4k at 30%. A roughly 200-case exploration cannot certify a rare error rate; twenty cases check the contract only. Do not pilot unless comparable full-flow tasks show value at constant QA and the serious-error controls are validated.

## Compared to what?

Weighted project EV exceeds weighted next-best by **€113.5k** and do-nothing by **€116.0k**. Moving the full 20-point optimistic probability weight to Base still leaves €112.5k EV versus the €100.2k Base next-best hurdle; a 22.41-point shift would be needed to cross it. Probabilities remain judgments. Demo external API/trace costs need a separate budget; no real ticket may go to an external service.

## Which Qualifier? The efficiency front

Infrastructure cost per 1,000 tickets against expected error cost per ticket, on `test_natural` (610 tickets). Error cost = model silent errors (`scoring_protocol.md` §8) × €252.5, the cost of one wrong answer weighted by category (`Inputs!D14:D16` × `Inputs!D30:D32`). Infrastructure = measured seconds per ticket × €0.00008 a second of serverless CPU, or a T4 endpoint on 24/7 at €255 a month spread over 36,000 tickets (`scoring_protocol.md` §6). Training is paid once (2 h 06 of T4 for D) and left out.

| System | Infra per 1,000 tickets | Expected error cost per ticket | On the front? |
|---|---:|---:|---|
| B2 TF-IDF + logistic regression | ≈ €0.00 | €85.60 | yes: cheapest |
| B3 base Qwen 3B, prompted (T4) | €7.08 | €26.51 | no: D-q4 is cheaper and better |
| D Qwen 3B + LoRA, fp16 (T4) | €7.08 | €5.05 | no |
| D-q8 (CPU) | €0.71 | €2.52 | no |
| **D-q4 (CPU)** | **€0.59** | **€1.77** | **yes: chosen** |

Only B2 and D-q4 are on the front; B0 and B1 cost the same as B2 and err more. Going from B2 to D-q4 adds €0.59 per 1,000 tickets (about €21 a month) and removes about €84 of expected error cost per ticket: the fine-tuned, quantised model is the choice under any plausible price. The error cost is an upper bound before human review (every silent error is assumed to reach a merchant) and the error costs are guesses; neither changes the ordering. A Vertex CPU endpoint billed 24/7 instead of serverless CPU moves D-q4 to the right; it stays on the front (lowest error of all) and stays the choice while its extra cost per ticket is below the €84 of error it removes.

**Sources:** fictional scenario in [README](README.md); assumptions and sensitivities in [02_sizing.xlsx](02_sizing.xlsx); component evidence in the [LLMOps project](agentic-workflow-subproject/README.md); product gates in [spec](spec.md).

**Build / buy / orchestrate:** Orchestrate an in-house, tenant-scoped workflow around the Qualifier Model, deterministic Routing Node, and human sending; consider a bought Drafter Model only if it runs within the fictional production cloud boundary and beats the validated build case.
