from kfp.dsl import pipeline

from src.pipeline_components.data_transformation_component import data_transformation
from src.pipeline_components.fine_tuning_component import fine_tuning_component
from src.prompt import INSTRUCTION

# One parameter varied at a time around the baseline (lr=3e-4, r=8, dropout=0.05): 7 distinct runs
BASELINE = {"learning_rate": 3e-4, "lora_r": 8, "lora_alpha": 16, "lora_dropout": 0.05}
SWEEP_CONFIGS = [
    BASELINE,
    {**BASELINE, "learning_rate": 1e-4},
    {**BASELINE, "learning_rate": 1e-3},
    {**BASELINE, "lora_r": 4, "lora_alpha": 8},
    {**BASELINE, "lora_r": 16, "lora_alpha": 32},
    {**BASELINE, "lora_dropout": 0.1},
    {**BASELINE, "lora_dropout": 0.2},
]


@pipeline(name="keelpay-router-hyperparameter-sweep-pipeline")
def hyperparameter_sweep_pipeline(input_path: str, num_train_epochs: int = 3) -> None:
    data_transformation_task = data_transformation(input_path=input_path)

    # Python loop at compile time: one task per config. dsl.ParallelFor would turn the int lora_r into a float.
    previous_task = None
    for config in SWEEP_CONFIGS:
        fine_tuning_task = fine_tuning_component(
            train_dataset=data_transformation_task.outputs["train_output"],
            instruction=INSTRUCTION,
            num_train_epochs=num_train_epochs,
            **config,
        )
        fine_tuning_task.set_display_name(
            f"fine-tuning lr={config['learning_rate']} r={config['lora_r']} dropout={config['lora_dropout']}"
        )
        fine_tuning_task.set_accelerator_type("NVIDIA_TESLA_T4")
        fine_tuning_task.set_cpu_limit("16")
        fine_tuning_task.set_memory_limit("50G")
        # Runs are chained one after another because the T4 quota is likely 1 GPU;
        # drop .after() if the quota allows parallel runs.
        if previous_task is not None:
            fine_tuning_task.after(previous_task)
        previous_task = fine_tuning_task
