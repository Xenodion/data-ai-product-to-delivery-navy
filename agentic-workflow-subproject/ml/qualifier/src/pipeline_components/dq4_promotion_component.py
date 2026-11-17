"""KFP components for promoting a verified historical D-q4 GGUF to Vertex."""

from kfp.dsl import Artifact, Input, Model, Output, OutputPath, component


@component(base_image="python:3.11-bullseye", packages_to_install=["google-cloud-storage==3.17.1"])
def build_llama_cpp_wheel(serving_dir_uri: str) -> None:
    """Build llama-cpp-python 0.3.16 (the evaluated version) for glibc and store it in the serving dir.

    The published Linux wheels link musl and cannot load in the Ubuntu serving image. Debian bullseye
    (glibc 2.31) builds a wheel that runs on Ubuntu 22.04; GGML_NATIVE=OFF keeps portable CPU flags.
    """
    import os
    import subprocess
    import sys
    import zipfile
    from pathlib import Path

    from google.cloud import storage

    wheel_name = "llama_cpp_python-0.3.16-cp311-cp311-linux_x86_64.whl"
    out = Path("/tmp/wheelhouse")
    subprocess.run([sys.executable, "-m", "pip", "install", "cmake", "ninja"], check=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-cache-dir", "-w", str(out),
         "llama-cpp-python==0.3.16"],
        check=True,
        env={**os.environ, "CMAKE_ARGS": "-DGGML_NATIVE=OFF", "CMAKE_BUILD_PARALLEL_LEVEL": str(os.cpu_count())},
    )
    wheel = out / wheel_name
    with zipfile.ZipFile(wheel) as archive:
        if any(b"libc.musl" in archive.read(name) for name in archive.namelist() if ".so" in name):
            raise RuntimeError("built wheel links musl")
    bucket_name, _, prefix = serving_dir_uri.removeprefix("gs://").rstrip("/").partition("/")
    storage.Client().bucket(bucket_name).blob(f"{prefix}/{wheel_name}").upload_from_filename(str(wheel))
    print(f"Uploaded {wheel_name} to {serving_dir_uri}", flush=True)


@component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-storage==3.17.1"],
)
def verify_gguf_object(
    gguf_file_uri: str,
    expected_md5_hex: str,
    actual_md5_hex: OutputPath(str),
    object_generation: OutputPath(str),
) -> None:
    """Check the immutable GCS object metadata without downloading the GGUF."""
    import base64
    from urllib.parse import urlparse

    from google.cloud import storage

    parsed = urlparse(gguf_file_uri)
    if parsed.scheme != "gs" or not parsed.netloc or not parsed.path:
        raise ValueError("gguf_file_uri must be a gs:// bucket/object URI")
    try:
        if len(expected_md5_hex) != 32:
            raise ValueError
        bytes.fromhex(expected_md5_hex)
    except ValueError as exc:
        raise ValueError("expected_md5_hex must be 32 hexadecimal characters") from exc

    blob = storage.Client().bucket(parsed.netloc).blob(parsed.path.lstrip("/"))
    blob.reload()
    if not blob.md5_hash:
        raise ValueError("GCS did not provide an MD5 for the GGUF object")
    observed = base64.b64decode(blob.md5_hash).hex()
    if observed.lower() != expected_md5_hex.lower():
        raise ValueError(f"GGUF checksum mismatch: expected {expected_md5_hex.lower()}, observed {observed}")

    with open(actual_md5_hex, "w", encoding="utf-8") as output:
        output.write(observed)
    with open(object_generation, "w", encoding="utf-8") as output:
        output.write(str(blob.generation or ""))


