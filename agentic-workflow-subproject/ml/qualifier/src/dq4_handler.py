"""Vertex AI handler serving the D-q4 GGUF with llama-cpp-python on CPU.

Runs in Google's prebuilt Hugging Face inference container (the same image as the other Registry
models). The Registry artifact directory holds `handler.py` (this file), `model-q4.gguf` and the
pinned llama-cpp-python wheel; the toolkit downloads it and calls `EndpointHandler(model_dir)`.
Installing the bundled wheel at load keeps start-up offline and reproducible.

Request:  {"instances": [{"prompt": "<instruction + ticket>"}], "parameters": {"max_tokens": 160}}
Response: {"predictions": [{"response": "<model text, expected to be the JSON label>"}]}
"""

import hashlib
import os
import subprocess
import sys
import threading
from pathlib import Path

GGUF_NAME = "model-q4.gguf"
WHEEL_NAME = "llama_cpp_python-0.3.16-cp311-cp311-linux_x86_64.whl"
N_CTX = 2048  # same context as the D-q4 evaluation
DEFAULT_MAX_TOKENS = 160  # same budget as the D-q4 evaluation
MAX_TOKENS_LIMIT = 256
MAX_INSTANCES = 4  # CPU inference is sequential; caps the time of one request


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class EndpointHandler:
    """Load the GGUF once and answer Vertex prediction requests."""

    def __init__(self, model_dir: str) -> None:
        root = Path(model_dir)
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", str(root / WHEEL_NAME)],
                check=True,
            )
        from llama_cpp import Llama

        model_path = root / GGUF_NAME
        expected_md5 = os.environ.get("NAVY_GGUF_EXPECTED_MD5", "").lower()
        if expected_md5 and _md5(model_path) != expected_md5:
            raise RuntimeError(f"GGUF checksum mismatch: expected {expected_md5}")
        self.llm = Llama(model_path=str(model_path), n_ctx=N_CTX, n_threads=os.cpu_count(), verbose=False)
        self.lock = threading.Lock()  # one llama.cpp context is not safe for concurrent calls

    def __call__(self, data: dict) -> dict:
        instances = data["instances"]
        if not 1 <= len(instances) <= MAX_INSTANCES:
            raise ValueError(f"a request must hold between 1 and {MAX_INSTANCES} instances")
        max_tokens = int(data.get("parameters", {}).get("max_tokens", DEFAULT_MAX_TOKENS))
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        max_tokens = min(max_tokens, MAX_TOKENS_LIMIT)

        predictions = []
        with self.lock:
            for instance in instances:
                out = self.llm.create_chat_completion(
                    messages=[{"role": "user", "content": str(instance["prompt"])}],
                    max_tokens=max_tokens,
                    temperature=0.0,  # greedy, as in the evaluation
                )
                predictions.append({"response": out["choices"][0]["message"]["content"].strip()})
        return {"predictions": predictions}
