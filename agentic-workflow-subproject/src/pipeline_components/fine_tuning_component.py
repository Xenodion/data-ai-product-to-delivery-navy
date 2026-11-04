from kfp.dsl import Dataset, Input, Metrics, Model, Output, component


@component(
    base_image="pytorch/pytorch:2.8.0-cuda12.9-cudnn9-devel",
    packages_to_install=[
        "transformers==4.46.3",
        "peft==0.13.2",
        "trl==0.12.2",
        "datasets==3.6.0",
        "accelerate==1.15.0",
        "bitsandbytes==0.50.2",
        "tensorboard",
        "pandas",
    ],
)
def fine_tuning_component(
    train_dataset: Input[Dataset],
    model: Output[Model],
    metrics: Output[Metrics],
    instruction: str,
    model_id: str = "Qwen/Qwen2.5-3B-Instruct",
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    learning_rate: float = 3e-4,
    num_train_epochs: int = 3,
    per_device_train_batch_size: int = 2,
    gradient_accumulation_steps: int = 2,
    # Our chats are about 500 tokens (99 % under 820); 512 would cut the JSON answer off 41 % of the tickets
    max_seq_length: int = 1024,
    eval_steps: int = 50,
    val_size: float = 0.1,
    max_train_rows: int = 0,  # smoke test: keep only the first rows (0 = all)
    max_steps: int = -1,  # smoke test: stop after this many optimizer steps (-1 = follow the epochs)
    compute_dtype: str = "float32",  # "float16" is much faster on a T4 (no bfloat16), at the risk of unstable losses
    seed: int = 42,
) -> None:
    import json
    import logging
    from pathlib import Path

    import pandas as pd
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import DataCollatorForCompletionOnlyLM, SFTConfig, SFTTrainer

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.unk_token
        tokenizer.pad_token_id = tokenizer.unk_token_id

    # Dataset: one chat per ticket (user turn = instruction + ticket, assistant turn = the JSON), rendered with the
    # chat template of the model, the same one the inference step applies.
    df = pd.read_csv(train_dataset.path, keep_default_na=False)
    if max_train_rows > 0:
        df = df.head(max_train_rows)
    dataset = Dataset.from_list([
        {"text": tokenizer.apply_chat_template(
            [
                {"role": "user", "content": f"{instruction}\n\nTicket:\n{row.ticket}"},
                {"role": "assistant", "content": row.target},
            ],
            tokenize=False,
        )}
        for row in df.itertuples()
    ])
    split = dataset.train_test_split(test_size=val_size, seed=seed)
    logger.info("Train: %d rows, validation: %d rows", len(split["train"]), len(split["test"]))

    # The loss is computed on the assistant answer only: the instruction is identical in every example
    collator = DataCollatorForCompletionOnlyLM(
        response_template=tokenizer.encode("<|im_start|>assistant\n", add_special_tokens=False),
        tokenizer=tokenizer,
    )

    # Model: Qwen2.5 quantized to 4 bits, then LoRA adapters on top
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=getattr(torch, compute_dtype),
    )
    base_model = AutoModelForCausalLM.from_pretrained(model_id, device_map="cuda:0", quantization_config=bnb_config)
    base_model = prepare_model_for_kbit_training(base_model)
    peft_model = get_peft_model(base_model, LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    ))
    trainable, total = peft_model.get_nb_trainable_parameters()
    logger.info("Trainable params: %d / %d", trainable, total)

    sft_config = SFTConfig(
        output_dir="/tmp/checkpoints",
        learning_rate=learning_rate,
        num_train_epochs=num_train_epochs,
        max_steps=max_steps,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_train_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        packing=False,
        fp16=compute_dtype == "float16",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=eval_steps,
        # Keep the checkpoint with the lowest validation loss instead of the last one (guards against overfitting)
        save_strategy="steps",
        save_steps=eval_steps,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to=["tensorboard"],
        logging_dir=metrics.path,  # TensorBoard event files land in the Metrics artifact on GCS
        seed=seed,
    )
    trainer = SFTTrainer(
        model=peft_model,
        args=sft_config,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        data_collator=collator,
        processing_class=tokenizer,
    )
    train_result = trainer.train()

    # Save the LoRA adapter, the tokenizer and the loss curve (train and eval loss by step) to the Model artifact
    trainer.save_model(model.path)
    tokenizer.save_pretrained(model.path)
    (Path(model.path) / "log_history.json").write_text(json.dumps(trainer.state.log_history, indent=1))

    # Final metrics, visible in the Vertex Pipelines console
    metrics.log_metric("train_loss", train_result.training_loss)
    metrics.log_metric("eval_loss", trainer.evaluate()["eval_loss"])
    metrics.log_metric("trainable_params", trainable)
