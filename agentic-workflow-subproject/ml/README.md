# Models

`ml/` builds and evaluates the models; `flow/` uses them. Each topic has its own folder, with `src/`, `scripts/` and `notebooks/`.

`qualifier/` holds the dataset build, fine-tuning pipelines, scoring, baselines and journals of the Qualifier Model. Run the documented commands from the subproject root.

The seven-field contract lives in `qualifier/src/dataset_build/schema.py`, and `flow/` imports it from there. Datasets and saved results stay in `../data/` and `../docs/results/`.

Placement rules: [`../LAYOUT.md`](../LAYOUT.md).
