# Compact variants (roadmap G6): merged and quantised model, smaller models

Status on 2026-11-02: **full run passed** on Vertex CPU for D-q8 and D-q4 (293 tickets of val, cost 0.051 and 0.020 per ticket, 0 % urgent wrong desk, completed in 1 h 23 min on AMD EPYC 7B12, ~0.54 €). Next step: smaller models (S-1.5B, S-0.5B).

Why: the router outputs a short JSON (about 35 tokens) from a prompt of about 500 tokens, so a 4-bit or 8-bit model on a CPU answers in seconds. The point is a front between quality and infrastructure cost (`docs/scoring_protocol.md`, section 7).

## 1. Merged model, then GGUF (D-q4, D-q8)

Executed on 2026-11-02 via Vertex CPU job (8 vCPU, 32 GB, no GPU, no endpoint), pipeline `compact` (`src/pipeline_components/compact_variants_component.py`). It merges the LoRA adapter into Qwen2.5-3B, converts to GGUF, quantises to Q8_0 and Q4_K_M, predicts the 293 val tickets one at a time and writes the GGUF files, the predictions CSVs and a `timings` JSON as artifacts in the bucket.

### Measured results on the 293 val tickets (2026-11-02)

* **Machine**: AMD EPYC 7B12 (8 vCPU, 33.7 GB RAM allocated).
* **Job duration**: 1 h 23 min 17 s (from 11:08:44 to 12:32:02 UTC). Real cost: ~0.54 € (at ~0.39 €/h).
* **RAM footprint in production**: ~3.8 GB for D-q8, ~2.4 GB for D-q4.

| Metric | D-q8 (`Q8_0`) | D-q4 (`Q4_K_M`) | Full-precision D (T4 GPU) | Baseline B2 (TF-IDF) |
|---|---|---|---|---|
| **GGUF size** | **3 285 MB** | **1 930 MB** | ~6 GB (fp16) | < 10 MB |
| **RAM in inference** | **~3.8 GB** | **~2.4 GB** | ~14 GB VRAM | < 1 GB |
| **Mean latency / ticket** | **7.92 s** | **6.43 s** | ~1.5 s (GPU) | 0.9 ms |
| **Median latency / ticket** | **7.38 s** | **6.11 s** | - | - |
| **p95 latency / ticket** | **12.26 s** | **10.10 s** | - | - |
| **Valid JSON rate** | **0.990** (293/293 syntax) | **0.986** (293/293 syntax) | 0.990 (290/293) | 1.000 |
| **Desk accuracy** | **0.990** | **0.986** | 0.986 | 0.928 |
| **Urgent wrong desk** | **0.000** (0 %) | **0.000** (0 %) | 0.000 (0 %) | 0.038 |
| **Cost per ticket** | **0.051** | **0.020** | 0.027 | 1.478 |
| **Macro F1 intent** | **0.989** | **0.987** | 0.984 | 0.912 |
| **Exact transaction id** | **0.980** | **0.983** | 0.986 | 0.894 |
| **Exact amount** | **0.986** | **0.986** | 0.990 | 0.829 |
| **Recall high urgency** | **0.987** | **0.987** | 0.975 | 0.911 |
| **Confident and wrong** | **0.004** (1 ticket) | **0.004** (1 ticket) | 0.007 | 0.041 |

*Artifacts saved in `docs/results/`: `d_q8_full_run_val_predictions.csv`, `d_q4_full_run_val_predictions.csv`, and `d_compact_full_run_timings.json`.*

### Runner commands

```bash
# Smoke test (20 tickets):
uv run python scripts/pipeline_runner.py compact --smoke --adapter-uri gs://navy-team-llmops-bucket/pipeline_root/158407666882/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_-8515982401988460544/model

# Full run on val (293 tickets):
uv run python scripts/pipeline_runner.py compact --adapter-uri gs://navy-team-llmops-bucket/pipeline_root/158407666882/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_-8515982401988460544/model
```

