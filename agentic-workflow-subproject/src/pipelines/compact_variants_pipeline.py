from kfp.dsl import pipeline

from src.pipeline_components.compact_variants_component import compact_variants_component
from src.pipeline_components.data_transformation_component import data_transformation
from src.prompt import INSTRUCTION


@pipeline(name="keelpay-router-compact-variants-pipeline")
def compact_variants_pipeline(
    dataset_uri: str,
    adapter_uri: str,
    test_file: str = "val.csv",
    max_rows: int = 0,
    model_id: str = "Qwen/Qwen2.5-3B-Instruct",
) -> None:
    """Systems D-q8 and D-q4: merged adapter, GGUF, quantised, predicted on CPU (no GPU, no endpoint)."""
    data_transformation_task = data_transformation(dataset_uri=dataset_uri, test_file=test_file)
    compact_task = compact_variants_component(
        test_dataset=data_transformation_task.outputs["test_output"],
        instruction=INSTRUCTION,
        adapter_uri=adapter_uri,
        max_rows=max_rows,
        model_id=model_id,
    )
    compact_task.set_cpu_limit("8")
    compact_task.set_memory_limit("32G")
