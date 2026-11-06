# Technical plan — confidence study

Status: proposed, parallel and non-blocking. See [spec.md](spec.md) and [demo plan](../005-010-demo-delivery/plan.md).

1. Confirm the three candidates and freeze a comparison matrix: model/artifact version, task, available token probabilities or alternative signal, datasets, baseline and cost. Record incompatibilities rather than inventing confidence.
2. Build an offline replay harness with model-specific adapters. Keep label data separate from inference; save raw predictions, selected token log probabilities where exposed, parsing offsets, decoding parameters, inference errors, latency and provenance. Validate availability on a small local sample before full replay.
3. Derive candidate signals for intent and urgency from value tokens; compare simple alternatives and existing `UNDEFINED`/review rules. Evaluate JSON constraints, multi-token labels and changes in inference settings as separate systems.
4. Select thresholds/bands and any post-hoc calibration on validation only. Freeze the analysis and run the natural and trap tests separately. Report calibration/discrimination where sample size permits, confidence intervals, invalid outputs and slice counts.
5. Simulate review thresholds over the same tickets and calculate errors flagged and missed, residual silent/urgent errors among automatic cases, coverage and workload. Do not assume reviewer correction; report any perfect-review scenario only as a clearly labelled upper bound.
6. Decide go/no-go per model and component. If useful, implement optional versioned score metadata and at least two text-labelled attention bands in the review panel; preserve unavailable/stale states. No automatic routing change without separate policy review.
7. Investigate Drafter separately against independently reviewed factuality/source evidence; never reuse token likelihood as a claim of factual accuracy.

Deliverables: frozen protocol, reproducible replay configuration, versioned results and plots, trade-off table, reviewer wording, documented limitations and integration decision. Existing #45 tracks this work. Full labelled replay may require billed compute; estimate and agree limits before starting it.
