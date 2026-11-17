# Serving the D-q4 Qualifier on Vertex AI

Only the Qualifier is deployed. The API and the front end run locally and call the endpoint.

## What is deployed

| Resource | Value |
| --- | --- |
| Project / region | `agentics-workflows-2` (number `158407666882`) / `europe-west2` |
| Registry model | `navy-team-keelpay-router-json` (ID `7308774847222382592`) |
| Version 1 | Hugging Face LoRA artifact (training run `…20261101161625`), alias `qwen3b-lora-q4`. Never served. |
| Version 2 | First GGUF attempt. Broken: the bundled llama-cpp-python wheel links musl. No alias. |
| **Version 3** | **D-q4 GGUF**, aliases `d-q4-gguf`, `champion`, `default` |
| Endpoint | `navy-team-keelpay-router` (ID `7728645352521203712`), kept empty between demos |

Version 3 provenance (also in its Registry description): compact run
`keelpay-router-compact-variants-pipeline-20261102155447`, ML Metadata artifact `13644223326725605447`,
adapter from training run `keelpay-router-training-pipeline-20261101173631`, GGUF MD5
`b23b4f3092c9083c1c741551ec351dc8`. Both compact runs produced the same file (same size and MD5).

## How it is served

The project has no Artifact Registry, so there is no custom image. Like every Registry model of the
course, the version uses Google's prebuilt Hugging Face inference image with a custom
`handler.py` ([`ml/qualifier/src/dq4_handler.py`](../ml/qualifier/src/dq4_handler.py)). The
Registry artifact directory holds three files:

- `handler.py`: loads the GGUF with llama-cpp-python, greedy decoding, same prompt and token budget as
  the evaluation;
- `llama_cpp_python-0.3.16-cp311-cp311-linux_x86_64.whl`: the evaluated version, built for glibc by
  the pipeline (the published Linux wheels link musl and do not load in the Ubuntu image);
- `model-q4.gguf`: copied server side from the compact run, checksum verified after the copy.

The handler checks the GGUF MD5 at start-up. Request and response:

```json
{"instances": [{"prompt": "<instruction>\n\nTicket:\n<ticket text>"}], "parameters": {"max_tokens": 160}}
{"predictions": [{"response": "<JSON label>"}]}
```

Checks done: the handler returns exactly the evaluation output on 20/20 `test_natural` tickets
locally and on 3/3 through the endpoint. Latency on `n1-standard-4`: about 2 min for the first
call after deployment, then 13-18 s per ticket.

## Commands

All three are Kubeflow pipelines submitted by
[`ml/qualifier/scripts/dq4_registry_pipeline.py`](../ml/qualifier/scripts/dq4_registry_pipeline.py),
run from this directory. `compile` builds the templates locally without contacting GCP.

**Register a new version** (builds the wheel, copies the GGUF, moves the aliases; a few cents):

```powershell
$gguf = "gs://navy-team-llmops-bucket/pipeline_root/158407666882/keelpay-router-compact-variants-pipeline-20261102155447/compact-variants-component_-2725338443608489984/gguf_q4"
uv run --group ml python ml/qualifier/scripts/dq4_registry_pipeline.py register `
  --gguf-artifact-uri $gguf --gguf-file-uri "$gguf/model-q4.gguf" `
  --expected-md5-hex b23b4f3092c9083c1c741551ec351dc8 `
  --source-pipeline-run keelpay-router-compact-variants-pipeline-20261102155447 `
  --source-artifact-id 13644223326725605447 `
  --source-adapter-uri gs://navy-team-llmops-bucket/pipeline_root/158407666882/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_-8515982401988460544/model `
  --serving-dir-uri gs://navy-team-llmops-bucket/registry/keelpay-router-json/<new-version-dir> `
  --parent-model projects/158407666882/locations/europe-west2/models/7308774847222382592 `
  --confirm-billable-run
```

**Deploy** (billed per hour until undeployed; 15-20 min):

```powershell
$env:GCP_PROJECT_NUMBER = "158407666882"
uv run --group ml python ml/qualifier/scripts/dq4_registry_pipeline.py deploy `
  --model-versioned-resource-name projects/158407666882/locations/europe-west2/models/7308774847222382592@3 `
  --endpoint-resource-name projects/158407666882/locations/europe-west2/endpoints/7728645352521203712 `
  --machine-type n1-standard-4 --confirm-billable-run --confirm-billable-deploy
```

**Undeploy after every session** (keeps the empty endpoint, which costs nothing):

```powershell
uv run --group ml python ml/qualifier/scripts/dq4_registry_pipeline.py undeploy `
  --endpoint-resource-name projects/158407666882/locations/europe-west2/endpoints/7728645352521203712 `
  --expected-model-versioned-resource-name projects/158407666882/locations/europe-west2/models/7308774847222382592@3 `
  --confirm-billable-run
```

The pipelines refuse a non-empty or shared endpoint, an unversioned model name and an unexpected
version. The project is shared with other teams: never touch their models or endpoints.

## Use it from the local API

```powershell
$env:NAVY_QUALIFIER_PROVIDER = "vertex_raw_predict"
$env:NAVY_QUALIFIER_VERTEX_ENDPOINT_ID = "7728645352521203712"
$env:GCP_PROJECT_ID = "agentics-workflows-2"
.\run-local.ps1 -SkipQualifier
```

The call uses the presenter's Google credentials (`gcloud auth application-default login`).
