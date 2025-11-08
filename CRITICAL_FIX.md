# Critical Fix for RunPod Deployment

## Problem Identified

The server was **blocking on model initialization** before starting, which caused:

1. **Server never starts** until models are downloaded (can take 10-30+ minutes)
2. **RunPod health checks timeout** - `/ping` endpoint not accessible
3. **Workers get killed** - RunPod thinks they're dead
4. **Builds take forever** - Server appears to hang

## Solution Implemented

### 1. Background Model Loading (`sorawm/server/lifespan.py`)
- Models now load **asynchronously in the background**
- Server starts **immediately** after database initialization
- `/ping` endpoint responds right away

### 2. Non-Blocking Initialization (`sorawm/server/worker.py`)
- Added `initialized`, `initializing`, and `initialization_error` flags
- Model loading happens in a thread pool (doesn't block event loop)
- Worker queue waits for models before processing tasks

### 3. Immediate Health Checks (`_serve.py`)
- `/ping` endpoint responds immediately with status:
  - `{"status": "healthy", "models_ready": true}` - Fully ready
  - `{"status": "healthy", "models_ready": false, "models_loading": true}` - Still loading
  - `{"status": "degraded", ...}` - Error loading models

### 4. Graceful Task Handling (`sorawm/server/router.py`)
- Tasks can be submitted even while models are loading
- Tasks wait in queue until models are ready
- Clear error messages if model loading fails

## Key Changes

### Before (BLOCKING):
```python
async def lifespan(app: FastAPI):
    await init_db()
    await worker.initialize()  # BLOCKS for 10-30 minutes!
    # Server doesn't start until here
```

### After (NON-BLOCKING):
```python
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(worker.initialize())  # Background
    # Server starts immediately!
```

## Expected Behavior Now

1. **Server starts in < 10 seconds** (database init only)
2. **`/ping` responds immediately** with `{"status": "healthy"}`
3. **RunPod health checks pass** - workers marked as healthy
4. **Models load in background** - takes 10-30 minutes but doesn't block
5. **Tasks can be submitted** - they wait for models if needed

## Testing

After redeploying, you should see in logs:

```
Starting up...
Database initialized
Starting model loading in background...
Application started successfully (models loading in background)
Starting server on 0.0.0.0:5344
```

Then `/ping` will respond immediately, even while you see:
```
Initializing SoraWM models...
[Downloading models...]
SoraWM models initialized successfully
```

## Why This Will Work

1. ✅ **Fast startup** - Only database init blocks (milliseconds)
2. ✅ **Immediate health checks** - `/ping` responds right away
3. ✅ **RunPod won't kill workers** - Health checks pass
4. ✅ **Models load safely** - In background thread pool
5. ✅ **Tasks handled correctly** - Queue waits for models

## Next Steps

1. **Rebuild Docker image** with these changes
2. **Redeploy to RunPod**
3. **Wait 30-60 seconds** for server to start
4. **Test `/ping`** - should respond immediately
5. **Wait 10-30 minutes** for models to finish loading
6. **Submit a test task** - should process when models ready

This fix addresses the root cause: **server blocking on model downloads**. Now the server starts immediately and models load asynchronously.

