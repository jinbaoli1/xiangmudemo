from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    SEV1 = "SEV1"  # 重大事故
    SEV2 = "SEV2"  # 严重事故
    SEV3 = "SEV3"  # 一般事故
    SEV4 = "SEV4"  # 轻微事故


class Incident(BaseModel):
    id: str
    title: str
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.SEV3
    status: IncidentStatus = IncidentStatus.OPEN

    alert_ids: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    affected_hosts: List[str] = Field(default_factory=list)

    root_cause: Optional[str] = None
    root_cause_category: Optional[str] = None
    confidence: Optional[float] = None

    impact_scope: str = ""
    impact_duration_minutes: Optional[int] = None

    assignee: str = ""
    on_call_team: str = ""

    started_at: datetime = Field(default_factory=datetime.now)
    detected_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)
