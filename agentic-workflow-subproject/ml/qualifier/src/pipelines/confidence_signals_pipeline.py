from kfp.dsl import pipeline

from ml.qualifier.src.pipeline_components.confidence_signals_component import confidence_signals_component
from ml.qualifier.src.pipeline_components.data_transformation_component import data_transformation
from ml.qualifier.src.prompt import INSTRUCTION


@pipeline(name="keelpay-router-confidence-signals-pipeline")
def confidence_signals_pipeline(
    dataset_uri: str,
    gguf_uri: str,
    test_file: str = "val.csv",
    max_rows: int = 0,
) -> None:
    """D-q4 replayed on CPU with the probabilities of its tokens (no GPU, no endpoint)."""
    data_transformation_task = data_transformation(dataset_uri=dataset_uri, test_file=test_file)
    signals_task = confidence_signals_component(
        test_dataset=data_transformation_task.outputs["test_output"],
        instruction=INSTRUCTION,
        gguf_uri=gguf_uri,
        max_rows=max_rows,
    )
    signals_task.set_cpu_limit("8")
    signals_task.set_memory_limit("16G")
