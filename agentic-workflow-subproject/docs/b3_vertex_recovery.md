# B3 recovery from Vertex AI

## Current evidence

- Local prediction export: `data/runs/base_val_predictions.csv` (293 rows; exact ticket/order match to the committed `val.csv`).
- No B3 `test_natural` or `test_traps` prediction exports or Vertex job manifest/receipt are present in this checkout.
- The B3 pipeline writes an inference artifact and accepts `test_file`; its default is `val.csv`. The local runner's submission receipt is created after a run, but there are no receipts in the available checkout.
- B3 recovery is a **Vertex Pipelines / Vertex ML Metadata** search, not a Model Registry search. The registered `keelpay-router-json` entry is the selected D-q4 model; it does not establish where B3 inference outputs were retained.
- Vertex has **not yet been inspected** in this session: the authenticated browser bridge and GCP CLI are unavailable here. Absence from the local checkout is not evidence that Vertex/GCS artifacts are missing.

## Read-only Vertex inventory to perform first

In the Vertex AI Pipelines console, inspect the project and region configured for the subproject and filter the run list by `keelpay-router-base-model-pipeline` / display name `router-base-pipeline` and label `project=navy-qualifier`. For each matching run, record:

1. Full pipeline job resource name, display name, create/start/end times, state, project, and region.
2. Pipeline template/source digest if retained; parameters including dataset URI, `test_file`, `max_rows`, model ID, and prompt/instruction version.
3. Inference task state, input dataset artifact URI/digest, output prediction artifact URI, row count, model/container version, and logs containing generation settings.
4. Whether output artifacts exist for `val.csv`, `test_natural.csv`, and `test_traps.csv`; do not infer split from a filename alone.
5. Any model revision/resolved commit, tokenizer revision, task image digest, and exact job provenance available in Vertex ML Metadata.

Inspect the pipeline's artifact and execution lineage before downloading. If source objects exist, retrieve only the needed synthetic prediction CSVs and provenance receipt; record object generation/checksum. Do not download base model weights unless the review proves they are needed and separately budgets the transfer/storage impact.

## Recovery decision

| Vertex evidence | Action |
|---|---|
| Complete B3 exports exist and their split, model, prompt, and job provenance are verifiable | Download only required outputs under the approved project budget; run exact split/order validation; score once under the frozen protocol and record the Vertex job link in MLflow. |
| B3 test outputs exist but model revision/provenance is incomplete | Preserve the files as historical artifacts with the missing facts marked `unknown`; do not claim exact reproducibility. Decide whether a fresh, fully versioned inference is needed. |
| Only val output exists, or no valid test output exists | Re-run **B3 inference only**, not training, for each missing frozen test split. Keep the result as a new, fully versioned candidate and perform a single predeclared test evaluation; do not use it for tuning. |
| Vertex job exists but failed or has no output artifact | Record the failed historical run. If authorized, rerun only the missing B3 inference step on the affected split(s), with a fresh job ID and full provenance. |

The user's latest instruction authorizes conditional reruns if inspection shows the needed artifacts are unavailable. A rerun is a billed T4 inference job and must capture its new run resource, exact inputs, model/prompt versions, output checksums, and cost. It is **not a retraining run**. If the exact original model revision cannot be recovered, label the new output as a new B3 evaluation rather than claiming it reproduces the historical one.

## Capture and synchronize

For every recovered/new result, create a local export manifest following [`mlops_tracking.md`](mlops_tracking.md). Include separate result rows for `B3` and each split, full `pipeline_job_resource`, `inference-component` task name, model and prompt revision, dataset SHA-256, prediction artifact SHA-256, generation parameters, and measured runtime/cost evidence when available. Then use the offline `scripts/sync_vertex_run.py` flow to attach the manifest and artifacts to MLflow. This synchronization makes no Vertex/GCS calls.

Before reporting an action matrix or consequence-weighted result, complete policy review in [`../../specs/004-routing-node/error-consequences.md`](../../specs/004-routing-node/error-consequences.md). A valid B3 prediction export can be inventoried and preserved before then; product-level interpretation waits for the router policy.
