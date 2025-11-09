# CUDA + PyTorch runtime
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# System deps (FFmpeg with libx264 codec support is required by the repo)
# Install FFmpeg static build with all codecs including libx264
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    xz-utils \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && cd /tmp \
    && wget -q https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz \
    && tar -xf ffmpeg-git-amd64-static.tar.xz \
    && mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe \
    && rm -rf ffmpeg-*-amd64-static* ffmpeg-git-amd64-static.tar.xz \
    && ffmpeg -version \
    && ffmpeg -codecs 2>&1 | grep -q "libx264" || echo "WARNING: libx264 not found"

# Install uv
RUN pip install -U pip uv

# Setup app
WORKDIR /app
COPY . /app

# Install dependencies
RUN uv sync

# Make sure the container uses the uv-created venv
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
