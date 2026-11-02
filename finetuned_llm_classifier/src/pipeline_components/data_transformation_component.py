from kfp.dsl import component, OutputPath


@component(
    base_image="python:3.11",
    packages_to_install=["pandas", "gcsfs"],
)
def data_transformation(
    input_path: str,
    train_output: OutputPath("Dataset"),
    test_output: OutputPath("Dataset"),
    test_size: float = 0.1,
    seed: int = 42,
) -> None:
    import json
    import logging

    import pandas as pd

    logging.basicConfig(level=logging.INFO)

    df = pd.read_csv(input_path)
    logging.info("Read %d rows from %s", len(df), input_path)

    # Fail fast at the boundary: the raw file needs a ticket and a target that is a JSON object
    missing = {"ticket", "target"} - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {input_path}: {sorted(missing)}")
    invalid = []
    for index, target in df["target"].items():
        try:
            if not isinstance(json.loads(target), dict):
                invalid.append(index)
        except (TypeError, json.JSONDecodeError):
            invalid.append(index)
    if invalid:
        raise ValueError(f"{len(invalid)} rows have a target that is not a JSON object, first at row {invalid[0]}")

    # Random split for now; the evaluation gold set will be a separate, independently labelled file
    test = df.sample(frac=test_size, random_state=seed)
    train = df.drop(test.index)
    train.to_csv(train_output, index=False)
    test.to_csv(test_output, index=False)
    logging.info("Wrote %d train and %d test rows", len(train), len(test))
