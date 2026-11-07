from kfp.dsl import Dataset, Input, Output, component


@component(
    base_image="python:3.11",
    packages_to_install=["numpy", "pandas", "cmake", "llama-cpp-python==0.3.16"],
    pip_index_urls=["https://pypi.org/simple"],
)
def confidence_signals_component(
    test_dataset: Input[Dataset],
    instruction: str,
    gguf_uri: str,  # gs:// path of model-q4.gguf, the file the flow serves
    signals: Output[Dataset],
    max_new_tokens: int = 200,
    max_rows: int = 0,  # smoke test: replay only the first rows (0 = all)
) -> None:
    """Replay a split through D-q4 and save the probabilities of the tokens it writes (study of #45).

    Same prompt, same GGUF and greedy decoding as the served Qualifier. The prompt is evaluated once and
    only the logits of the last token are read at each step; the output is JSON lines, one per ticket.
    """
    import json
    import logging
    import os
    import shutil
    import time
    from pathlib import Path

    import numpy as np
    import pandas as pd
    from llama_cpp import Llama

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    top_k = 5
    stop_tokens = ["<|im_end|>", "<|endoftext|>"]
    # Same text as the served Qualifier (flow/qualifier.py); KFP components cannot import local modules.
    chat_template = (
        "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n"
        "<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
    )

    # Vertex mounts the bucket under /gcs/; copy the model to local disk before loading it
    source = Path(gguf_uri.replace("gs://", "/gcs/", 1))
    local_model = Path("/tmp/model-q4.gguf")
    shutil.copyfile(source, local_model)
    llm = Llama(model_path=str(local_model), n_ctx=2048, n_threads=os.cpu_count(), verbose=False)
    stop_ids = {llm.token_eos(), *(llm.tokenize(t.encode(), add_bos=False, special=True)[0] for t in stop_tokens)}

    def log_softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - logits.max()
        return shifted - np.log(np.exp(shifted).sum())

    def piece(token_id: int) -> str:
        return llm.detokenize([token_id]).decode("utf-8", errors="replace")

    def generate(prompt: str) -> dict:
        llm.reset()
        llm.eval(llm.tokenize(prompt.encode("utf-8"), add_bos=False, special=True))
        tokens, logprobs, tops, offsets, length = [], [], [], [], 0
        for _ in range(max_new_tokens):
            pointer = llm._ctx.get_logits_ith(-1)
            logp = log_softmax(np.ctypeslib.as_array(pointer, shape=(llm.n_vocab(),)).astype(np.float64))
            best = int(logp.argmax())
            if best in stop_ids:
                break
            top_ids = np.argpartition(logp, -top_k)[-top_k:]
            top_ids = top_ids[np.argsort(logp[top_ids])[::-1]]
            text = piece(best)
            tokens.append(text)
            logprobs.append(float(logp[best]))
            tops.append({piece(int(i)): float(logp[i]) for i in top_ids})
            offsets.append(length)
            length += len(text)
            llm.eval([best])
        return {
            "text": "".join(tokens),
            "tokens": tokens,
            "token_logprobs": logprobs,
            "top_logprobs": tops,
            "text_offset": offsets,
        }

    data = pd.read_csv(test_dataset.path, keep_default_na=False)
    if max_rows > 0:
        data = data.head(max_rows)
    os.makedirs(os.path.dirname(signals.path), exist_ok=True)
    started = time.perf_counter()
    with open(signals.path, "w", encoding="utf-8") as sink:
        for i, row in enumerate(data.itertuples(index=False), start=1):
            prompt = chat_template.format(user=f"{instruction}\n\nTicket:\n{row.ticket}")
            begin = time.perf_counter()
            record = {"row": i - 1, **generate(prompt), "seconds": round(time.perf_counter() - begin, 3)}
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            if i % 20 == 0:
                logger.info("%d/%d tickets, %.0f s", i, len(data), time.perf_counter() - started)
