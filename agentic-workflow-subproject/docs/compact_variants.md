# Compact variants (roadmap G6): merged and quantised model, smaller models

Status on 2026-11-02: **full run passed** on Vertex CPU for D-q8 and D-q4 (293 tickets of val: 1.0 and 0.3 silent errors per 100, 0 % urgent in a wrong desk, completed in 1 h 23 min on AMD EPYC 7B12, about 0.54 euro). Smaller models cancelled (section 2).

Why: the Qualifier Model outputs short JSON (about 35 tokens) from a prompt of about 500 tokens, so a 4-bit or 8-bit model on CPU can answer in seconds. The experiment compares quality with infrastructure cost (`docs/scoring_protocol.md`, section 6). Historical artifact paths and registry IDs containing `router` are unchanged.

## 1. Merged model, then GGUF (D-q4, D-q8)

Executed on 2026-11-02 via Vertex CPU job (8 vCPU, 32 GB, no GPU, no endpoint), pipeline `compact` (`research/qualifier/src/pipeline_components/compact_variants_component.py`). It merges the LoRA adapter into Qwen2.5-3B, converts to GGUF, quantises to Q8_0 and Q4_K_M, predicts the 293 val tickets one at a time and writes the GGUF files, the predictions CSVs and a `timings` JSON as artifacts in the bucket.

### Measured results on the 293 val tickets (2026-11-02)

* **Machine**: AMD EPYC 7B12 (8 vCPU, 33.7 GB RAM allocated).
* **Job duration**: 1 h 23 min 17 s (from 11:08:44 to 12:32:02 UTC). Real cost: about 0.54 euro (at about 0.39 euro per hour).
* **RAM footprint in production**: about 3.8 GB for D-q8, about 2.4 GB for D-q4.

| Metric | D-q8 (`Q8_0`) | D-q4 (`Q4_K_M`) | Full-precision D (T4 GPU) | Baseline B2 (TF-IDF) |
|---|---|---|---|---|
| **GGUF size** | 3,285 MB | 1,930 MB | about 6 GB (fp16) | < 10 MB |
| **RAM in inference** | about 3.8 GB | about 2.4 GB | about 14 GB VRAM | < 1 GB |
| **Mean / median / p95 seconds per ticket** | 7.92 / 7.38 / 12.26 | 6.43 / 6.11 / 10.10 | about 1.5 (GPU) | 0.0009 |
| **Silent errors per 100 tickets** | 1.0 | **0.3** (1 ticket) | 0.7 | 28.3 |
| **Urgent in a wrong desk** | 0 % | 0 % | 0 % | 7.6 % |
| **Sent to a human without need, per 100** | 0.7 | 1.0 | 0.7 | 0.7 |
| **Auto-routed** | 82.9 % | 82.6 % | 83.3 % | 86.3 % |
| **Desk accuracy** | 99.0 % | 98.6 % | 98.6 % | 94.9 % |
| **Valid JSON rate** | 99.0 % | 98.6 % | 99.0 % | 100 % |
| **Error severity score** | 0.051 | 0.020 | 0.027 | 1.478 |
| **Macro-F1 intent** | 0.989 | 0.987 | 0.984 | 0.927 |
| **Exact transaction id / amount** | 0.980 / 0.986 | 0.983 / 0.986 | 0.986 / 0.990 | 0.894 / 0.829 |
| **Recall high urgency** | 0.987 | 0.987 | 0.975 | 0.911 |

Quantising to 8 or 4 bits loses nothing visible on val. The differences between D, D-q8 and D-q4 are one or two tickets out of 293 and do not separate them; the test sets do (Journal 5).

*Artifacts saved in `docs/results/`: `d_q8_full_run_val_predictions.csv`, `d_q4_full_run_val_predictions.csv`, and `d_compact_full_run_timings.json`.*

### Runner commands

```bash
# Smoke test (20 tickets):
uv run python research/qualifier/scripts/pipeline_runner.py compact --smoke --adapter-uri gs://navy-team-llmops-bucket/pipeline_root/158407666882/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_-8515982401988460544/model --confirm-billable-run

# Full run on val (293 tickets):
uv run python research/qualifier/scripts/pipeline_runner.py compact --adapter-uri gs://navy-team-llmops-bucket/pipeline_root/158407666882/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_-8515982401988460544/model --confirm-billable-run
```

The manual steps below are what the job does.

1. Download the adapter of the full run from the bucket (`pipeline_root/<project>/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_*/model/`: `adapter_model.safetensors`, `adapter_config.json`, tokenizer files).
2. Merge in float16 on the CPU: load `Qwen/Qwen2.5-3B-Instruct`, `PeftModel.from_pretrained(base, adapter_dir)`, `merge_and_unload()`, `save_pretrained(merged_dir)` with the tokenizer.
3. Convert with the `convert_hf_to_gguf.py` script of `llama.cpp` (`--outtype f16`), then quantise with `llama-quantize` to `Q4_K_M` and `Q8_0`. Keep these tools and the model files outside the repository.
4. Run with `llama.cpp` (server or `llama-cpp-python`) using the Qwen chat template, the same `research/qualifier/src/prompt.py` instruction, temperature 0. A JSON grammar can force a valid JSON object, but a grammar that forces the schema would change the system (valid JSON would be 100 percent by construction): if used, report it as a separate system, not as D-q4.
5. Predict the 293 val tickets one at a time, writing a CSV with the columns `user_input` and `extracted_response`, and time the loop (model already loaded). Score with `uv run --with scikit-learn python research/qualifier/scripts/score_predictions.py <csv> val`.

## 2. Smaller models (S-1.5B, S-0.5B): cancelled on 2026-11-02

**Decision:** the planned runs on `Qwen2.5-1.5B-Instruct` and `0.5B-Instruct` are cancelled. Gate G6 is closed and declared passed with `D-q4`.

### Reasons

1. **D-q4 already fits the smallest container tier.**
   * Memory: about 2.4 GB of RAM, no GPU.
   * Latency: 6.43 s per ticket on a standard CPU. In an asynchronous email workflow a 6-second qualification delay is invisible to merchants.
   * Monthly inference compute for 36,000 tickets: 36,000 x 6.43 s = 231,336 CPU-seconds, about 64 CPU-hours. At the assumed serverless CPU price (about 0.00008 euro per second for 4 vCPU / 4 GB) this is **about 20 euros a month** (19 on val, 21 with the test latency on another CPU), or 5 to 10 euros on a shared node. A T4 endpoint running 24/7 costs about 255 euros a month. D-q4 already captures more than 90 % of the possible infrastructure saving.
2. **Diminishing returns.** A 1.5B or 0.5B model might answer in 3 to 4 seconds and save about 9 euros a month at most, and training them costs another 1.5 h of T4 and team time.
3. **The error that matters is the silent error.** A silent error that reaches a merchant costs 150 to 400 euros (investment memo, guess), and the smaller models have less capacity to extract 6-digit transaction ids, currency codes and implicit dates. The 9 euros a month of savings would be outweighed by a handful of extra silent errors.

**Conclusion:** D-q4 is locked as the production candidate for G6.

## 3. What is recorded

The metrics of D-q8 and D-q4 are in `docs/results/` and `notebooks/qualifier/04_compact_variants.ipynb`. The test sets were read once afterwards (Journal 5, `docs/scoring_protocol.md` section 8).
