# CUDA + PyTorch runtime
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# System deps (FFmpeg is required by the repo)
# This layer is cached unless system deps change
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Install pip and uv first (cached unless these change)
RUN pip install -U pip uv

# App - Copy dependency files first for better caching
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install Python deps (cached unless dependencies change)
RUN uv sync --frozen

# Copy application code last (changes most frequently)
# This layer is rebuilt only when code changes, not dependencies
COPY . /app

# Make sure the container actually runs the uv-created venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Model caches — safe default. If you mount a Network Volume, mount it at /models.
# All models (YOLO, LAMA, HuggingFace) will be stored on the network volume
ENV MODELS_DIR=/models \
    TORCH_HOME=/models \
    HF_HOME=/models/hf \
    HUGGINGFACE_HUB_CACHE=/models/hf \
    TRANSFORMERS_CACHE=/models/hf \
    XDG_CACHE_HOME=/models/.cache
# Create directory structure (will use network volume if mounted)
RUN mkdir -p /models /models/hf /models/.cache /app/resources

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
