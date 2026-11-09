from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class LogEntry(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    host: str
    service: str
    source: str = ""  # log file path or source name
    level: LogLevel = LogLevel.INFO
    message: str
    trace_id: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
