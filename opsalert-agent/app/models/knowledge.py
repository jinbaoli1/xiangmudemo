from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class KnowledgeEntry(BaseModel):
    id: str
    title: str
    category: str = "troubleshooting"  # troubleshooting, best_practice, runbook, faq
    symptom: str = ""
    root_cause: str = ""
    solution: str = ""
    steps: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

    severity_hint: str = ""  # P0/P1/P2/P3
    duration_hint: str = ""  # typical resolution time
    risk_level: str = "medium"  # low, medium, high

    author: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = 0
    rating: float = 0.0

    references: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)
