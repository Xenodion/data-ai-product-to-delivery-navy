# Compact variants (roadmap G6): merged and quantised model, smaller models

Status on 2026-11-01: **not run.** The merge needs about 8 GB of free RAM for the 3B model in float16 (16 GB total is safer) and about 20 GB of disk; the project lead's machine does not have it. The commands below were written from the documentation of the tools and **have not been executed**: check each one on a small test before relying on it. Everything here is local and free except part 2.

Why: the router outputs a short JSON (about 35 tokens) from a prompt of about 500 tokens, so a 4-bit model on a CPU may answer in seconds. The point is a front between quality and infrastructure cost (`docs/scoring_protocol.md`, section 7).

## 1. Merged model, then GGUF (D-q4, D-q8)

Needs a machine with enough RAM (another computer, a free notebook environment, or a billed CPU job on Vertex: say which before running).

1. Download the adapter of the full run from the bucket (`pipeline_root/<project>/keelpay-router-training-pipeline-20261101173631/fine-tuning-component_*/model/`: `adapter_model.safetensors`, `adapter_config.json`, tokenizer files).
2. Merge in float16 on the CPU: load `Qwen/Qwen2.5-3B-Instruct`, `PeftModel.from_pretrained(base, adapter_dir)`, `merge_and_unload()`, `save_pretrained(merged_dir)` with the tokenizer.
3. Convert with the `convert_hf_to_gguf.py` script of `llama.cpp` (`--outtype f16`), then quantise with `llama-quantize` to `Q4_K_M` and `Q8_0`. Keep these tools and the model files outside the repository.
4. Run with `llama.cpp` (server or `llama-cpp-python`) using the Qwen chat template, the same `src/prompt.py` instruction, temperature 0. A JSON grammar can force a valid JSON object, but a grammar that forces the schema would change the system (valid JSON would be 100 percent by construction): if used, report it as a separate system, not as D-q4.
5. Predict the 293 val tickets one at a time, writing a CSV with the columns `user_input` and `extracted_response`, and time the loop (model already loaded). Score with `uv run --with scikit-learn python scripts/score_predictions.py <csv> val`.

## 2. Smaller models (S-1.5B, S-0.5B), billed on Vertex

The pipeline is the same; only the base model changes. Ask for the project lead's go and state the teardown before each run.

```bash
uv run python scripts/pipeline_runner.py training --fp16 --model-id Qwen/Qwen2.5-1.5B-Instruct
uv run python scripts/pipeline_runner.py training --fp16 --model-id Qwen/Qwen2.5-0.5B-Instruct
```

Expected, by scaling from the 3B run (2 h 06 of T4 for training, 30 minutes for the 293 predictions): roughly half and a third of that. These are estimates to check on the first run's step rate, which the live TensorBoard files give within minutes. After each run: check in the console that no pipeline job is `RUNNING` or `PENDING`, download the predictions and score them on val. Small models handle 4-bit quantisation worse: use 8 or 5 bits for them.

## 3. What to write down

Seconds per ticket, the machine and its price (dated), the size of the file, the scores on val under both valid-JSON thresholds. Do not read the test sets until the list of `docs/scoring_protocol.md` section 7 is confirmed and every system that will be reported has its val score.
