FROM ghcr.io/ggml-org/llama.cpp:server-b5974
ARG MODEL_MD5=b23b4f3092c9083c1c741551ec351dc8
COPY model-q4.gguf /models/model-q4.gguf
RUN echo "${MODEL_MD5}  /models/model-q4.gguf" | md5sum -c -
