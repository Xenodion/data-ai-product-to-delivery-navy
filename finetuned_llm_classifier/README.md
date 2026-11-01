# finetuned_llm_classifier

**This is the sub-project of the course "Agentic Workflows & LLM Ops" (Albert School, M2).** The course asks for an end-to-end LLMOps flow on a text-generation use case of the team's own design: fine-tune a small open-source model with LoRA on Vertex AI, run it through a KFP pipeline, evaluate it, deploy it to an endpoint and put a small web app in front of it. The course is shared with "Data & AI Product: From Diagnosis to Delivery", whose project is the NAVY / Keelpay copilot described in the root `README.md`.

Our use case: turn a raw merchant ticket (French or English) into a strict JSON, the first step of the copilot flow. The task, the closed values and four examples are in `initial_brief.md`. The code follows the course practice sessions and is adapted from the team's own working solution of those sessions (`Agentic-LLMOps`), changing the task from "translate to Yoda" to "read a ticket and return JSON".

It is an isolated uv project (own `pyproject.toml`, Python 3.11.6, `uv.lock`, `.venv`): the heavy ML dependencies stay out of the NAVY root environment.

## Contract with the rest of NAVY

The only interface is the JSON schema below; NAVY never imports this code and calls the deployed endpoint.

Keys: `intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`. All values are strings: `"UNDEFINED"` when a field cannot be determined, `"OTHER"` when the request is understood but fits no listed class, `""` when `transaction_id`, `amount` or `currency` is absent. Contract in `src/dataset_build/schema.py`, definitions in `docs/label_definitions.md`. Routing of `UNDEFINED` to a support agent is product logic and lives outside this folder.

## Status

| Part | State |
|---|---|
| GCP check, pipeline runner, constants | copied from the reference solution |
| Data transformation, fine-tuning, inference components | adapted to the ticket task (JSON target, 512-token sequences, JSON validity check) |
| Training and hyperparameter-sweep pipelines | adapted; both compile |
| Handler (Vertex AI custom endpoint) | adapted |
| Synthetic dataset (`data/dataset/`), scoring (`src/scoring.py`) and baselines B0-B2 | done, see `docs/scoring_protocol.md` |
| Base model (B3) pipeline and prediction scoring (`scripts/score_predictions.py`) | written, not run on Vertex yet |
| Training on Vertex with Qwen2.5-3B-Instruct | not run yet |
| Evaluation component (field-level metrics) | to do |
| Model registration, endpoint, Chainlit app, notebooks | to do |
| Requirements specific to the shared project (automated evaluation harness in CI, monitoring, model routing, semantic caching, production-readiness checklist) | to define |

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
uv run python scripts/pipeline_runner.py training --smoke                  # calibration: 200 tickets, 40 steps, 20 predictions
uv run python scripts/pipeline_runner.py training                          # predicts on val
uv run python scripts/pipeline_runner.py training --test-file test_natural.csv   # final run, once
uv run python scripts/pipeline_runner.py sweep
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
  app/main.py              # Chainlit app (to do)
  pipeline_components/     # KFP components
  pipelines/               # training and sweep pipelines
scripts/                   # GCP check, dataset upload, pipeline runner, baselines, scoring of predictions, dataset build
notebooks/                 # local experiments
data/dataset/              # the four splits and their quarantine (committed on purpose); other data is gitignored
```
