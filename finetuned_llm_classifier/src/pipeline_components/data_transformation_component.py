from kfp.dsl import OutputPath, component


@component(
    base_image="python:3.11",
    packages_to_install=["pandas", "gcsfs"],
)
def data_transformation(
    dataset_uri: str,
    train_output: OutputPath("Dataset"),
    test_output: OutputPath("Dataset"),
    train_file: str = "train.csv",
    test_file: str = "val.csv",
) -> None:
    import json
    import logging

    import pandas as pd

    logging.basicConfig(level=logging.INFO)

    # The splits are fixed by the dataset build (no random split here); only validate and pass them on
    for name, output in ((train_file, train_output), (test_file, test_output)):
        path = f"{dataset_uri.rstrip('/')}/{name}"
        df = pd.read_csv(path, keep_default_na=False)
        logging.info("Read %d rows from %s", len(df), path)

        # Fail fast at the boundary: the file needs a ticket and a target that is a JSON object
        missing = {"ticket", "target"} - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
        invalid = []
        for index, target in df["target"].items():
            try:
                if not isinstance(json.loads(target), dict):
                    invalid.append(index)
            except (TypeError, json.JSONDecodeError):
                invalid.append(index)
        if invalid:
            raise ValueError(f"{len(invalid)} rows of {path} have a target that is not a JSON object, first at row {invalid[0]}")
        df.to_csv(output, index=False)
