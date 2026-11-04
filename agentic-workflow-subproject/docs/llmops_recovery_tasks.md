# LLM fine-tuning and MLflow recovery tasks

Recovered from the current repository state on 2026-11-03. This list tracks the unfinished LLMOps work after the project refactor.

The notebook redesign, B3 recovery, MLflow/KFP/Vertex lineage and delivery checks are sequenced in [`notebook_mlflow_execution_plan.md`](notebook_mlflow_execution_plan.md). This checklist records status; the plan defines the work and acceptance criteria.

The controlled B3 inference campaign is specified in [`b3_rerun_execution_plan.md`](b3_rerun_execution_plan.md), including preflight gates, three split runs, output checks, MLflow lineage and notebook integration. It is a plan; no Vertex job has been submitted from this checkout.

**Order constraint:** approve and version the Routing Node decision/consequence policy first (`specs/004-routing-node/error-consequences.md`). B3 artifact inventory can proceed in parallel, but action-level error metrics and consequence-weighted reporting wait for that policy review.

## Done or already present

- [x] Masterclass handbook defines the use-case metric contract, operational confusion matrices, chart standards, metadata/tagging vocabulary, system ownership, and historical recovery boundaries (`docs/data_science_masterclass.md`).
- [x] MLflow tracking schema and local historical-import tooling exist (`src/tracking.py`, `scripts/import_legacy_results.py`). Prediction artifacts are sanitized to omit ticket text and reference labels.
- [x] Notebook helpers can load tracked evaluations and fall back to local prediction exports (`notebooks/_tracking.py`).
- [x] Figure export code reads MLflow evaluation runs and writes figures back as tracked artifacts (`scripts/build_tracking_figures.py`).
- [x] B3 `val` export is present at `data/runs/base_val_predictions.csv`; checked locally against `data/dataset/val.csv`: 293 rows, all ticket strings in the same order.
- [x] Notebook 2 now compares B2, B3, and D on validation with silent-error intervals, loading MLflow results before exact-split local fallbacks.
- [x] The MLflow figure builder now has a dedicated validation view for B2/B3/D, with separate silent-error and urgent wrong-desk panels.
- [x] The initial Router evaluation is derived from existing prediction exports in `src/router_evaluation.py`; `score_predictions.py --mlflow` logs namespaced Router counts/rates and its action matrix as an artifact. Notebook 5 displays the same diagnostic without changing the historical scorer.
- [x] The historical importer prepares v2 MLflow evaluation records with Router matrices and D train/eval loss histories by step. Notebook charts now display from their plotting cells with descriptive titles; field, trap-support and storage/RAM views were added as executable cells.

## Remaining work

1. **Validate the Router policy.** Complete T000–T000b in `specs/004-routing-node/tasks.md`, record owner decisions/policy version, then implement the pure Routing Node contract before product-level metrics.
2. **Complete the masterclass diagnostics.** Router action matrix and missed-urgency counts are now in the reusable evaluation path. Add field-level confusion summaries and reference error buckets, check the notebook chart rendering, and keep invalid output, abstention and misroute distinct.
3. **Inspect Vertex for B3 artifacts.** Follow [`b3_vertex_recovery.md`](b3_vertex_recovery.md): inspect run lineage/outputs and checksums before any download. The current session could not access an authenticated Vertex console or GCP CLI, so cloud availability remains unknown. The user has authorized conditional B3 inference reruns if Vertex lacks verified artifacts; training is not needed. Re-run only missing splits after recording the job inputs, GPU cost boundary, provenance capture, and teardown check.
4. **Implement the metadata contract end to end.** Structured D loss metrics and versioned evaluation imports are coded but not executed here. Add a model-card manifest and validation, complete KFP/Vertex resource cross-links, and audit the Registry version/alias labels against the local receipt. Make historical unknown values explicit; don't fabricate missing history.
5. **Import B3 on validation into MLflow.** Start the local MLflow server, run `scripts/import_legacy_results.py --dry-run --include-b3 --system-id B3 --split val`, inspect the reported row, then import with `--include-b3 --system-id B3 --split val`. This avoids rescoring the already-read test sets. Confirm the MLflow artifact contains hashed row IDs and model outputs only.
6. **Refresh the notebook narrative and charts.** Use MLflow-backed results after import, add B3 only where a matching split result exists, and show denominators and uncertainty consistently. Keep trap families diagnostic, label infrastructure costs as estimates, and preserve the G7 reading unless valid historical B3 test exports are recovered.
7. **Refresh and review generated figures.** Run `scripts/build_tracking_figures.py` against the populated local experiment, inspect SVG/PNG output, and confirm source run IDs are logged with each figure.

## Completion check

- B0–B3 and D variants with available validated results are visible in MLflow and the appropriate notebook comparisons.
- Every logged evaluation identifies its split hash, scorer/protocol version, model, origin, and prediction artifact hash; no ticket text or labels are logged.
- Figures can be rebuilt from MLflow and identify their source runs. The notebook distinguishes measured values from cost assumptions and never treats missing B3 test runs as zero or as a pass.
- No billed Vertex action occurs until read-only inventory establishes the missing outputs, a targeted plan captures provenance/cost/teardown, and only the missing inference is rerun.
