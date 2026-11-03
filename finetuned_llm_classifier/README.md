# finetuned_llm_classifier

**This is the sub-project of the course "Agentic Workflows & LLM Ops" (Albert School, M2).** The course asks for an end-to-end LLMOps flow on a text-generation use case of the team's own design: fine-tune a small open-source model with LoRA on Vertex AI, run it through a KFP pipeline, evaluate it, deploy it to an endpoint and put a small web app in front of it. The course is shared with "Data & AI Product: From Diagnosis to Delivery", whose project is the NAVY / Keelpay copilot described in the root `README.md`.

Our use case: turn a raw merchant ticket (French or English) into a strict JSON, the first step of the copilot flow. The task, the closed values and four examples are in `initial_brief.md`. The code follows the course practice sessions and is adapted from the team's own working solution of those sessions (`Agentic-LLMOps`), changing the task from "translate to Yoda" to "read a ticket and return JSON".

It is an isolated uv project (own `pyproject.toml`, Python 3.11.6, `uv.lock`, `.venv`): the heavy ML dependencies stay out of the NAVY root environment.

## Contract with the rest of NAVY

The only interface is the JSON schema below; NAVY never imports this code and calls the deployed endpoint.

Keys: `intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`. All values are strings: `"UNDEFINED"` when a field cannot be determined, `"OTHER"` when the request is understood but fits no listed class, `""` when `transaction_id`, `amount` or `currency` is absent. Contract in `src/dataset_build/schema.py`, definitions in `docs/label_definitions.md`. Routing of `UNDEFINED` to a support agent is product logic and lives outside this folder.

## Status (2026-11-01)

The plan, with its gates, is `docs/roadmap.md`; the day-by-day account is in `notebooks/`.

| Part | State |
|---|---|
| Dataset (`data/dataset/`: train 1922, val 293, test_natural 610, test_traps 380, plus quarantines) | done and frozen |
| Scoring (`src/scoring.py`) and baselines B0-B2 | done; test sets read once, results in `docs/baseline_results.md` |
| Pipelines on Vertex (training, base model, sweep) with Qwen2.5-3B-Instruct, float16 | training run done (2 h 06 of T4); base-model and sweep pipelines compile, not run |
| Model D (Qwen2.5-3B + LoRA) on val | cost 0.027 per ticket against 1.478 for B2; valid JSON 290 of 293; test sets not read yet (`docs/results/`) |
| Compact variants (merged GGUF, smaller models) | D-q4 locked on val (cost 0.020, 6.4 s CPU, 0 % urgent wrong desk, < 18 €/mo); S-1.5B/S-0.5B cancelled under explicit decision rule (`docs/compact_variants.md`) |
| Final reading of the test sets (Gate G7) | PASSED in `notebooks/05_final_evaluation.ipynb`. Champion D-q4 achieves 0.054 € error cost (-1.61 € vs B2, p < 0.0001) |
| Model registration in Vertex AI (Gate G8) | PASSED. Model registered: `keelpay-router-json` (ID: 7308774847222382592, alias: `qwen3b-lora-q4`, region europe-west2) |
| Requirements of the shared project (evaluation harness in CI, monitoring, routing, caching, production-readiness checklist) | to define |

## Documents

| File | What it is |
|---|---|
| `docs/roadmap.md` | gates G1-G9 and the rules that stay fixed |
| `docs/scoring_protocol.md` | frozen metrics, cost matrix, decision rule, dated amendments, systems and efficiency metric (confirmed) |
| `docs/methodology.md` | how we test, control cost and choose |
| `docs/label_definitions.md` | definition of each label |
| `docs/baseline_results.md` | B0-B2 on val and the test sets |
| `docs/compact_variants.md` | procedure and val results for merged GGUF models (D-q8, D-q4) and smaller models |
| `docs/results/` | predictions and loss history of full run D, D-q8, D-q4 and timings |
| `notebooks/01_dataset_build.ipynb`, `02_scoring_and_baselines.ipynb`, `03_finetuning_vertex.ipynb`, `04_compact_variants.ipynb`, `05_final_evaluation.ipynb` | the logbook, in the order of discovery (G1 to G8 complete) |

