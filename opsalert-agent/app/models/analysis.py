from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .alert import AlertLevel
from .incident import IncidentSeverity


class RootCauseHypothesis(BaseModel):
    id: str
    description: str
    category: str = ""  # network, database, application, infrastructure, configuration
    confidence: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    supporting_metrics: List[str] = Field(default_factory=list)
    supporting_logs: List[str] = Field(default_factory=list)
    related_knowledge_ids: List[str] = Field(default_factory=list)


class RemediationStep(BaseModel):
    order: int
    action: str
    description: str = ""
    estimated_time_minutes: int = 5
    risk_level: str = "low"  # low, medium, high
    rollback_step: str = ""
    automation_available: bool = False
    command: str = ""


class PostmortemReport(BaseModel):
    incident_id: str
    title: str
    summary: str = ""

    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    impact_scope: str = ""
    affected_services: List[str] = Field(default_factory=list)
    affected_users: str = ""

    root_cause: str = ""
    root_cause_category: str = ""
    contributing_factors: List[str] = Field(default_factory=list)

    detection: str = ""
    response_actions: List[str] = Field(default_factory=list)
    resolution: str = ""

    what_went_well: List[str] = Field(default_factory=list)
    what_went_wrong: List[str] = Field(default_factory=list)

    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)

    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: str = "OpsAlert Agent"


class AnalysisResult(BaseModel):
    trace_id: str
    alert_id: str

    level: Optional[AlertLevel] = None
    level_score: Optional[float] = None
    level_reason: str = ""

    incident_id: Optional[str] = None
    incident_severity: Optional[IncidentSeverity] = None

    impact_scope: str = ""
    affected_services: List[str] = Field(default_factory=list)
    affected_upstream: List[str] = Field(default_factory=list)
    affected_downstream: List[str] = Field(default_factory=list)

    root_cause_hypotheses: List[RootCauseHypothesis] = Field(default_factory=list)
    top_root_cause: Optional[RootCauseHypothesis] = None

    remediation_steps: List[RemediationStep] = Field(default_factory=list)
    estimated_fix_time: int = 0

    similar_historical_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    related_knowledge: List[Dict[str, Any]] = Field(default_factory=list)

    ticket_id: Optional[str] = None
    postmortem: Optional[PostmortemReport] = None

    agent_steps: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "pending"  # pending, analyzing, completed, failed
    error_message: Optional[str] = None

    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
