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
    model: Input[Model],
    test_dataset: Input[Dataset],
    predictions: Output[Dataset],
    instruction: str,
    model_id: str = "microsoft/Phi-3-mini-4k-instruct",
    max_new_tokens: int = 160,
) -> None:
    import json
    import logging
    import os
    import re

    import pandas as pd
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    logging.basicConfig(level=logging.INFO)

    # Load 4-bit quantized base model
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float32,
    )
    logging.info("Loading base model: %s", model_id)
    base_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda:0",
        quantization_config=bnb_config,
    )

    # Load fine-tuned LoRA adapters and tokenizer
    logging.info("Loading PEFT model from %s", model.path)
    peft_model = PeftModel.from_pretrained(base_model, model.path)
    peft_model.eval()

    logging.info("Loading tokenizer from %s", model.path)
    tokenizer = AutoTokenizer.from_pretrained(model.path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.unk_token
        tokenizer.pad_token_id = tokenizer.unk_token_id

    # Load test dataset
    logging.info("Reading test dataset from %s", test_dataset.path)
    test_df = pd.read_csv(test_dataset.path)
    logging.info("Test dataset contains %d samples", len(test_df))

    def build_prompt(tok, ticket: str) -> str:
        """Apply the Phi-3 chat template to the instruction + ticket for inference."""
        messages = [{"role": "user", "content": f"{instruction}\n\nTicket:\n{ticket}"}]
        return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def extract_response(text: str) -> str:
        """Extract assistant reply stripping chat tokens and prompt."""
        match = re.search(r"<\|assistant\|>\s*([\s\S]*?)(?:<\|end(?:oftext)?\|>|$)", text)
        if match:
            return match.group(1).strip()
        return text.strip()

    def parse_json(text: str) -> str:
        """Return the reply as compact JSON if it is a JSON object, else an empty string."""
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return ""
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True) if isinstance(parsed, dict) else ""

    results = []
    for _, row in test_df.iterrows():
        ticket = row["ticket"]
        prompt = build_prompt(tokenizer, ticket)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda:0")

        with torch.no_grad():
            outputs = peft_model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )

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

    pred_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(predictions.path), exist_ok=True)
    pred_df.to_csv(predictions.path, index=False)
    logging.info(
        "Wrote %d predictions (%d valid JSON) to %s", len(pred_df), int(pred_df["valid_json"].sum()), predictions.path
    )