The manual steps below are what the job does.

1. Download the adapter of the full run from the bucket (`pipeline_root/<project>/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_*/model/`: `adapter_model.safetensors`, `adapter_config.json`, tokenizer files).
2. Merge in float16 on the CPU: load `Qwen/Qwen2.5-3B-Instruct`, `PeftModel.from_pretrained(base, adapter_dir)`, `merge_and_unload()`, `save_pretrained(merged_dir)` with the tokenizer.
3. Convert with the `convert_hf_to_gguf.py` script of `llama.cpp` (`--outtype f16`), then quantise with `llama-quantize` to `Q4_K_M` and `Q8_0`. Keep these tools and the model files outside the repository.
4. Run with `llama.cpp` (server or `llama-cpp-python`) using the Qwen chat template, the same `src/prompt.py` instruction, temperature 0. A JSON grammar can force a valid JSON object, but a grammar that forces the schema would change the system (valid JSON would be 100 percent by construction): if used, report it as a separate system, not as D-q4.
5. Predict the 293 val tickets one at a time, writing a CSV with the columns `user_input` and `extracted_response`, and time the loop (model already loaded). Score with `uv run --with scikit-learn python scripts/score_predictions.py <csv> val`.

## 2. Smaller models (S-1.5B, S-0.5B): Decision of 2026-11-02 to cancel

**Decision:** The planned runs on `Qwen2.5-1.5B-Instruct` and `0.5B-Instruct` are **cancelled**. Gate G6 is closed and declared passed with `D-q4`.

### Rationale and compute cost economics

1. **The 3B sweet spot with `D-q4`**:
   * Memory in production: **~2.4 GB of RAM**, fitting inside the smallest container tier (e.g. 4 GB Cloud Run or small shared VM) without GPU.
   * Latency: **6.43 s / ticket** on standard CPU (AMD EPYC). In Keelpay's asynchronous email workflow, a 6-second qualification delay is invisible to merchants and well within support SLAs.
   * Total monthly inference compute for 36,000 tickets:
     $$36\,000 \times 6.426\text{ s} = 231\,336\text{ CPU-seconds} \approx 64.3\text{ CPU-hours/month}$$
     At on-demand serverless CPU pricing (~0.00008 € / second for 4 vCPU / 4 GB), inference costs **~18 € / month** (or ~5–10 €/month on a shared node). In comparison, keeping an active unquantised GPU endpoint (T4 on Vertex AI, 24/7) costs **~$255 / month** (~3,060 €/year). `D-q4` already captures **> 93 % of all potential infrastructure savings**.

2. **Diminishing returns of smaller models**:
   * A 1.5B or 0.5B model might answer in 3 to 4 seconds, saving at most ~9 € / month in compute.
   * Training them would cost additional GPU compute (~1.5 h of T4, ~$1.00) and team time.

3. **Asymmetric risk on high-urgency errors**:
   * In Keelpay's cost matrix (`docs/scoring_protocol.md`), an urgent ticket misrouted (chargeback deadline missed, regulatory AML hold) costs **300 € to 400 €** in regulatory penalties and merchant losses.
   * `D-q4` achieves **0.0 % urgent wrong desk** (0 errors on 293 validation tickets) with an expected cost per ticket of **0.020** (against 1.478 for baseline B2).
   * Models < 1.5B have significantly reduced attention capacity for complex entity extraction (6-digit transaction IDs, currency codes, implicit dates) and edge cases. A drop of just 1 % on urgent routing accuracy would cause **over 1,000 € / month in operational losses**, completely dwarfing the 9 € / month of CPU savings.

**Conclusion:** Pushing for smaller models is economically irrational and operationally reckless. `D-q4` is locked as our production candidate for Gate G6.

## 3. What to write down

The metrics of D-q8 and D-q4 are logged in `docs/results/` and `notebooks/04_compact_variants.ipynb`. The test sets (`test_natural` and `test_traps`) remain unread until Gate G7.
