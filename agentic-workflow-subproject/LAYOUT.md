# Subproject layout rules

This layout is frozen. `tests/test_layout.py` enforces it.

| What the code does | Where it goes |
|---|---|
| Runs in the demo | `flow/` for pipeline steps, `frontend/` for the interface, `api/` once the API exists |
| Builds, trains or evaluates a model, or studies one | `ml/<topic>/` |
| Holds datasets or run outputs | `data/` |
| Explains a result or a method | `docs/` |
| Tests code | `tests/<same folder as the code>/` |
| Is generated or downloaded on a machine | `.local/`, ignored by Git and created by `flow.setup_local` |

Inside `ml/<topic>/`, code goes in `src/`, entry points in `scripts/` and journals in `notebooks/`. A topic stays in one folder. Notebooks live nowhere else.

Code gets the `.local/` folders from `ml/qualifier/src/local_paths.py`. Create a folder when its first real file arrives, never as an empty placeholder. Specifications live in `specs/` here, and design references in `docs/design/`. The repository root belongs to the AI Product course: it follows the course template and holds no code or technical specification.

`flow/` may import from `ml/`. `ml/` never imports from `flow/`.

Adding a top-level folder is an explicit decision: update this file, the README layout and `tests/test_layout.py` together.
