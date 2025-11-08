import asyncio
from asyncio import Queue
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from loguru import logger
from sqlalchemy import select

from sorawm.configs import WORKING_DIR
from sorawm.core import SoraWM
from sorawm.server.db import get_session
from sorawm.server.models import Task
from sorawm.server.schemas import Status, WMRemoveResults


class WMRemoveTaskWorker:
    def __init__(self) -> None:
        self.queue = Queue()
        self.sora_wm = None
        self.initialized = False
        self.initializing = False
        self.initialization_error = None
        self.output_dir = WORKING_DIR
        self.upload_dir = WORKING_DIR / "uploads"
        self.upload_dir.mkdir(exist_ok=True, parents=True)

    async def initialize(self):
        """Initialize models. Can be called asynchronously without blocking server startup."""
        if self.initialized:
            return
        if self.initializing:
            # Wait for ongoing initialization
            while self.initializing:
                await asyncio.sleep(0.1)
            return
        
        self.initializing = True
        try:
            logger.info("Initializing SoraWM models...")
            # Run model loading in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            self.sora_wm = await asyncio.to_thread(SoraWM)
            self.initialized = True
            logger.info("SoraWM models initialized successfully")
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Failed to initialize SoraWM models: {e}")
            raise
        finally:
            self.initializing = False
    
    def is_ready(self) -> bool:
        """Check if worker is ready to process tasks."""
        return self.initialized and self.sora_wm is not None

    async def create_task(self) -> str:
        task_uuid = str(uuid4())
        async with get_session() as session:
            task = Task(
                id=task_uuid,
                video_path="",  # 暂时为空，后续会更新
                status=Status.UPLOADING,
                percentage=0,
            )
            session.add(task)
        logger.info(f"Task {task_uuid} created with UPLOADING status")
        return task_uuid

    async def queue_task(self, task_id: str, video_path: Path):
        async with get_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one()
            task.video_path = str(video_path)
            task.status = Status.PROCESSING
            task.percentage = 0

        self.queue.put_nowait((task_id, video_path))
        logger.info(f"Task {task_id} queued for processing: {video_path}")

    async def mark_task_error(self, task_id: str, error_msg: str):
        async with get_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.status = Status.ERROR
                task.percentage = 0
        logger.error(f"Task {task_id} marked as ERROR: {error_msg}")

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        error_str = str(error).lower()
        # Retryable errors: transient failures, FFmpeg pipe issues, timeouts
        retryable_keywords = [
            "broken pipe",
            "timeout",
            "connection",
            "temporary",
            "retry",
            "ffmpeg process terminated",
            "pipe broken",
        ]
        # Non-retryable errors: file not found, invalid format, model errors
        non_retryable_keywords = [
            "file not found",
            "invalid format",
            "model not available",
            "models failed to initialize",
            "no such file",
        ]
        
        # Check non-retryable first
        for keyword in non_retryable_keywords:
            if keyword in error_str:
                return False
        
        # Check retryable
        for keyword in retryable_keywords:
            if keyword in error_str:
                return True
        
        # Default: retry for unknown errors (might be transient)
        return True

    async def run(self):
        logger.info("Worker started, waiting for tasks...")
        MAX_RETRIES = 3  # Maximum number of retry attempts
        
        while True:
            task_uuid, video_path = await self.queue.get()
            logger.info(f"Processing task {task_uuid}: {video_path}")

            # Wait for models to be initialized before processing
            if not self.is_ready():
                logger.warning(f"Models not ready yet, waiting for initialization...")
                # Wait for initialization to complete
                while not self.is_ready() and self.initialization_error is None:
                    await asyncio.sleep(1)
                
                if self.initialization_error:
                    logger.error(f"Cannot process task {task_uuid}: Models failed to initialize: {self.initialization_error}")
                    await self.mark_task_error(task_uuid, f"Models not available: {self.initialization_error}")
                    self.queue.task_done()
                    continue

            # Retry loop
            retry_count = 0
            success = False
            
            while retry_count <= MAX_RETRIES and not success:
                try:
                    if retry_count > 0:
                        wait_time = min(2 ** retry_count, 60)  # Exponential backoff, max 60 seconds
                        logger.info(f"Retrying task {task_uuid} (attempt {retry_count + 1}/{MAX_RETRIES + 1}) after {wait_time}s wait...")
                        await asyncio.sleep(wait_time)
                    
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    file_suffix = video_path.suffix
                    output_filename = f"{task_uuid}_{timestamp}{file_suffix}"
                    output_path = self.output_dir / output_filename

                    async with get_session() as session:
                        result = await session.execute(
                            select(Task).where(Task.id == task_uuid)
                        )
                        task = result.scalar_one()
                        task.status = Status.PROCESSING
                        task.percentage = 10
                        task.retry_count = retry_count  # Update retry count
                        task.error_message = None  # Clear previous error

                    loop = asyncio.get_event_loop()

                    def progress_callback(percentage: int):
                        asyncio.run_coroutine_threadsafe(
                            self._update_progress(task_uuid, percentage), loop
                        )

                    await asyncio.to_thread(
                        self.sora_wm.run, video_path, output_path, progress_callback
                    )

                    async with get_session() as session:
                        result = await session.execute(
                            select(Task).where(Task.id == task_uuid)
                        )
                        task = result.scalar_one()
                        task.status = Status.FINISHED
                        task.percentage = 100
                        task.output_path = str(output_path)
                        task.download_url = f"/download/{task_uuid}"
                        task.error_message = None
                        task.retry_count = retry_count  # Keep retry count for reference

                    logger.info(
                        f"Task {task_uuid} completed successfully on attempt {retry_count + 1}, output: {output_path}"
                    )
                    success = True

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error processing task {task_uuid} (attempt {retry_count + 1}): {error_msg}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Check if error is retryable
                    is_retryable = self._is_retryable_error(e)
                    
                    async with get_session() as session:
                        result = await session.execute(
                            select(Task).where(Task.id == task_uuid)
                        )
                        task = result.scalar_one()
                        task.retry_count = retry_count + 1
                        task.error_message = error_msg
                        
                        if not is_retryable or retry_count >= MAX_RETRIES:
                            # Non-retryable error or max retries reached
                            task.status = Status.ERROR
                            task.percentage = 0
                            if retry_count >= MAX_RETRIES:
                                task.error_message = f"{error_msg} (Failed after {MAX_RETRIES + 1} attempts)"
                            logger.error(
                                f"Task {task_uuid} failed permanently: {error_msg}"
                            )
                            break
                        else:
                            # Retryable error, will retry
                            task.status = Status.PROCESSING  # Keep as processing for retry
                            logger.warning(
                                f"Task {task_uuid} will be retried (attempt {retry_count + 1}/{MAX_RETRIES + 1}): {error_msg}"
                            )
                    
                    retry_count += 1
                    # Continue to retry loop

            self.queue.task_done()

    async def _update_progress(self, task_id: str, percentage: int):
        try:
            async with get_session() as session:
                result = await session.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    task.percentage = percentage
                    logger.debug(f"Task {task_id} progress updated to {percentage}%")
        except Exception as e:
            logger.error(f"Error updating progress for task {task_id}: {e}")

    async def get_task_status(self, task_id: str) -> WMRemoveResults | None:
        async with get_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task is None:
                return None
            return WMRemoveResults(
                percentage=task.percentage,
                status=Status(task.status),
                download_url=task.download_url,
                error_message=task.error_message,  # Include error message
                retry_count=task.retry_count,  # Include retry count
            )

    async def get_output_path(self, task_id: str) -> Path | None:
        async with get_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task is None or task.output_path is None:
                return None
            return Path(task.output_path)


worker = WMRemoveTaskWorker()
