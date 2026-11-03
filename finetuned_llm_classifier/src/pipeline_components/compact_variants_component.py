from kfp.dsl import Artifact, Dataset, Input, Model, Output, component


@component(
    base_image="python:3.11",
    packages_to_install=[
        "torch",
        "transformers==4.46.3",
        "peft==0.13.2",
        "pandas",
        "cmake",
        "sentencepiece",
        "protobuf",
        "gguf",
        "llama-cpp-python==0.3.16",
    ],
    pip_index_urls=["https://download.pytorch.org/whl/cpu", "https://pypi.org/simple"],
)
def compact_variants_component(
    test_dataset: Input[Dataset],
    instruction: str,
    adapter_uri: str,  # gs:// folder of the LoRA adapter saved by the fine-tuning step
    predictions_q8: Output[Dataset],
    predictions_q4: Output[Dataset],
    gguf_q8: Output[Model],
    gguf_q4: Output[Model],
    timings: Output[Artifact],
    model_id: str = "Qwen/Qwen2.5-3B-Instruct",
    max_new_tokens: int = 160,
    max_rows: int = 0,  # smoke test: predict only the first rows (0 = all)
) -> None:
    """Merge the adapter, convert to GGUF, quantise (Q8_0, Q4_K_M) and predict on CPU with timings.

    Systems D-q8 and D-q4 of the scoring protocol (section 7). Seconds per ticket are measured on the
    machine that runs this step, with the model already loaded; the machine is recorded in `timings`.
    """
    import gc
    import json
    import logging
    import os
    import platform
    import re
    import shutil
    import subprocess
    import sys
    import time
    from pathlib import Path

    import pandas as pd
    import torch
    from llama_cpp import Llama
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    logging.basicConfig(level=logging.INFO)
    work = Path("/tmp/compact")
    work.mkdir(parents=True, exist_ok=True)

    def run(cmd: list[str], cwd: Path | None = None) -> None:
        logging.info("Running: %s", " ".join(cmd))
        subprocess.run(cmd, cwd=cwd, check=True)

    # 1. Merge the adapter into the base model (float16 weights, CPU)
    adapter_dir = Path(adapter_uri.replace("gs://", "/gcs/", 1))
    logging.info("Merging adapter %s into %s", adapter_dir, model_id)
    base = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16)
    merged = PeftModel.from_pretrained(base, str(adapter_dir)).merge_and_unload()
    merged_dir = work / "merged"
    merged.save_pretrained(merged_dir)
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir))
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.save_pretrained(merged_dir)
    del base, merged
    gc.collect()

    # 2. llama.cpp tools: conversion script and quantiser (built from source)
    run(["git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp", str(work / "llama.cpp")])
    llama_dir = work / "llama.cpp"
    run([sys.executable, "-m", "pip", "install", "--no-deps", "./gguf-py"], cwd=llama_dir)
    run(["cmake", "-B", "build", "-DLLAMA_CURL=OFF"], cwd=llama_dir)
    run(["cmake", "--build", "build", "--target", "llama-quantize", "-j", str(os.cpu_count())], cwd=llama_dir)

    f16_path = work / "model-f16.gguf"
    run([sys.executable, "convert_hf_to_gguf.py", str(merged_dir), "--outtype", "f16", "--outfile", str(f16_path)], cwd=llama_dir)
    shutil.rmtree(merged_dir, ignore_errors=True)

    variants = {"q8": ("Q8_0", gguf_q8), "q4": ("Q4_K_M", gguf_q4)}
    for name, (quant, artifact) in variants.items():
        os.makedirs(artifact.path, exist_ok=True)
        run([
            str(llama_dir / "build" / "bin" / "llama-quantize"),
            str(f16_path),
            str(Path(artifact.path) / f"model-{name}.gguf"),
            quant,
            str(os.cpu_count()),
        ])
    f16_path.unlink(missing_ok=True)

    # 3. Predict one ticket at a time, greedy decoding, timing the loop with the model already loaded
    test_df = pd.read_csv(test_dataset.path, keep_default_na=False)
    if max_rows > 0:
        test_df = test_df.head(max_rows)

    def parse_json(text: str) -> str:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return ""
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True) if isinstance(parsed, dict) else ""

    report: dict = {
        "machine": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "tickets": len(test_df),
    }
    cpu_lines = [line for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")]
    report["cpu_model"] = cpu_lines[0].split(":", 1)[1].strip() if cpu_lines else "unknown"
    report["memory_gb"] = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1)

    for name, artifact_out in (("q8", predictions_q8), ("q4", predictions_q4)):
        gguf_file = Path((gguf_q8 if name == "q8" else gguf_q4).path) / f"model-{name}.gguf"
        llm = Llama(model_path=str(gguf_file), n_ctx=2048, n_threads=os.cpu_count(), verbose=False)
        rows, seconds = [], []
        for _, row in test_df.iterrows():
            messages = [{"role": "user", "content": f"{instruction}\n\nTicket:\n{row['ticket']}"}]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            start = time.perf_counter()
            out = llm(prompt, max_tokens=max_new_tokens, temperature=0.0, stop=["<|im_end|>", "<|endoftext|>"])
            seconds.append(time.perf_counter() - start)
            extracted = re.split(r"<\|im_end\|>|<\|endoftext\|>", out["choices"][0]["text"])[0].strip()
            valid = parse_json(extracted)
            rows.append({
                "user_input": row["ticket"],
                "reference": row["target"],
                "extracted_response": valid or extracted,
                "valid_json": bool(valid),
            })
        del llm
        gc.collect()
        os.makedirs(os.path.dirname(artifact_out.path), exist_ok=True)
        pd.DataFrame(rows).to_csv(artifact_out.path, index=False)
        ordered = sorted(seconds)
        report[name] = {
            "gguf_mb": round(gguf_file.stat().st_size / 1e6),
            "seconds_mean": round(sum(seconds) / len(seconds), 3),
            "seconds_median": round(ordered[len(ordered) // 2], 3),
            "seconds_p95": round(ordered[int(0.95 * (len(ordered) - 1))], 3),
            "valid_json": sum(r["valid_json"] for r in rows),
        }
        logging.info("%s: %s", name, report[name])

    os.makedirs(os.path.dirname(timings.path), exist_ok=True)
    Path(timings.path).write_text(json.dumps(report, indent=2))
