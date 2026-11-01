from kfp.dsl import pipeline

from src.pipeline_components.data_transformation_component import data_transformation
from src.pipeline_components.inference_component import inference_component
from src.prompt import INSTRUCTION


@pipeline(name="keelpay-router-base-model-pipeline")
def base_model_pipeline(dataset_uri: str, test_file: str = "val.csv") -> None:
    """System B3 of the scoring protocol: the same prompt and the same tickets, without the LoRA adapter."""
    data_transformation_task = data_transformation(
        dataset_uri=dataset_uri, test_file=test_file
    )
    inference_task = inference_component(
        test_dataset=data_transformation_task.outputs["test_output"],
        instruction=INSTRUCTION,
    )
    inference_task.set_accelerator_type("NVIDIA_TESLA_T4")
    inference_task.set_cpu_limit("16")
    inference_task.set_memory_limit("50G")