## Setup

```bash
cd finetuned_llm_classifier
uv sync
cp .env.example .env   # fill in GCP_PROJECT_ID, GCP_REGION, GCP_BUCKET_NAME (never commit .env)
uv run python scripts/validate_gcp_setup.py
```

The four splits of the dataset build (`data/dataset/{train,val,test_natural,test_traps}.csv`, committed for the exercise) are expected at `gs://<bucket>/dataset/`; each has a `ticket` column and a `target` column (the expected JSON as a string).

```bash
uv run python scripts/upload_dataset.py
uv run python scripts/pipeline_runner.py training --fp16 --smoke           # calibration: 200 tickets, 40 steps, 20 predictions
uv run python scripts/pipeline_runner.py training --fp16                   # full run, predicts on val (about 2 h 06 of T4 for the 3B model)
uv run python scripts/pipeline_runner.py base                              # the base model alone (system B3)
uv run python scripts/pipeline_runner.py training --fp16 --model-id Qwen/Qwen2.5-1.5B-Instruct   # smaller model
uv run python scripts/pipeline_runner.py sweep                             # 7 chained trainings: only after a single run was checked

# then, locally: download the predictions CSV of the inference step and score it
uv run --with scikit-learn python scripts/score_predictions.py <predictions.csv> val
```

## Training settings

Starting point of the course (3 epochs, LoRA r=8 alpha=16 dropout 0.05, learning rate 3e-4, 4-bit base model), with three changes for our data: sequences of 1024 tokens (our chats have a median of 495 and a p99 of 813, so 512 cut the JSON answer off 41 % of the tickets), no packing, and a loss on the assistant answer only. The best checkpoint on validation loss is kept; `log_history.json` in the model artifact holds the loss curve. Run the `--smoke` pipeline first (time and memory per step, loss going down, valid JSON), then one full run, then read the curve before any sweep.

## Cost and teardown: be vigilant

Vertex AI is billed to the school's credits. Two very different cases:

- **Pipeline jobs (training, sweep, base model, inference)** are ephemeral: the GPU machine exists for the task and is released when it ends, whether it succeeds or fails. Still, after every run, check in the Vertex AI console (Pipelines, then Training jobs) that nothing stays `RUNNING` or `PENDING`, and stop a task that looks stuck. The sweep chains 7 trainings: do not start it before a single run has been checked.
- **An endpoint is never ephemeral.** It bills per node and per hour, there is **no scale to zero**, and it keeps billing while idle. As soon as the tests are done: undeploy the model, then delete the endpoint (console, Online prediction, Endpoints), and check that the list is empty. Keep `min_replica_count=1` and `max_replica_count=1`. Never leave an endpoint over a night or a weekend.

Before any billed command: say whether it is local (free) or on GCP (billed) and what will stop it.

## Layout

```
src/
  constants.py             # settings from environment variables
  prompt.py                # the instruction shared by training, inference and serving
  dataset_build/           # synthetic dataset: JSON output contract (schema.py), cards, generation, review, export
  scoring.py, baselines.py # metrics and baselines B0-B2 of docs/scoring_protocol.md
  handler.py               # Vertex AI EndpointHandler
  app/main.py              # Chainlit app (to do, conditional)
  pipeline_components/     # KFP components
  pipelines/               # training and sweep pipelines
scripts/                   # GCP check, dataset upload, pipeline runner, baselines, scoring of predictions, dataset build
notebooks/                 # the logbook (5 notebooks: G1 to G8 complete)
docs/                      # protocol, roadmap, methodology, results (see the table above)
data/dataset/              # the four splits and their quarantine (committed on purpose); other data is gitignored
```
