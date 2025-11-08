# CUDA + PyTorch + Python
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# FFmpeg for video io
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
# build from your fork (RunPod will clone your repo), so just copy everything
COPY . /app

# use uv (project has uv.lock) to install exact deps
RUN pip install --no-cache-dir uv && \
    uv sync --frozen
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# cache model weights on a mounted volume
ENV TORCH_HOME=/models \
    HF_HOME=/models/hf \
    HUGGINGFACE_HUB_CACHE=/models/hf

RUN mkdir -p /models

# the repo's FastAPI app starts on port 5344
EXPOSE 5344
CMD ["python", "start_server.py"]
