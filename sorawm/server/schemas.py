from enum import StrEnum

from pydantic import BaseModel


class Status(StrEnum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class WMRemoveResults(BaseModel):
    percentage: int
    status: Status
    download_url: str | None = None
    error_message: str | None = None  # Include error message in response
    retry_count: int | None = None  # Include retry count in response
