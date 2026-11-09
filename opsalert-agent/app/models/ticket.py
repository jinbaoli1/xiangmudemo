from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"


class Ticket(BaseModel):
    id: str
    title: str
    description: str = ""
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM

    incident_id: Optional[str] = None
    alert_id: Optional[str] = None

    assignee: str = ""
    reporter: str = ""
    components: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)

    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    resolution: Optional[str] = None
    comments: List[Dict[str, Any]] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)