@component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform==2.7.0", "google-cloud-storage==3.17.1"],
)
def register_dq4_model(
    gguf_artifact: Input[Model],
    source_pipeline_run: str,
    source_artifact_id: str,
    source_adapter_uri: str,
    gguf_file_uri: str,
    gguf_md5_hex: str,
    gguf_generation: str,
    serving_dir_uri: str,
    serving_image_uri: str,
    project: str,
    region: str,
    display_name: str,
    parent_model: str,
    version_aliases: str,
    vertex_model: Output[Model],
) -> None:
    """Assemble the serving directory and upload it as a new version of the team's Registry model.

    The serving directory already holds `handler.py` and the llama-cpp-python wheel (uploaded by the
    CLI); this step copies the verified GGUF next to them server side, then registers the directory
    with Google's prebuilt Hugging Face inference image. Earlier versions are never modified; only the
    aliases (e.g. `champion`) move to this version.
    """
    import base64
    from urllib.parse import urlparse

    from google.cloud import aiplatform, storage

    if not source_pipeline_run or not source_artifact_id or not source_adapter_uri:
        raise ValueError("source pipeline, artifact ID, and adapter URI are required for provenance")
    artifact_uri = gguf_artifact.uri.rstrip("/")
    source = urlparse(gguf_file_uri)
    serving = urlparse(serving_dir_uri.rstrip("/"))
    if source.scheme != "gs" or serving.scheme != "gs" or not serving.path.strip("/"):
        raise ValueError("gguf_file_uri and serving_dir_uri must be gs:// URIs")

    client = storage.Client(project=project)
    serving_bucket = client.bucket(serving.netloc)
    serving_prefix = serving.path.strip("/")
    for required in ("handler.py", "llama_cpp_python-0.3.16-cp311-cp311-linux_x86_64.whl"):
        if not serving_bucket.blob(f"{serving_prefix}/{required}").exists():
            raise ValueError(f"{required} is missing from {serving_dir_uri}")
    target = serving_bucket.blob(f"{serving_prefix}/model-q4.gguf")
    token = None
    while True:  # rewrite copies large objects server side in several calls
        token, _, _ = target.rewrite(
            client.bucket(source.netloc).blob(source.path.lstrip("/")), token=token
        )
        if token is None:
            break
    target.reload()
    if base64.b64decode(target.md5_hash).hex() != gguf_md5_hex.lower():
        raise ValueError("Copied GGUF checksum differs from the verified source")
    parent_parts = parent_model.split("/")
    if parent_model and (
        len(parent_parts) != 6
        or parent_parts[0] != "projects"
        or parent_parts[2:5] != ["locations", region, "models"]
        or not parent_parts[5].isdigit()
    ):
        raise ValueError("parent_model must be projects/<project>/locations/<region>/models/<numeric id>")
    aliases = [alias.strip() for alias in version_aliases.split(",") if alias.strip()]

    aiplatform.init(project=project, location=region)
    description = "\n".join(
        [
            "D-q4 Q4_K_M GGUF served on CPU by llama-cpp-python 0.3.16 (handler.py).",
            f"Source compact pipeline run: {source_pipeline_run}",
            f"Source KFP artifact ID: {source_artifact_id}",
            f"Source adapter URI: {source_adapter_uri}",
            f"Source GGUF artifact directory: {artifact_uri}",
            f"Source GGUF file: {gguf_file_uri}",
            f"GGUF GCS MD5: {gguf_md5_hex}",
            f"GGUF GCS generation: {gguf_generation}",
            f"Serving directory: {serving_dir_uri}",
        ]
    )
    model = aiplatform.Model.upload(
        display_name=display_name,
        parent_model=parent_model or None,
        is_default_version=True,
        version_aliases=aliases or None,
        version_description=description,
        artifact_uri=serving_dir_uri.rstrip("/"),
        serving_container_image_uri=serving_image_uri,
        serving_container_environment_variables={
            "HF_MODEL_DIR": "/opt/huggingface/model",
            "HF_TASK": "text-generation",
            "NAVY_GGUF_EXPECTED_MD5": gguf_md5_hex.lower(),
        },
        serving_container_ports=[8080],
        description=description,
        labels={
            "team": "navy",
            "project": "data-ai-product-navy",
            "base_model": "qwen2_5-3b-instruct",
            "tuning_method": "lora-peft",
            "quantization": "q4_k_m",
            "format": "gguf",
            "serving": "llama-cpp-python-0-3-16",
            "source_run": source_pipeline_run[-32:],
        },
        sync=True,
    )

    vertex_model.uri = model.versioned_resource_name
    vertex_model.metadata.update(
        {
            "versionedResourceName": model.versioned_resource_name,
            "resourceName": model.resource_name,
            "displayName": display_name,
            "sourcePipelineRun": source_pipeline_run,
            "sourceArtifactId": source_artifact_id,
            "sourceAdapterUri": source_adapter_uri,
            "ggufArtifactUri": artifact_uri,
            "ggufFileUri": gguf_file_uri,
            "ggufMd5Hex": gguf_md5_hex,
            "ggufGeneration": gguf_generation,
            "servingImageUri": serving_image_uri,
            "servingDirUri": serving_dir_uri,
        }
    )


