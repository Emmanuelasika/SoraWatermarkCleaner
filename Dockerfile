FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Install deps (uv lock if present, else requirements.txt)
RUN pip install --no-cache-dir uv && uv sync --frozen || \
    pip install --no-cache-dir -r requirements.txt

# Always write caches to /models (works even if it's just ephemeral)
ENV TORCH_HOME=/models \
    HF_HOME=/models/hf \
    HUGGINGFACE_HUB_CACHE=/models/hf \
    TRANSFORMERS_CACHE=/models/hf \
    XDG_CACHE_HOME=/models/.cache
RUN mkdir -p /models /models/hf /models/.cache

EXPOSE 5344
CMD ["python", "start_server.py"]
