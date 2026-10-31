# finetuned_llm_classifier

Sub-project of NAVY (Keelpay payments copilot), built for the Agentic LLMOps course. It fine-tunes a small LLM on Vertex AI to turn a raw merchant ticket into a strict JSON, the first step of the copilot flow. See `initial_brief.md` for the task and examples.

It is an isolated uv project (own `pyproject.toml`, Python 3.11.6, `uv.lock`, `.venv`): the heavy ML dependencies stay out of the NAVY root environment. The folder layout follows the course practice sessions.

## Contract with the rest of NAVY

The only interface is the JSON schema below; NAVY never imports this code and calls the deployed endpoint.

Keys: `intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`. Ambiguous text fields are `"UNDEFINED"`, absent optional fields are `null`. Routing of `UNDEFINED` to a human agent is product logic and lives outside this folder.

## Setup

```bash
cd finetuned_llm_classifier
uv sync
cp .env.example .env   # fill in GCP_PROJECT_ID, GCP_REGION, GCP_BUCKET_NAME
```

## Layout

```
src/
  constants.py             # settings from environment variables
  schema.py                # JSON output contract
  handler.py               # Vertex AI EndpointHandler
  app/main.py              # Chainlit app
  pipeline_components/     # KFP components
  pipelines/               # KFP pipeline
scripts/                   # GCP check, pipeline runner
notebooks/                 # local experiments
data/                      # datasets (gitignored)
```
