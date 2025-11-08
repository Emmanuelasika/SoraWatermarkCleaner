# Network Volume Setup for RunPod

## Overview

With a network volume attached, models are stored persistently and **don't need to be downloaded every time** the worker starts. This dramatically reduces startup time from 10-30 minutes to just a few seconds!

## Network Volume Configuration

### 1. Mount Point

The network volume should be mounted at `/models` in your RunPod endpoint configuration.

### 2. What Gets Stored on Network Volume

All models are stored on the network volume:

- **YOLO weights** (`best.pt`) → `/models/best.pt`
- **LAMA model** (`big-lama.pt`) → `/models/.cache/torch/hub/checkpoints/big-lama.pt` (via `TORCH_HOME`)
- **HuggingFace models** (if any) → `/models/hf/` (via `HF_HOME`)

### 3. Environment Variables

The Dockerfile sets these environment variables to use the network volume:

```dockerfile
ENV MODELS_DIR=/models \
    TORCH_HOME=/models \
    HF_HOME=/models/hf \
    HUGGINGFACE_HUB_CACHE=/models/hf \
    TRANSFORMERS_CACHE=/models/hf \
    XDG_CACHE_HOME=/models/.cache
```

## How It Works

### First Startup (Models Not Cached)

1. Server starts immediately (database init only)
2. `/ping` responds right away
3. Models download in background:
   - YOLO: Downloads to `/models/best.pt`
   - LAMA: Downloads to `/models/.cache/torch/hub/checkpoints/big-lama.pt`
4. Takes 10-30 minutes (one time only)

### Subsequent Startups (Models Cached)

1. Server starts immediately
2. `/ping` responds right away
3. Models load from network volume (already downloaded)
4. **Takes only seconds!** ⚡

## Model Download Logic

### YOLO Weights

- **Location**: `/models/best.pt` (or `/app/resources/best.pt` if network volume not mounted)
- **Check**: `download_detector_weights()` checks if file exists before downloading
- **Update**: Only downloads if hash mismatch detected

### LAMA Model

- **Location**: `/models/.cache/torch/hub/checkpoints/big-lama.pt`
- **Check**: `is_downloaded()` checks if file exists
- **Download**: Only downloads if not found

## Verification

After first startup, check if models are on network volume:

```bash
# Check YOLO weights
ls -lh /models/best.pt

# Check LAMA model
ls -lh /models/.cache/torch/hub/checkpoints/big-lama.pt

# Check HuggingFace cache
ls -lh /models/hf/
```

## Benefits

✅ **Fast startup** - Models load from network volume in seconds
✅ **No re-downloads** - Models persist across worker restarts
✅ **Cost savings** - No bandwidth costs for re-downloading
✅ **Reliability** - Models available even if worker crashes

## Troubleshooting

### Models Still Downloading Every Time

**Check:**
1. Is network volume mounted at `/models`?
2. Are models actually on the volume? (`ls /models`)
3. Are environment variables set correctly?

**Solution:**
- Verify network volume is mounted in RunPod endpoint settings
- Check that `/models` directory exists and is writable
- Verify models were downloaded to network volume on first run

### Models Not Found

**Check:**
1. Does `/models` directory exist?
2. Are files readable?
3. Are permissions correct?

**Solution:**
- Ensure network volume is properly mounted
- Check file permissions: `chmod -R 755 /models`
- Verify models downloaded successfully on first run

### Fallback Behavior

If network volume is not mounted:
- Models will download to `/app/resources/` (container filesystem)
- Models will be lost when container restarts
- Will need to re-download each time

## Configuration

The code automatically detects if network volume is mounted:

```python
# In sorawm/configs.py
MODELS_DIR = Path(os.getenv("MODELS_DIR", "/models"))
if not MODELS_DIR.exists():
    # Fallback to local resources if network volume not mounted
    MODELS_DIR = ROOT / "resources"
```

This ensures the code works both with and without network volumes.

## Next Steps

1. **Deploy with network volume mounted at `/models`**
2. **First startup**: Wait for models to download (10-30 min)
3. **Subsequent startups**: Models load instantly from network volume!
4. **Verify**: Check `/models` directory contains model files

Enjoy fast startup times! 🚀

