from kfp.dsl import pipeline

from src.pipeline_components.data_transformation_component import data_transformation
from src.pipeline_components.fine_tuning_component import fine_tuning_component
from src.pipeline_components.inference_component import inference_component
from src.prompt import INSTRUCTION


@pipeline(name="keelpay-router-training-pipeline")
def model_training_pipeline(input_path: str) -> None:
    data_transformation_task = data_transformation(input_path=input_path)

    fine_tuning_task = fine_tuning_component(
        train_dataset=data_transformation_task.outputs["train_output"],
        instruction=INSTRUCTION,
        # Epochs and LoRA values are the starting point of the course reference project (3 epochs, r=8, lr=3e-4);
        # re-run the sweep pipeline on our dataset before trusting them.
        num_train_epochs=3,
    )
    fine_tuning_task.set_accelerator_type("NVIDIA_TESLA_T4")
    fine_tuning_task.set_cpu_limit("16")
    fine_tuning_task.set_memory_limit("50G")

    inference_task = inference_component(
        model=fine_tuning_task.outputs["model"],
        test_dataset=data_transformation_task.outputs["test_output"],
        instruction=INSTRUCTION,
    )
    inference_task.set_accelerator_type("NVIDIA_TESLA_T4")
    inference_task.set_cpu_limit("16")
    inference_task.set_memory_limit("50G")

    # The evaluation step (field-level metrics) is added once its design is agreed.
