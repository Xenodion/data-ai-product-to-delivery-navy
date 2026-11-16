"""Upload and deploy the GGUF D-q4 llama.cpp serving image on a Vertex endpoint.

Image builds and model registration do not allocate inference nodes. The deploy
command is explicitly gated because Vertex online prediction bills deployed
replicas while they are ready, including when idle.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def _context(parser: argparse.ArgumentParser, args: argparse.Namespace):
    from google.cloud import aiplatform

    project = args.project or os.environ.get("GCP_PROJECT_ID")
    region = args.region or os.environ.get("GCP_REGION", "europe-west2")
    if not project:
        parser.error("Pass --project or set GCP_PROJECT_ID in .env")
    aiplatform.init(project=project, location=region)
    return aiplatform, project, region


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="GCP project; defaults to GCP_PROJECT_ID")
    parser.add_argument("--region", help="Vertex region; defaults to GCP_REGION or europe-west2")
    commands = parser.add_subparsers(dest="command", required=True)

    upload = commands.add_parser("upload", help="register the Vertex custom-container model")
    upload.add_argument("--image-uri", required=True, help="Artifact Registry URI built from vertex_build/")
    upload.add_argument("--display-name", default="keelpay-router-dq4-gguf")

    deploy = commands.add_parser("deploy", help="deploy one replica to an endpoint")
    deploy.add_argument("--model-resource", required=True, help="full Vertex Model resource name")
    deploy.add_argument("--machine-type", required=True, help="Vertex-supported CPU machine type")
    deploy.add_argument("--endpoint-id", help="reuse an empty endpoint; otherwise create one")
    deploy.add_argument("--endpoint-display-name", default="keelpay-router-dq4")
    deploy.add_argument("--confirm-billable-deploy", action="store_true")

    stop = commands.add_parser("undeploy", help="remove the model and release its inference nodes")
    stop.add_argument("--endpoint-id", required=True)

    args = parser.parse_args()
    aiplatform, project, region = _context(parser, args)

    if args.command == "upload":
        model = aiplatform.Model.upload(
            display_name=args.display_name,
            serving_container_image_uri=args.image_uri,
            serving_container_args=[
                "--model", "/models/model-q4.gguf",
                "--ctx-size", "2048",
                "--parallel", "1",
                "--host", "0.0.0.0",
                "--port", "8080",
            ],
            serving_container_ports=[8080],
            serving_container_health_route="/health",
            serving_container_predict_route="/v1/chat/completions",
            description="D-q4 GGUF Qualifier served by the pinned llama.cpp CPU container.",
            sync=True,
        )
        print(f"Vertex model: {model.resource_name}")
        return

    if args.command == "deploy":
        if not args.confirm_billable_deploy:
            parser.error("Deployment allocates billable nodes; pass --confirm-billable-deploy after reviewing cost")
        model = aiplatform.Model(args.model_resource, project=project, location=region)
        endpoint = (
            aiplatform.Endpoint(args.endpoint_id, project=project, location=region)
            if args.endpoint_id
            else aiplatform.Endpoint.create(
                display_name=args.endpoint_display_name,
                project=project,
                location=region,
                labels={"app": "navy", "model": "dq4-gguf"},
                sync=True,
            )
        )
        if endpoint.gca_resource.deployed_models:
            parser.error("Endpoint is not empty; choose an empty endpoint to avoid changing existing traffic")
        endpoint.deploy(
            model,
            machine_type=args.machine_type,
            min_replica_count=1,
            max_replica_count=1,
            traffic_percentage=100,
            sync=True,
        )
        deployed = endpoint.gca_resource.deployed_models[-1]
        print(f"Endpoint resource: {endpoint.resource_name}")
        print(f"Deployed model ID: {deployed.id}")
        print("Stop billing with the undeploy command shown in docs/vertex_dq4_endpoint.md.")
        return

    endpoint = aiplatform.Endpoint(args.endpoint_id, project=project, location=region)
    deployed_models = list(endpoint.gca_resource.deployed_models)
    if not deployed_models:
        print("Endpoint already has no deployed models.")
        return
    if len(deployed_models) != 1:
        parser.error("Refusing to stop an endpoint with multiple deployed models")
    endpoint.undeploy(deployed_model_id=deployed_models[0].id, sync=True)
    print(f"Undeployed model {deployed_models[0].id}; endpoint resource remains available for redeployment.")


if __name__ == "__main__":
    main()
