# Feature 011 — Confidence signals for reviewer attention

Status: research specification, 5 November 2026. Parallel to and non-blocking for the V1 demonstration. The goal is a validated attention indicator in the final control panel, not a promise of calibrated probabilities or a replacement for human review.

## User story

As a reviewer, I want an understandable warning when the Qualifier or Drafter has a demonstrably less reliable result, so that I can pay particular attention to the relevant field or draft while reviewing it. All drafts require review regardless of the indicator.

## Scope and contract

- Compare three project model candidates on matched labelled tickets. The exact three, their adapters, available probabilities, and comparable baseline must be explicitly confirmed before the protocol is frozen; do not assume a non-LLM baseline exposes token probabilities. Missing signals are recorded, never invented.
- Qualifier first: investigate generated-token log probabilities or other available model signals, particularly intent and urgency, and aggregate value tokens separately from JSON syntax. Account for tokenization, output constraints and decoding settings. Preserve raw outputs and model, tokenizer, prompt, quantization and inference versions. Return any signal as separate metadata; the seven-field JSON remains unchanged.
- Investigate Drafter separately: token probability alone is not evidence that facts are correct. Evaluate a signal only against an appropriate independently reviewed draft reference or factuality task; unavailable is an acceptable result. V1 direct drafting does not depend on this study.
- No model fine-tuning is required for the candidate study. Post-hoc calibration or threshold selection can use labelled validation data. Record additional inference time, compute cost and any effect of changing serving configuration.

## Evaluation protocol

1. Freeze candidate models, dataset versions, intended outcome, metric definitions and prediction settings before analysis. Use the same applicable labelled tickets, report missing/invalid predictions and valid denominators. Capture provenance and any lack of label independence. Preserve historical model comparisons as separate results if decoding or constraints change.
2. Produce candidate field-level signals and evaluate discrimination and calibration against verified labels, with uncertainty and per-slice results where sample size permits. Compare against simple baselines such as `UNDEFINED` and existing deterministic review rules. Do not interpret a token probability as a correctness probability without evidence.
3. Choose thresholds and at least two attention bands on validation only; three bands are desirable if data supports them. Evaluate the frozen rules on held-out natural and trap splits separately, without tuning on test results. Report uncertainty, counts and denominators, especially for urgent and silent errors.
4. Simulate threshold-based deferral on identical tickets and report silent and urgent wrong-desk errors flagged, missed, and remaining among automatically handled tickets; report automatic coverage and extra review workload. Report outcomes before and after deferral without claiming reviewers corrected flagged errors; any assumed correction scenario must be labelled as an assumption. Compare to current routing policy and its existing human-review rules.
5. If the signal is useful and stable enough, define field/model-specific versioned bands and expose them as metadata with provenance, freshness and unavailable/error states. Re-evaluate when model, prompt, decoding or data changes. No threshold alters production or demo routing automatically without a separate decision and validated policy update.

## Reviewer experience and acceptance

- The target is a clearly labelled Qualifier and/or Drafter attention indicator in the final control panel: green/orange/red where three validated bands are supported, or at least two bands otherwise. A low-confidence signal calls attention to the relevant field or response and explains what to check. Color is accompanied by text and an unavailable state; never display an unsupported numerical probability of correctness.
- The reviewer can see which component and model/version produced the indicator. The absence of a warning is not approval; no band bypasses validation or send gates.
- Study completion requires a reproducible comparison of the three confirmed candidates where technically feasible, results for natural and trap splits, selected-band rationale, error/coverage/workload trade-offs and a documented go/no-go per component. A negative result is valid: ship an unavailable state rather than a misleading color.
- Deployment of an indicator is a separate acceptance milestone: score provenance is auditable, band mapping is versioned, missing/stale scores are unavailable, and the workspace shows the correct attention state without blocking the rest of the V1.

## Dependencies and open questions

Dataset labels and model artifacts are available from the existing Qualifier campaign, subject to provenance verification. Confirm the three candidate model names, feasible probability access, independent draft labels, reviewer wording, operational ownership, evaluation budget and any future routing-policy change. Runtime metadata and monitoring contracts must accommodate an optional signal without changing the Qualifier JSON.
