# Roadmap and gates

Short and kept up to date: one line per gate, a gate is passed only when its check is written in the journal (`notebooks/`). Nothing billed on GCP starts without the go of the project lead and a planned teardown.

## Where we are

| Gate | Check to pass | State |
|---|---|---|
| G1 Dataset | all splits at or above their floor, no leakage between splits, quarantine kept | passed (train 1922, val 293, test_natural 610, test_traps 380) |
| G2 Baselines | B0-B2 scored once with the frozen protocol | passed (`docs/baseline_results.md`; B2 cost 1.666 per ticket on test_natural) |
| G3 Smoke run | the pipeline runs end to end on Vertex, loss goes down, no NaN, valid JSON, no job left open | passed in float32 and float16 (float16 is 3 times faster) |
| G4 Full run D | Qwen2.5-3B + LoRA, float16, 3 epochs; the loss curve is read before anything else | to do |
| G5 D on val | valid JSON at least 99 percent and expected cost per ticket not worse than B2 on val; otherwise diagnose (epochs, learning rate, errors by field) before touching the tests | to do |
| G6 Light variants | merged model then GGUF 4 bits on CPU, then a smaller fine-tuned model with a lighter compression; time per ticket measured on the same tickets and the same machine | to do |
| G7 Test | the added systems and the efficiency metric are written in `docs/scoring_protocol.md` first; then every system is scored once on test_natural and test_traps | to do |
| G8 Registry and deployment (conditional) | only after G7 and once one model is chosen; if the chosen model runs well locally, we stop there and ask the teacher whether a deployed endpoint is required; if it is, register the adapter in the Vertex AI Model Registry and deploy only for the demo, with the teardown checked in the console | to decide after G7 |
| G9 Memo | cost per ticket of each system and the efficiency/cost front fed to the investment memo | to do |

## Rules that stay fixed

- Settings are chosen on val only; the test sets are read once, at G7.
- The decision rule of `docs/scoring_protocol.md` is not changed after results are seen. Added systems are reported as extra rows and as a point on the front, not as a new rule.
- No endpoint is deployed before G7 is done and a model is chosen.
- Pipeline jobs end by themselves; an endpoint never does. Check the console after every run and delete any endpoint the same day.