@component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform==2.7.0"],
)
def create_dq4_endpoint(
    project: str,
    project_number: str,
    region: str,
    endpoint_display_name: str,
    endpoint_resource_name: str,
    endpoint: Output[Artifact],
) -> None:
    """Create a new endpoint, or accept only an empty endpoint in the target project/region."""
    from google.cloud import aiplatform

    aiplatform.init(project=project, location=region)
    if endpoint_resource_name:
        parts = endpoint_resource_name.split("/")
        if (
            len(parts) != 6
            or parts[0] != "projects"
            or parts[1] not in {project, project_number}
            or parts[2] != "locations"
            or parts[3] != region
            or parts[4] != "endpoints"
            or not parts[5]
        ):
            raise ValueError("Endpoint resource must belong to the configured project and region")
        target = aiplatform.Endpoint(endpoint_resource_name, project=project, location=region)
        if target.gca_resource.deployed_models:
            raise ValueError("The supplied endpoint is not empty; refusing to change its traffic")
    else:
        target = aiplatform.Endpoint.create(
            display_name=endpoint_display_name,
            project=project,
            location=region,
            labels={"app": "navy", "model": "dq4-gguf"},
            sync=True,
        )
    print(f"Ready empty endpoint resource: {target.resource_name}", flush=True)
    endpoint.uri = target.resource_name
    endpoint.metadata.update({"resourceName": target.resource_name})


@component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform==2.7.0"],
)
def deploy_dq4_model(
    model_versioned_resource_name: str,
    endpoint: Input[Artifact],
    project: str,
    project_number: str,
    region: str,
    machine_type: str,
    deployed_model_id: OutputPath(str),
) -> None:
    """Deploy exactly the specified Vertex model version to the empty endpoint."""
    from google.cloud import aiplatform

    versioned_name = model_versioned_resource_name.split("@")
    model_name = versioned_name[0]
    version_id = versioned_name[1] if len(versioned_name) == 2 else ""
    parts = model_name.split("/")
    if (
        len(parts) != 6
        or parts[0] != "projects"
        or parts[1] not in {project, project_number}
        or parts[2] != "locations"
        or parts[3] != region
        or parts[4] != "models"
        or not parts[5]
        or not version_id.isdigit()
    ):
        raise ValueError("Use a versioned model resource name in the configured project and region")
    endpoint_resource_name = endpoint.uri
    if not endpoint_resource_name:
        raise ValueError("Vertex Endpoint resource name is missing")
    endpoint_parts = endpoint_resource_name.split("/")
    if (
        len(endpoint_parts) != 6
        or endpoint_parts[0] != "projects"
        or endpoint_parts[1] not in {project, project_number}
        or endpoint_parts[2] != "locations"
        or endpoint_parts[3] != region
        or endpoint_parts[4] != "endpoints"
        or not endpoint_parts[5]
    ):
        raise ValueError("Endpoint resource must belong to the configured project and region")
    if not machine_type:
        raise ValueError("machine_type is required for billable endpoint deployment")

    aiplatform.init(project=project, location=region)
    target = aiplatform.Endpoint(endpoint_resource_name, project=project, location=region)
    if target.gca_resource.deployed_models:
        raise ValueError("Endpoint changed after preflight; refusing to deploy to a non-empty endpoint")
    model = aiplatform.Model(model_versioned_resource_name, project=project, location=region)
    target.deploy(
        model,
        machine_type=machine_type,
        min_replica_count=1,
        max_replica_count=1,
        traffic_percentage=100,
        sync=True,
    )
    deployed = list(target.gca_resource.deployed_models)
    if len(deployed) != 1:
        raise RuntimeError("Expected exactly one deployed model on the fresh endpoint")
    deployed_parts = deployed[0].model.split("/")
    if (
        len(deployed_parts) != 6
        or deployed_parts[0] != "projects"
        or deployed_parts[1] not in {project, project_number}
        or deployed_parts[2] != "locations"
        or deployed_parts[3] != region
        or deployed_parts[4] != "models"
        or deployed_parts[5].split("@", 1)[0] != parts[5]
        or str(deployed[0].model_version_id) != version_id
    ):
        raise RuntimeError("Vertex deployed a different model version than requested")
    with open(deployed_model_id, "w", encoding="utf-8") as output:
        output.write(deployed[0].id)


