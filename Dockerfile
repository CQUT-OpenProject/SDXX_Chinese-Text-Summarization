FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/workspace/.cache/huggingface

WORKDIR /workspace

# PyTorch supports CPU on Apple Silicon; CUDA support depends on the host and image architecture.
RUN pip install --no-cache-dir torch==2.6.0 transformers==4.57.6 datasets==3.6.0 accelerate==1.15.0 sentencepiece==0.2.0
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY configs ./configs
COPY tests ./tests

CMD ["summarizer", "--help"]
