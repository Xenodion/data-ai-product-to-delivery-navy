from kfp.dsl import pipeline

from src.pipeline_components.data_transformation_component import data_transformation
from src.pipeline_components.inference_component import inference_component
from src.prompt import INSTRUCTION


@pipeline(name="keelpay-router-inference-pipeline")
def inference_pipeline(
    dataset_uri: str,
    adapter_uri: str = "",
    test_file: str = "val.csv",
    max_rows: int = 0,
    model_id: str = "Qwen/Qwen2.5-3B-Instruct",
) -> None:
    """Pure GPU inference for System D (original fine-tuned) or B3 (base model) on a test split."""
    data_transformation_task = data_transformation(
        dataset_uri=dataset_uri, test_file=test_file
    )
    inference_task = inference_component(
        test_dataset=data_transformation_task.outputs["test_output"],
        instruction=INSTRUCTION,
        adapter_uri=adapter_uri,
        max_rows=max_rows,
        model_id=model_id,
    )
    inference_task.set_accelerator_type("NVIDIA_TESLA_T4")
    inference_task.set_cpu_limit("16")
    inference_task.set_memory_limit("50G")
