"""
RunPod server entry point for SoraWatermarkCleaner.

This file initializes the FastAPI app and adds the /ping endpoint
required by RunPod's load balancer for health checks.

RunPod Load Balancer Requirements:
- HTTP server on PORT environment variable
- /ping endpoint accessible (typically on same port as main server)
"""
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from sorawm.server.app import init_app
except Exception as e:
    print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize the FastAPI app
try:
    app = init_app()
    print("✓ FastAPI app initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)


# Add /ping endpoint for RunPod health checks
# This endpoint should return 200 OK quickly without heavy operations
# It responds immediately even if models are still loading
@app.get("/ping")
def ping():
    """Health check endpoint for RunPod load balancer."""
    from sorawm.server.worker import worker
    if worker.is_ready():
        return {"status": "healthy", "models_ready": True}
    elif worker.initializing:
        return {"status": "healthy", "models_ready": False, "models_loading": True}
    elif worker.initialization_error:
        return {"status": "degraded", "models_ready": False, "error": worker.initialization_error}
    else:
        return {"status": "healthy", "models_ready": False, "models_loading": False}


# Add root endpoint for basic connectivity check
@app.get("/")
def root():
    """Root endpoint for basic connectivity check."""
    return {
        "status": "running",
        "service": "SoraWatermarkCleaner",
        "endpoints": {
            "ping": "/ping",
            "submit_task": "/submit_remove_task",
            "get_results": "/get_results",
            "download": "/download/{task_id}",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn

    # Read port from environment variable (RunPod sets PORT)
    # RunPod Load Balancer expects server on PORT
    port = int(os.getenv("PORT", "5344"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("=" * 60)
    print("SoraWatermarkCleaner Server")
    print("=" * 60)
    print(f"Starting server on {host}:{port}")
    print(f"Health check endpoint: http://{host}:{port}/ping")
    print(f"API documentation: http://{host}:{port}/docs")
    print("=" * 60)
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=75,  # Increase timeout for long-running requests
        )
    except Exception as e:
        print(f"ERROR: Server failed to start: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