@component(
    base_image="python:3.11",
    packages_to_install=["google-cloud-aiplatform==2.7.0"],
)
def undeploy_dq4_endpoint(
    endpoint_resource_name: str,
    expected_model_versioned_resource_name: str,
    project: str,
    project_number: str,
    region: str,
    endpoint: Output[Artifact],
) -> None:
    """Remove only the expected D-q4 version, refusing shared or unexpected endpoints."""
    from google.cloud import aiplatform

    endpoint_parts = endpoint_resource_name.split("/")
    if (
        len(endpoint_parts) != 6
        or endpoint_parts[0] != "projects"
        or endpoint_parts[1] not in {project, project_number}
        or endpoint_parts[2] != "locations"
        or endpoint_parts[3] != region
        or endpoint_parts[4] != "endpoints"
        or not endpoint_parts[5]
    ):
        raise ValueError("Endpoint resource must belong to the configured project and region")
    if not expected_model_versioned_resource_name:
        raise ValueError("expected_model_versioned_resource_name is required")
    expected_parts = expected_model_versioned_resource_name.split("@")
    expected_model_parts = expected_parts[0].split("/")
    expected_version_id = expected_parts[1] if len(expected_parts) == 2 else ""
    if (
        len(expected_model_parts) != 6
        or expected_model_parts[0] != "projects"
        or expected_model_parts[1] not in {project, project_number}
        or expected_model_parts[2] != "locations"
        or expected_model_parts[3] != region
        or expected_model_parts[4] != "models"
        or not expected_model_parts[5]
        or not expected_version_id.isdigit()
    ):
        raise ValueError("Expected model must be a versioned resource in the configured project and region")
    aiplatform.init(project=project, location=region)
    target = aiplatform.Endpoint(endpoint_resource_name, project=project, location=region)
    deployed = list(target.gca_resource.deployed_models)
    if len(deployed) > 1:
        raise ValueError("Endpoint is shared; refusing to undeploy any model")
    if deployed:
        deployed_parts = deployed[0].model.split("/")
        if (
            len(deployed_parts) != 6
            or deployed_parts[0] != "projects"
            or deployed_parts[1] not in {project, project_number}
            or deployed_parts[2] != "locations"
            or deployed_parts[3] != region
            or deployed_parts[4] != "models"
            or deployed_parts[5].split("@", 1)[0] != expected_model_parts[5]
            or str(deployed[0].model_version_id) != expected_version_id
        ):
            raise ValueError("Endpoint contains an unexpected model version; refusing to undeploy it")
        target.undeploy(deployed_model_id=deployed[0].id, sync=True)
    target = aiplatform.Endpoint(endpoint_resource_name, project=project, location=region)
    remaining = list(target.gca_resource.deployed_models)
    if remaining:
        raise RuntimeError("Vertex endpoint still has deployed models after undeploy")
    endpoint.uri = target.resource_name
    endpoint.metadata.update({"resourceName": target.resource_name, "deployedModelCount": 0})
