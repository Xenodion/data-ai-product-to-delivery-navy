# MLflow and Vertex AI runbook

This project uses Kubeflow Pipelines on Vertex AI to execute training and inference, MLflow Tracking to compare experiment runs and retain their provenance, and Vertex AI Model Registry as the deployment registry. MLflow is not yet a shared hosted service; local development uses a localhost tracking server. DVC is deferred while the synthetic dataset remains small and Git-managed. The current subproject directory is `agentic-workflow-subproject/` (older notes may call it `finetuned_llm_classifier/`).

## Local setup

The subproject dependency list includes MLflow. Regenerate the lock with the project's Python 3.11 environment, then sync dependencies: `uv lock --python 3.11` followed by `uv sync`.

```powershell
cd agentic-workflow-subproject
Copy-Item .env.example .env  # set only the local values needed for your task
uv sync
uv run mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlartifacts --host 127.0.0.1 --port 5000
```

Open `http://127.0.0.1:5000`. Stop the local process with Ctrl+C. The local database and artifact directory are ignored by Git. This store is per-machine and is not the team's shared system of record. Before using a shared MLflow server, decide the backend database, artifact storage, access control, backup, and retention.

The tracking helpers default to `MLFLOW_TRACKING_URI=http://127.0.0.1:5000` and experiment `navy-qualifier`; set these in the local `.env` to override them. Do not put credentials in tracked files or upload `.env`.

## Track local baseline runs

```powershell
uv run python scripts/run_baselines.py --mlflow
```

This scores `val` and logs B0–B2 results and privacy-filtered prediction artifacts (row hash and model output, without ticket text or reference labels) to MLflow. Adding `--final` explicitly evaluates and tracks the final test sets; do not use it while tuning.

To score a prediction export such as a recovered B3 CSV:

```powershell
uv run python scripts/score_predictions.py path\to\predictions.csv val --mlflow --system-id B3 --model-id Qwen/Qwen2.5-3B-Instruct --tracking-origin historical_import
```

The scorer checks that ticket text and row order match the selected committed split; logged artifacts keep only row hashes and model outputs. It reports a failure rather than importing mismatched predictions.

## Import existing local results

First validate which local files match each committed split without contacting MLflow:

```powershell
uv run python scripts/import_legacy_results.py --dry-run
uv run python scripts/import_legacy_results.py --dry-run --include-b3 --system-id B3 --split val
```

When the B3 prediction export is local and passes the exact split checks, import existing results:

```powershell
uv run python scripts/import_legacy_results.py --include-b3 --system-id B3 --split val
```

This command never queries Vertex or GCS. It imports locally available B0–B3, D, D-q8, and D-q4 prediction results, creates `docs/results/dataset_manifest.json`, records timing artifacts and explicitly marks cost assumptions as estimates. Missing or invalid files are skipped and reported. Use the local B3 export only after its cloud job/split provenance has been verified; do not rerun the pipeline to fill missing metadata.

The v2 evaluation record additionally logs initial Router counts/rates under `router.*`, a five-action matrix artifact and, for D/val, the preserved train/eval loss at its original optimizer steps. These are historical imports with explicit source files, not retroactive claims that the original Vertex job streamed into MLflow. The v2 key creates a new immutable evaluation run; existing v1 runs are left intact.

## Synchronize an already completed Vertex pipeline

`scripts/sync_vertex_run.py` accepts a local JSON export manifest and local artifact paths. It does not query Vertex or download GCS objects. Any remote lookup/download must first pass the project's cost and access approval.

Minimal manifest shape:

```json
{
  "schema_version": 1,
  "vertex": {
    "project": "project-id",
    "region": "europe-west2",
    "pipeline_job_resource": "projects/.../locations/.../pipelineJobs/...",
    "pipeline_name": "training",
    "display_name": "router-training-...",
    "pipeline_template_version": "sha256:..."
  },
  "experiment_name": "navy-qualifier",
  "parameters": {"model_id": "Qwen/Qwen2.5-3B-Instruct"},
  "results": [
    {
      "task_name": "inference-component",
      "system_id": "B3",
      "run_type": "inference",
      "split": "test_natural",
      "tags": {"dataset_revision": "sha256:...", "tracking_origin": "historical_import"},
      "params": {"precision": "float16", "seed": "42"},
      "metrics": {"silent_error_rate": 0.01, "urgent_wrong_desk": 0.02},
      "metric_evidence": {"silent_error_rate": {"status": "measured", "source": "score report"}},
      "artifacts": [{"path": "predictions.csv", "artifact_path": "predictions"}]
    }
  ]
}
```

Paths in the manifest are resolved relative to the manifest file. Results are grouped under an MLflow parent run for the Vertex job. The sync key includes job resource, task, system, split, and run type. Repeating an identical manifest is a no-op; changed data under the same key is rejected rather than appended as duplicate metric history.

```powershell
uv run python scripts/sync_vertex_run.py path\to\vertex-export.json
```

The script logs local files to MLflow; for large files already in GCS, use approved local retrieval or extend the manifest/artifact strategy to immutable cloud references before syncing. It does not create, list, or download cloud resources.

## Link a Vertex registered model

After a model has been registered through the approved Vertex workflow, record its immutable resource/version and alias snapshot against the source MLflow run:

```powershell
uv run python scripts/link_vertex_model.py `
  --run-id <mlflow-run-id> `
  --system-id D-q4 `
  --model-resource projects/<project>/locations/europe-west2/models/<model-id>@<version> `
  --alias qwen3b-lora-q4 `
  --artifact-uri gs://<bucket>/<immutable-model-path> `
  --artifact-sha256 <sha256>
```

The command writes a lineage event to MLflow and an ignored local receipt. It does not call Vertex, register a model, move an alias, or change a deployment. A changed alias/version is a new event.
The resource argument must contain an immutable model version. The receipt also copies the source run's dataset/scorer/prediction hashes and Vertex pipeline job reference when known; `unknown` is retained when historical provenance cannot be recovered. A local link is only one side of synchronization: inspect the Vertex model version/labels and KFP execution lineage separately before declaring the crosswalk verified.

## Rebuild slide figures

Once legacy runs or later pipeline results are present in the configured MLflow experiment:

```powershell
uv run python scripts/build_tracking_figures.py
```

It writes SVG and PNG charts to `docs/figures/` and logs the exports with their source run IDs. Available views include quality versus monthly inference cost, silent and urgent error rates, quality versus measured latency, trap-family severity, and training loss when the training history artifact is present. A chart is omitted if the required source metrics are unavailable; test-trap results remain diagnostic and do not become headline quality.

## Recovery and safeguards

- If MLflow is unavailable, keep the Vertex job artifacts intact and retry synchronization later. Do not rerun a completed job just to recreate tracking metadata. If read-only B3 inventory proves a required inference output is absent, the authorized recovery plan is a new, versioned B3 inference job on only the missing split(s), with cost, provenance, and teardown captured; no training run is needed.
- If a tracking key already exists with a different payload, do not edit the old result. Identify the provenance change and use an explicit new version/key.
- Store only synthetic ticket exports under the current data policy. MLflow prediction artifacts omit ticket text and reference labels; tags and parameters contain bounded identifiers and short metadata.
- Record measured and estimated values separately. The monthly CPU/GPU costs in this project are estimates under scenario assumptions, not the billing export.
- Vertex training, inference, conversion, GCS retrieval, hosted MLflow infrastructure, IAM changes, and endpoint deployment can incur charges or modify shared state. The scripts above that submit jobs are not part of this local tracking quickstart.
