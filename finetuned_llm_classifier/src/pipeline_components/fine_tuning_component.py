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
    model_id: str = "microsoft/Phi-3-mini-4k-instruct",
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    learning_rate: float = 3e-4,
    num_train_epochs: int = 3,
    per_device_train_batch_size: int = 4,
    max_seq_length: int = 512,
    eval_steps: int = 50,
    val_size: float = 0.1,
    seed: int = 42,
) -> None:
    import logging

    import pandas as pd
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    logging.basicConfig(level=logging.INFO)

    # Dataset: one chat per ticket, the user turn is the instruction + the ticket, the assistant turn is the JSON
    df = pd.read_csv(train_dataset.path)
    dataset = Dataset.from_list([
        {"messages": [
            {"role": "user", "content": f"{instruction}\n\nTicket:\n{row.ticket}"},
            {"role": "assistant", "content": row.target},
        ]}
        for row in df.itertuples()
    ])
    split = dataset.train_test_split(test_size=val_size, seed=seed)
    logging.info("Train: %d rows, validation: %d rows", len(split["train"]), len(split["test"]))

    # Model: Phi-3 quantized to 4 bits, then LoRA adapters on top
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float32,
    )
    base_model = AutoModelForCausalLM.from_pretrained(model_id, device_map="cuda:0", quantization_config=bnb_config)
    base_model = prepare_model_for_kbit_training(base_model)
    peft_model = get_peft_model(base_model, LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=["o_proj", "qkv_proj", "gate_up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    ))
    trainable, total = peft_model.get_nb_trainable_parameters()
    logging.info("Trainable params: %d / %d", trainable, total)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.unk_token
    tokenizer.pad_token_id = tokenizer.unk_token_id

    sft_config = SFTConfig(
        output_dir="/tmp/checkpoints",
        learning_rate=learning_rate,
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        max_seq_length=max_seq_length,
        packing=True,
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
        processing_class=tokenizer,
    )
    train_result = trainer.train()

    # Save the LoRA adapter and the tokenizer to the Model artifact
    trainer.save_model(model.path)
    tokenizer.save_pretrained(model.path)

    # Final metrics, visible in the Vertex Pipelines console
    metrics.log_metric("train_loss", train_result.training_loss)
    metrics.log_metric("eval_loss", trainer.evaluate()["eval_loss"])
    metrics.log_metric("trainable_params", trainable)
