# Serve D-q4 through a Vertex AI endpoint

The application model remains the evaluated D-q4 GGUF artifact. Vertex serves the pinned `llama.cpp` server image as a custom container. The flow calls Vertex `rawPredict` with the OpenAI-compatible chat-completions body, and Vertex forwards that body to `/v1/chat/completions`.

## Build the serving image remotely

The 1.93 GB model is already in GCS. Cloud Build copies it into a small, dedicated build context, checks the pinned MD5, and pushes the image to Artifact Registry. This avoids building the image or uploading the model from the demo PC.

From `agentic-workflow-subproject`, after authenticating the Google Cloud CLI and confirming the project and region:

```powershell
$project = $env:GCP_PROJECT_ID
$region = $env:GCP_REGION
$image = "$region-docker.pkg.dev/$project/navy-serving/qualifier-dq4:b5974"

gcloud artifacts repositories create navy-serving `
  --repository-format=docker --location=$region --project=$project

gcloud builds submit flow/deploy/vertex_build `
  --config=flow/deploy/vertex_build/cloudbuild.yaml `
  --substitutions="_IMAGE=$image,_MODEL_URI=gs://navy-team-llmops-bucket/pipeline_root/158407666882/keelpay-router-compact-variants-pipeline-20261102155447/compact-variants-component_-2725338443608489984/gguf_q4/model-q4.gguf" `
  --project=$project --region=$region
```

If the Artifact Registry repository already exists, skip its creation. The Cloud Build service account needs read access to the model object and write access to the `navy-serving` repository. Building and storing the image may incur Cloud Build and Artifact Registry charges, separate from endpoint inference-node charges.

## Register the custom serving model

```powershell
uv run --group ml python ml/qualifier/scripts/deploy_dq4_vertex.py `
  --project $env:GCP_PROJECT_ID --region $env:GCP_REGION `
  upload --image-uri $image
```

The model is registered with port `8080`, health route `/health` and predict route `/v1/chat/completions`. The application uses Vertex `rawPredict`, which supports arbitrary request bodies; the server response remains the standard OpenAI chat-completion JSON.

## Deploy and stop

First choose a Vertex-supported CPU machine type with enough memory for the 1.93 GB model plus its context/KV cache. The deployment command requires an explicit machine type and an explicit billing acknowledgement. It pins minimum and maximum replicas to one.

```powershell
uv run --group ml python ml/qualifier/scripts/deploy_dq4_vertex.py `
  --project $env:GCP_PROJECT_ID --region $env:GCP_REGION `
  deploy --model-resource <MODEL_RESOURCE> --machine-type <MACHINE_TYPE> `
  --confirm-billable-deploy
```

Copy the endpoint ID printed by the command into the backend environment:

```text
NAVY_QUALIFIER_PROVIDER=vertex_raw_predict
NAVY_QUALIFIER_VERTEX_ENDPOINT_ID=<ENDPOINT_ID>
NAVY_QUALIFIER_VERTEX_PROJECT_ID=<PROJECT_ID>
NAVY_QUALIFIER_VERTEX_REGION=europe-west2
```

To turn inference off while retaining the empty endpoint for later redeployment:

```powershell
uv run --group ml python ml/qualifier/scripts/deploy_dq4_vertex.py `
  --project $env:GCP_PROJECT_ID --region $env:GCP_REGION `
  undeploy --endpoint-id <ENDPOINT_ID>
```

Vertex charges for deployed inference nodes while they are ready, including idle time. Undeploy the model immediately after a short test/demo; endpoint deletion is optional after all models are undeployed. See [Google's endpoint cleanup instructions](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/predictions/undeploy-model?hl=en).
