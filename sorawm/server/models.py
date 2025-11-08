from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from sorawm.server.db import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    video_path: Mapped[str] = mapped_column(String, nullable=False)
    output_path: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PROCESSING")
    percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    download_url: Mapped[str] = mapped_column(String, nullable=True)
    error_message: Mapped[str] = mapped_column(String, nullable=True)  # Store error messages
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Track retry attempts
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
