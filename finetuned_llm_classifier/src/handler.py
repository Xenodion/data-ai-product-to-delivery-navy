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
        prompts = [instance["prompt"] for instance in data["instances"]]
        parameters = {
            key: ALLOWED_PARAMETERS[key](value)
            for key, value in data.get("parameters", {}).items()
            if key in ALLOWED_PARAMETERS
        }
        parameters["max_new_tokens"] = min(
            parameters.get("max_new_tokens", DEFAULT_MAX_NEW_TOKENS), MAX_NEW_TOKENS_LIMIT
        )

        # Padding is on the left (tokenizer_config), so generation continues each prompt.
        inputs = self.tokenizer(prompts, return_tensors="pt", padding=True).to(DEVICE_MAP)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                pad_token_id=self.tokenizer.pad_token_id,
                **parameters,
            )

        responses = self.tokenizer.batch_decode(outputs, skip_special_tokens=False)
        return {"predictions": [{"response": response} for response in responses]}
