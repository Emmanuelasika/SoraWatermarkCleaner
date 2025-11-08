import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from sorawm.server.db import init_db
from sorawm.server.worker import worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    # Initialize database first (fast)
    await init_db()
    logger.info("Database initialized")

    # Start model loading in background (don't block server startup)
    # This allows the /ping endpoint to respond immediately for health checks
    logger.info("Starting model loading in background...")
    model_loading_task = asyncio.create_task(worker.initialize())
    
    # Start worker task queue handler
    worker_task = asyncio.create_task(worker.run())

    logger.info("Application started successfully (models loading in background)")

    yield

    logger.info("Shutting down...")
    # Cancel background tasks
    model_loading_task.cancel()
    worker_task.cancel()
    try:
        await asyncio.gather(model_loading_task, worker_task, return_exceptions=True)
    except Exception:
        pass
    logger.info("Application shutdown complete")
