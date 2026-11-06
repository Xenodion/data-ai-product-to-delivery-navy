# Roadmap and gates

Short and kept up to date: one line per gate, a gate is passed only when its check is written in the journal (`ml/qualifier/notebooks/`). Nothing billed on GCP starts without the go of the project lead and a planned teardown. Metric names follow `docs/scoring_protocol.md`.

## Where we are

| Gate | Check to pass | State |
|---|---|---|
| G1 Dataset | all splits at or above their floor, no leakage between splits, quarantine kept | passed (train 1,922, val 293, test_natural 610, test_traps 380) |
| G2 Baselines | B0-B2 scored with the protocol | passed (`docs/baseline_results.md`; B2 on test_natural: 33.9 silent errors per 100 tickets, 6.6 % of urgent tickets in a wrong desk) |
| G3 Smoke run | the pipeline runs end to end on Vertex, loss goes down, no NaN, valid JSON, no job left open | passed in float32 and float16 (float16 is 3 times faster) |
| G4 Full run D | Qwen2.5-3B + LoRA, float16, 3 epochs; the loss curve is read before anything else | passed (2 h 06 of T4; validation loss lowest at the last evaluation, step 1250, no overfitting) |
| G5 D on val | fewer silent errors than B2 on val and urgent tickets in a wrong desk not worse; otherwise diagnose (epochs, learning rate, errors by field) before touching the tests | passed (silent errors 0.7 per 100 against 28.3 for B2; urgent in a wrong desk 0 against 7.6 %); the 3 outputs rejected by the contract are malformed ids copied from the ticket, they go to a human |
| G6 Light variants | merged model then GGUF 4 bits on CPU; time per ticket measured on the same tickets and machine | passed on val: D-q4 locked (silent errors 0.3 per 100, 0 % urgent in a wrong desk, 6.4 s per ticket on CPU, about 2.4 GB of RAM, about 20 euros a month on 36,000 tickets); S-1.5B and S-0.5B cancelled (`docs/compact_variants.md`) |
| G7 Test | every system scored once on test_natural and test_traps | passed (`ml/qualifier/notebooks/05_final_evaluation.ipynb`): D-q4 champion with 0.7 silent errors per 100 against 33.9 for B2, 0.6 % of urgent tickets in a wrong desk (1 of 167) against 6.6 %. Acceptance bars of the brief: desk accuracy and auto-routing met, urgent guardrail and silent-error trigger not met on the model alone (`docs/scoring_protocol.md`, section 8) |
| G8 Registry and demo deployment | after G7, retain the registered model and build/deploy the shared synthetic-data demo: Python API on Cloud Run with CPU Qualifier Model, Routing Node, synthetic lookup/KB, external synthetic-only Drafter Model, functional frontend, Python Demo Injector, and Langfuse; verify teardown | registered historical artifact (`keelpay-router-json`, ID `7308774847222382592`, alias `qwen3b-lora-q4`, region `europe-west2`); no deployed demo endpoint currently standing; integrated demo is required future work |
| G9 Memo | preserve component metrics and infrastructure assumptions for the investment memo; distinguish historical model scoring from full-flow metrics | D-q4 CPU cost remains an assumption from compact-variant work; weighted 0.0745% serious-error input is an assumption, not measured reviewer catch rate |

## Open items

- Complete the LLM fine-tuning comparison recovery in `docs/llmops_recovery_tasks.md`: import the validated B3 `val` export into MLflow, recover/verify B3 test artifacts before any further test comparison, refresh comparison figures and notebook narrative, and make training/inference/registry lineage visible from MLflow. Do not rerun a billed Vertex job to recreate metadata.
- Test the complete flow on synthetic tickets: priority remains visible while draft preparation proceeds; every draft receives Human Review before simulated send. Measure missed urgencies and handling time as well as model errors.
- Integrate the Drafter Model outside this folder, using an external API only with non-critical synthetic demo data.
- Build the deterministic Routing Node, synthetic lookup/KB, durable queues, functional three-tab UI, Python Demo Injector, and Langfuse traces as shared-project work.

## Rules that stay fixed

- Settings are chosen on val only; the test sets are read once, at G7.
- Added systems are reported as extra rows and as points of the front.
- No model/demo endpoint is deployed before G7 is done and a model is chosen; the target demo backend is Cloud Run, not an already deployed service.
- Pipeline jobs end by themselves; an endpoint never does. Check the console after every run and delete any endpoint the same day.
