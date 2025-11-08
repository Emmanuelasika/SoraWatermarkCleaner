# RunPod Deployment Guide for SoraWatermarkCleaner

## Overview

This guide explains the fixes made for RunPod Load Balancer deployment and how to troubleshoot common issues.

## Changes Made

### 1. Created `_serve.py` Entry Point

The main issue was that the Dockerfile was trying to import an `app` object from `start_server.py`, which doesn't exist. The `start_server.py` file uses the Fire library and doesn't export an `app` object directly.

**Solution**: Created a new `_serve.py` file that:
- Properly imports and initializes the FastAPI app using `init_app()` from `sorawm.server.app`
- Adds the `/ping` endpoint required by RunPod's load balancer
- Reads the `PORT` environment variable (set by RunPod)
- Includes proper error handling and logging

### 2. Updated Dockerfile

**Previous Issue**: The Dockerfile was using `printf` to create a Python file inline, which was error-prone and tried to import from the wrong module.

**Solution**: 
- Removed the inline `printf` command
- Use the `_serve.py` file directly (copied from the repo)
- Simplified the CMD to run `python -u _serve.py`
- Set proper environment variables for PORT and HOST

## RunPod Requirements

According to RunPod's documentation, your worker needs:
1. **HTTP server** running on the port specified in the `PORT` environment variable
2. **`/ping` endpoint** accessible for health checks (typically on the same port)

The current implementation serves both the main API and health checks on the same port (`PORT`), which is the standard approach.

## Endpoints

- `GET /ping` - Health check endpoint (returns `{"status": "healthy"}`)
- `GET /` - Root endpoint with API information
- `POST /submit_remove_task` - Submit a video for watermark removal
- `GET /get_results` - Get task status and results
- `GET /download/{task_id}` - Download processed video
- `GET /docs` - FastAPI interactive documentation

## Troubleshooting

### Issue: 400 Bad Request on `/ping`

**Symptoms**: 
- Ping requests return 400 Bad Request
- Workers exit with error codes 1 or 2
- Logs show "unrecognized arguments" errors

**Solution**:
1. Ensure `_serve.py` is in the repository root
2. Verify the Dockerfile is using the correct CMD: `["python", "-u", "_serve.py"]`
3. Check that all dependencies are installed correctly
4. Verify models are downloaded (they should download automatically on first run)

### Issue: Workers Not Starting

**Symptoms**:
- Workers show as "Initializing" but never become ready
- Logs show model loading errors

**Solution**:
1. Check that the network volume is properly mounted at `/models` (if using one)
2. Verify disk space is sufficient for model downloads
3. Check logs for specific model download errors
4. Ensure GPU is available and CUDA is working

### Issue: Health Check Timeout

**Symptoms**:
- Health checks fail due to timeout
- Server takes too long to start

**Solution**:
1. The `/ping` endpoint is lightweight and should respond quickly
2. If models are still loading, the server won't start (by design with FastAPI lifespan)
3. Consider pre-downloading models in the Docker image if startup time is critical
4. Check that database initialization isn't blocking

## Environment Variables

RunPod sets these automatically:
- `PORT` - Port for the main HTTP server (default: 5344)
- `PORT_HEALTH` - Port for health checks (typically same as PORT)
- `HOST` - Host to bind to (default: 0.0.0.0)

## Testing Locally

To test the server locally before deploying:

```bash
# Build the Docker image
docker build -t sorawm-runpod .

# Run the container
docker run -p 5344:5344 -e PORT=5344 sorawm-runpod

# Test the ping endpoint
curl http://localhost:5344/ping

# Should return: {"status":"healthy"}
```

## Model Downloads

Models are automatically downloaded on first startup:
- **YOLO weights**: Downloaded to `resources/best.pt`
- **LAMA model**: Downloaded to torch cache directory

If using a RunPod Network Volume, mount it at `/models` to persist models between restarts.

## Next Steps

1. **Rebuild your Docker image** with the updated Dockerfile
2. **Redeploy to RunPod** with the new image
3. **Monitor logs** to ensure the server starts correctly
4. **Test the `/ping` endpoint** once the worker is ready

If you continue to experience issues, check the RunPod logs for specific error messages and ensure all dependencies are correctly installed.

