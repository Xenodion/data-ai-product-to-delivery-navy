# finetuned_llm_classifier

**This is the sub-project of the course "Agentic Workflows & LLM Ops" (Albert School, M2).** The course asks for an end-to-end LLMOps flow on a text-generation use case of the team's own design: fine-tune a small open-source model with LoRA on Vertex AI, run it through a KFP pipeline, evaluate it, deploy it to an endpoint and put a small web app in front of it. The course is shared with "Data & AI Product: From Diagnosis to Delivery", whose project is the NAVY / Keelpay copilot described in the root `README.md`.

Our use case: turn a raw merchant ticket (French or English) into a strict JSON, the first step of the copilot flow. The task, the closed values and four examples are in `initial_brief.md`. The code follows the course practice sessions and is adapted from the team's own working solution of those sessions (`Agentic-LLMOps`), changing the task from "translate to Yoda" to "read a ticket and return JSON".

It is an isolated uv project (own `pyproject.toml`, Python 3.11.6, `uv.lock`, `.venv`): the heavy ML dependencies stay out of the NAVY root environment.

## Contract with the rest of NAVY

The only interface is the JSON schema below; NAVY never imports this code and calls the deployed endpoint.

Keys: `intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`. Ambiguous text fields are `"UNDEFINED"`, absent optional fields are `null`. Routing of `UNDEFINED` to a support agent is product logic and lives outside this folder.

## Status

| Part | State |
|---|---|
| GCP check, pipeline runner, constants | copied from the reference solution |
| Data transformation, fine-tuning, inference components | adapted to the ticket task (JSON target, 512-token sequences, JSON validity check) |
| Training and hyperparameter-sweep pipelines | adapted; both compile |
| Handler (Vertex AI custom endpoint) | adapted |
| Synthetic dataset and gold test set | to do |
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

The raw dataset is expected at `gs://<bucket>/tickets_synthetic.csv` with two columns: `ticket` (the message) and `target` (the expected JSON as a string).

```bash
uv run python scripts/pipeline_runner.py training   # or: sweep
```

## Layout

```
src/
  constants.py             # settings from environment variables
  prompt.py                # the instruction shared by training, inference and serving
  schema.py                # JSON output contract (to do)
  handler.py               # Vertex AI EndpointHandler
  app/main.py              # Chainlit app (to do)
  pipeline_components/     # KFP components
  pipelines/               # training and sweep pipelines
scripts/                   # GCP check, pipeline runner
notebooks/                 # local experiments
data/                      # datasets (gitignored)
```
