# LLM fine-tuning and MLflow recovery tasks

Recovered from the current repository state on 2026-11-03. This list tracks the unfinished LLMOps work after the project refactor.

**Order constraint:** approve and version the Routing Node decision/consequence policy first (`specs/004-routing-node/error-consequences.md`). Action-level error metrics and consequence-weighted reporting wait for that policy review.

## Done or already present

- [x] Masterclass handbook defines the use-case metric contract, operational confusion matrices, chart standards, metadata/tagging vocabulary, system ownership, and historical recovery boundaries (`docs/data_science_masterclass.md`).
- [x] MLflow tracking schema and local historical-import tooling exist (`ml/qualifier/src/tracking.py`, `ml/qualifier/scripts/import_legacy_results.py`). Prediction artifacts are sanitized to omit ticket text and reference labels.
- [x] Notebook helpers can load tracked evaluations and fall back to local prediction exports (`ml/qualifier/notebooks/_tracking.py`).
- [x] B3 `val` export is present at `data/runs/base_val_predictions.csv`; checked locally against `data/dataset/val.csv`: 293 rows, all ticket strings in the same order.
- [x] Notebook 2 now compares B2, B3, and D on validation with silent-error intervals, loading MLflow results before exact-split local fallbacks.
- [x] The initial Router evaluation is derived from existing prediction exports in `ml/qualifier/src/router_evaluation.py`; `score_predictions.py --mlflow` logs namespaced Router counts/rates and its action matrix as an artifact. Notebook 5 displays the same diagnostic without changing the historical scorer.
- [x] The historical importer prepares v2 MLflow evaluation records with Router matrices and D train/eval loss histories by step. Notebook charts now display from their plotting cells with descriptive titles; field, trap-support and storage/RAM views were added as executable cells.
- [x] B3 test inference ran on Vertex for `test_natural` and `test_traps`; predictions are in `data/runs/base_test_*_predictions.csv`, row-order validated, with provenance in `data/runs/b3-2026-11-04-a_manifest.json`.
- [x] All historical evaluations, B3 on val and both test splits included, are imported into the local MLflow experiment (`ml/qualifier/scripts/import_legacy_results.py --include-b3`).
- [x] Notebooks show the contract, prompts, example tickets and training settings; every system (B0-B3, D variants) is compared on every split with one chart theme.

## Remaining work

1. **Validate the Router policy.** Complete T000–T000b in `specs/004-routing-node/tasks.md`, record owner decisions/policy version, then implement the pure Routing Node contract before product-level metrics.
2. **Complete the masterclass diagnostics.** Router action matrix and missed-urgency counts are now in the reusable evaluation path. Add field-level confusion summaries and reference error buckets, check the notebook chart rendering, and keep invalid output, abstention and misroute distinct.
3. **Implement the metadata contract end to end.** Structured D loss metrics and versioned evaluation imports are coded but not executed here. Add a model-card manifest and validation, complete KFP/Vertex resource cross-links, and audit the Registry version/alias labels against the local receipt. Make historical unknown values explicit; don't fabricate missing history.

## Completion check

- B0–B3 and D variants with available validated results are visible in MLflow and the appropriate notebook comparisons.
- Every logged evaluation identifies its split hash, scorer/protocol version, model, origin, and prediction artifact hash; no ticket text or labels are logged.
- Figures are rebuilt by executing the notebooks; they distinguish measured values from cost assumptions.
