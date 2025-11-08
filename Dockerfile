# CUDA + PyTorch runtime
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# System deps (FFmpeg is required by the repo)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# App
WORKDIR /app
COPY . /app

# Install Python deps using uv (repo has pyproject.toml + uv.lock)
# Fall back to requirements.txt if needed.
RUN pip install -U pip uv && \
    (uv sync --frozen || pip install --no-cache-dir -r requirements.txt)

# Make sure the container actually runs the uv-created venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Model caches — safe default. If you mount a Network Volume, mount it at /models.
ENV TORCH_HOME=/models \
    HF_HOME=/models/hf \
    HUGGINGFACE_HUB_CACHE=/models/hf \
    TRANSFORMERS_CACHE=/models/hf \
    XDG_CACHE_HOME=/models/.cache
RUN mkdir -p /models /models/hf /models/.cache

# Expose the repo's port
EXPOSE 5344

# Helpful defaults for RunPod Load Balancer
# RunPod will set PORT and PORT_HEALTH environment variables
# We serve the main API and health checks on the same port (PORT)
ENV PORT=5344
ENV PORT_HEALTH=5344
ENV HOST=0.0.0.0

# Start the server using the _serve.py entry point
# The _serve.py file is included in the repo and properly initializes the app
CMD ["python", "-u", "_serve.py"]
