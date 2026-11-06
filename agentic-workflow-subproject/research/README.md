# Research layout and migration

The Qualifier research code and scripts live in `qualifier/src/` and `qualifier/scripts/`; its journals and helpers live in `../notebooks/qualifier/`. Run the documented commands from the subproject root. `drafter/` and `confidence/` are placeholders for later studies. Existing datasets, saved results and historical provenance remain at their original locations.

The complete runtime will live inside this subproject: `backend/` for API, orchestration, persistence and nodes, `frontend/` for the support experience, and `demo/` for injection and fixtures. These directories are scaffolding, not working services. Existing datasets and results keep their current locations and provenance during migration. Decide a single shared seven-field contract before moving or duplicating the schema.
