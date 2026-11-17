"""Register a verified historical D-q4 GGUF and deploy its exact Vertex version."""

from kfp import dsl
from kfp.dsl import Model, importer

from ml.qualifier.src.pipeline_components.dq4_promotion_component import (
    build_llama_cpp_wheel,
    create_dq4_endpoint,
    deploy_dq4_model,
    register_dq4_model,
    undeploy_dq4_endpoint,
    verify_gguf_object,
)


@dsl.pipeline(
    name="keelpay-dq4-gguf-promotion-pipeline",
    description="Promote a verified historical D-q4 GGUF into a distinct Vertex Registry model.",
)
def dq4_promotion_pipeline(
    project: str,
    region: str,
    gguf_artifact_uri: str,
    gguf_file_uri: str,
    expected_md5_hex: str,
    source_pipeline_run: str,
    source_artifact_id: str,
    source_adapter_uri: str,
    serving_dir_uri: str,
    serving_image_uri: str,
    display_name: str = "navy-team-keelpay-router-json",
    parent_model: str = "",
    version_aliases: str = "d-q4-gguf,champion",
) -> None:
    source_artifact = importer(
        artifact_uri=gguf_artifact_uri,
        artifact_class=Model,
        reimport=False,
    )
    verified = verify_gguf_object(
        gguf_file_uri=gguf_file_uri,
        expected_md5_hex=expected_md5_hex,
    )
    wheel = (
        build_llama_cpp_wheel(serving_dir_uri=serving_dir_uri)
        .set_cpu_limit("8")
        .set_memory_limit("16G")
    )
    register_dq4_model(
        gguf_artifact=source_artifact.outputs["artifact"],
        source_pipeline_run=source_pipeline_run,
        source_artifact_id=source_artifact_id,
        source_adapter_uri=source_adapter_uri,
        gguf_file_uri=gguf_file_uri,
        gguf_md5_hex=verified.outputs["actual_md5_hex"],
        gguf_generation=verified.outputs["object_generation"],
        serving_dir_uri=serving_dir_uri,
        serving_image_uri=serving_image_uri,
        project=project,
        region=region,
        display_name=display_name,
        parent_model=parent_model,
        version_aliases=version_aliases,
    ).after(wheel)


@dsl.pipeline(
    name="keelpay-dq4-gguf-deployment-pipeline",
    description="Deploy one exact D-q4 Registry model version to a fresh one-replica endpoint.",
)
def dq4_deployment_pipeline(
    project: str,
    project_number: str,
    region: str,
    model_versioned_resource_name: str,
    endpoint_display_name: str,
    machine_type: str,
    endpoint_resource_name: str = "",
) -> None:
    created_endpoint = create_dq4_endpoint(
        project=project,
        project_number=project_number,
        region=region,
        endpoint_display_name=endpoint_display_name,
        endpoint_resource_name=endpoint_resource_name,
    )
    deploy_dq4_model(
        model_versioned_resource_name=model_versioned_resource_name,
        endpoint=created_endpoint.outputs["endpoint"],
        project=project,
        project_number=project_number,
        region=region,
        machine_type=machine_type,
    )


@dsl.pipeline(
    name="keelpay-dq4-gguf-undeployment-pipeline",
    description="Undeploy the expected D-q4 model version, refusing to remove other models.",
)
def dq4_undeployment_pipeline(
    project: str,
    project_number: str,
    region: str,
    endpoint_resource_name: str,
    expected_model_versioned_resource_name: str,
) -> None:
    undeploy_dq4_endpoint(
        endpoint_resource_name=endpoint_resource_name,
        expected_model_versioned_resource_name=expected_model_versioned_resource_name,
        project=project,
        project_number=project_number,
        region=region,
    )
