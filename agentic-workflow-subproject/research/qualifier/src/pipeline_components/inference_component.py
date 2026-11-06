from kfp.dsl import Dataset, Input, Model, Output, component


@component(
    base_image="pytorch/pytorch:2.8.0-cuda12.9-cudnn9-devel",
    packages_to_install=[
        "transformers==4.46.3",
        "peft==0.13.2",
        "datasets==3.6.0",
        "accelerate==1.15.0",
        "bitsandbytes==0.50.2",
        "pandas",
    ],
)
def inference_component(
    test_dataset: Input[Dataset],
    predictions: Output[Dataset],
    instruction: str,
    model: Input[Model] = None,  # LoRA adapter; left out, the base model alone answers (system B3)
    adapter_uri: str = "",  # gs:// folder of the LoRA adapter (used when run as standalone inference)
    model_id: str = "Qwen/Qwen2.5-3B-Instruct",
    max_new_tokens: int = 160,
    max_rows: int = 0,  # smoke test: predict only the first rows (0 = all)
) -> None:
    import json
    import logging
    import os
    import re
    import time
    from pathlib import Path

    import pandas as pd
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load 4-bit quantized base model
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float32,
    )
    logger.info("Loading base model: %s", model_id)
    base_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda:0",
        quantization_config=bnb_config,
    )

    # Load fine-tuned LoRA adapters and tokenizer (or the base model and its tokenizer alone)
    adapter_path = None
    if model is not None:
        adapter_path = Path(model.path)
    elif adapter_uri:
        adapter_path = Path(adapter_uri.replace("gs://", "/gcs/", 1))

    if adapter_path is not None:
        logger.info("Loading PEFT model from %s", adapter_path)
        peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))
    else:
        logger.info("No adapter: scoring the base model %s", model_id)
        peft_model = base_model
    peft_model.eval()

    tok_path = str(adapter_path) if adapter_path is not None else model_id
    tokenizer = AutoTokenizer.from_pretrained(tok_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.unk_token
        tokenizer.pad_token_id = tokenizer.unk_token_id

    # Load test dataset
    logger.info("Reading test dataset from %s", test_dataset.path)
    test_df = pd.read_csv(test_dataset.path, keep_default_na=False)
    if max_rows > 0:
        test_df = test_df.head(max_rows)
    logger.info("Test dataset contains %d samples", len(test_df))

    def build_prompt(tok, ticket: str) -> str:
        """Apply the model's chat template to the instruction + ticket for inference."""
        messages = [{"role": "user", "content": f"{instruction}\n\nTicket:\n{ticket}"}]
        return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def extract_response(text: str) -> str:
        """Cut the generated reply at the first end-of-turn token."""
        return re.split(r"<\|im_end\|>|<\|endoftext\|>", text)[0].strip()

    def parse_json(text: str) -> str:
        """Return the reply as compact JSON if it is a JSON object, else an empty string."""
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return ""
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True) if isinstance(parsed, dict) else ""

    results = []
    durations = []
    for _, row in test_df.iterrows():
        ticket = row["ticket"]
        prompt = build_prompt(tokenizer, ticket)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda:0")

        t0 = time.perf_counter()
        with torch.no_grad():
            outputs = peft_model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        durations.append(time.perf_counter() - t0)

        # Decode only the new tokens, so the prompt cannot leak into the reply
        raw_output = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)
        extracted = extract_response(raw_output)
        valid = parse_json(extracted)
        results.append({
            "user_input": ticket,
            "reference": row["target"],
            "extracted_response": valid or extracted,
            "valid_json": bool(valid),
        })

    if durations:
        ordered = sorted(durations)
        logger.info(
            "Latency: mean=%.3fs, median=%.3fs, p95=%.3fs over %d tickets",
            sum(durations) / len(durations),
            ordered[len(ordered) // 2],
            ordered[int(0.95 * (len(durations) - 1))],
            len(durations),
        )

    pred_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(predictions.path), exist_ok=True)
    pred_df.to_csv(predictions.path, index=False)
    logger.info(
        "Wrote %d predictions (%d valid JSON) to %s", len(pred_df), int(pred_df["valid_json"].sum()), predictions.path
    )
