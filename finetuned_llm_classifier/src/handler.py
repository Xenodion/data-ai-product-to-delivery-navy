import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Environment-specific values: set for a T4 GPU (Colab test and Vertex AI endpoint).
MODEL_DIR = "models/router-phi3"
DEVICE_MAP = "cuda:0"
TORCH_DTYPE = torch.float16  # T4 has no native bfloat16 support

# Only these generation parameters are accepted from requests, with their expected type.
ALLOWED_PARAMETERS = {
    "max_new_tokens": int,
    "do_sample": bool,
    "temperature": float,
    "top_p": float,
    "top_k": int,
}
DEFAULT_MAX_NEW_TOKENS = 160
MAX_NEW_TOKENS_LIMIT = 256  # caps GPU time per request
MAX_INSTANCES = 8  # caps the batch size of one request
MAX_INPUT_TOKENS = 3840  # Phi-3-mini-4k context (4096) minus MAX_NEW_TOKENS_LIMIT


def _clean_parameters(raw: dict) -> dict:
    """Keep the allowed generation parameters, cast them, and reject values outside a safe range."""
    parameters = {key: ALLOWED_PARAMETERS[key](value) for key, value in raw.items() if key in ALLOWED_PARAMETERS}
    max_new_tokens = parameters.get("max_new_tokens", DEFAULT_MAX_NEW_TOKENS)
    if max_new_tokens < 1:
        raise ValueError("max_new_tokens must be at least 1")
    parameters["max_new_tokens"] = min(max_new_tokens, MAX_NEW_TOKENS_LIMIT)
    if "temperature" in parameters and not 0 < parameters["temperature"] <= 2:
        raise ValueError("temperature must be in (0, 2]")
    if "top_p" in parameters and not 0 < parameters["top_p"] <= 1:
        raise ValueError("top_p must be in (0, 1]")
    if "top_k" in parameters and parameters["top_k"] < 1:
        raise ValueError("top_k must be at least 1")
    return parameters


class EndpointHandler:
    """Handler for processing inference requests using a Hugging Face model."""

    def __init__(self, model_dir: str = MODEL_DIR) -> None:
        """Load tokenizer and model from the specified directory."""
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.unk_token
            self.tokenizer.pad_token_id = self.tokenizer.unk_token_id

        # model_dir holds LoRA adapters: transformers loads the base model named in
        # adapter_config.json and attaches the adapters on top (requires peft).
        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            device_map=DEVICE_MAP,
            torch_dtype=TORCH_DTYPE,
        )
        self.model.eval()

    def __call__(self, data: dict) -> dict:
        """Generate a completion for each instance of a Vertex AI prediction request.

        Args:
            data: Vertex AI request body, e.g.
                {"instances": [{"prompt": "<chat-templated prompt: instruction + ticket>"}],
                 "parameters": {"max_new_tokens": 160, "do_sample": False}}

        Returns:
            Vertex AI response body: {"predictions": [{"response": "<decoded text>"}]},
            one prediction per instance, in the same order. The text holds the JSON object; the caller
            validates it against the schema and routes `UNDEFINED` or invalid output to a human.
        """
        instances = data["instances"]
        if not 1 <= len(instances) <= MAX_INSTANCES:
            raise ValueError(f"a request must hold between 1 and {MAX_INSTANCES} instances")
        prompts = [instance["prompt"] for instance in instances]
        parameters = _clean_parameters(data.get("parameters", {}))

        # Padding is on the left (tokenizer_config), so generation continues each prompt.
        inputs = self.tokenizer(prompts, return_tensors="pt", padding=True)
        if inputs["input_ids"].shape[1] > MAX_INPUT_TOKENS:
            raise ValueError(f"a prompt is longer than {MAX_INPUT_TOKENS} tokens")
        inputs = inputs.to(DEVICE_MAP)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                pad_token_id=self.tokenizer.pad_token_id,
                **parameters,
            )

        responses = self.tokenizer.batch_decode(outputs, skip_special_tokens=False)
        return {"predictions": [{"response": response} for response in responses]}
