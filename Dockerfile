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

# Add a tiny wrapper that imports the repo's FastAPI app and adds /ping for LB health checks.
# (RunPod LB expects GET /ping on PORT_HEALTH.) 
RUN printf '%s\n' \
'from fastapi import FastAPI' \
'try:' \
'    from start_server import app as real_app' \
'except Exception as e:' \
'    real_app = FastAPI()' \
'    @real_app.get("/")' \
'    def _root(): return {"error":"failed to import app","detail":str(e)}' \
'' \
'app = real_app' \
'' \
'@app.get("/ping")' \
'def ping():' \
'    return {"status":"healthy"}' \
> /app/_serve.py

# Expose the repo's port
EXPOSE 5344

# Helpful defaults for RunPod Load Balancer
ENV PORT=5344
ENV PORT_HEALTH=5344

# Start the server (use -u for unbuffered logs)
CMD ["python", "-u", "-m", "uvicorn", "_serve:app", "--host", "0.0.0.0", "--port", "5344"]
