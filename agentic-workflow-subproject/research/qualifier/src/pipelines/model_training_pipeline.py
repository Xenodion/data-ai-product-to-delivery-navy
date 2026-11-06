from kfp.dsl import pipeline

from research.qualifier.src.pipeline_components.data_transformation_component import data_transformation
from research.qualifier.src.pipeline_components.fine_tuning_component import fine_tuning_component
from research.qualifier.src.pipeline_components.inference_component import inference_component
from research.qualifier.src.prompt import INSTRUCTION


@pipeline(name="keelpay-router-training-pipeline")
def model_training_pipeline(
    dataset_uri: str,
    test_file: str = "val.csv",
    max_train_rows: int = 0,
    max_steps: int = -1,
    eval_steps: int = 50,
    max_rows: int = 0,
    compute_dtype: str = "float32",
    model_id: str = "Qwen/Qwen2.5-3B-Instruct",  # a smaller Qwen2.5 for the compact variants
) -> None:
    # Development runs are evaluated on val; the final run passes test_natural.csv, then test_traps.csv
    data_transformation_task = data_transformation(
        dataset_uri=dataset_uri, test_file=test_file
    )

    fine_tuning_task = fine_tuning_component(
        train_dataset=data_transformation_task.outputs["train_output"],
        instruction=INSTRUCTION,
        # Epochs and LoRA values are the starting point of the course reference project (3 epochs, r=8, lr=3e-4);
        # re-run the sweep pipeline on our dataset before trusting them.
        num_train_epochs=3,
        eval_steps=eval_steps,
        max_train_rows=max_train_rows,  # smoke test only
        max_steps=max_steps,
        compute_dtype=compute_dtype,
        model_id=model_id,
    )
    fine_tuning_task.set_accelerator_type("NVIDIA_TESLA_T4")
    fine_tuning_task.set_cpu_limit("16")
    fine_tuning_task.set_memory_limit("50G")

    inference_task = inference_component(
        model=fine_tuning_task.outputs["model"],
        test_dataset=data_transformation_task.outputs["test_output"],
        instruction=INSTRUCTION,
        max_rows=max_rows,
        model_id=model_id,
    )
    inference_task.set_accelerator_type("NVIDIA_TESLA_T4")
    inference_task.set_cpu_limit("16")
    inference_task.set_memory_limit("50G")

    # The evaluation step (field-level metrics) is added once its design is agreed.
