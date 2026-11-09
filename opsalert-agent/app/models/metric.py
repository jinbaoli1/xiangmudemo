from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class MetricDataPoint(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)


class Metric(BaseModel):
    id: str
    name: str
    description: str = ""
    unit: str = ""
    category: str = "system"  # system, application, database, network
    host: Optional[str] = None
    service: Optional[str] = None
    current_value: Optional[float] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    data_points: list[MetricDataPoint] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)
