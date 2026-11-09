from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertLevel(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Alert(BaseModel):
    id: str = Field(..., description="告警唯一ID")
    alert_name: str = Field(..., description="告警名称")
    severity: AlertSeverity = Field(..., description="告警严重程度")
    status: AlertStatus = Field(default=AlertStatus.OPEN, description="告警状态")
    level: Optional[AlertLevel] = Field(None, description="分级后的告警级别 P0-P3")
    level_score: Optional[float] = Field(None, description="分级得分")

    host: str = Field(..., description="告警主机/节点")
    service: str = Field(..., description="所属服务")
    metric_name: str = Field(..., description="触发告警的指标名")
    metric_value: float = Field(..., description="指标当前值")
    threshold: float = Field(..., description="阈值")
    unit: str = Field(default="%", description="单位")

    summary: str = Field(..., description="告警摘要")
    description: Optional[str] = Field(None, description="详细描述")
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")
    annotations: Dict[str, str] = Field(default_factory=dict, description="注解")

    fingerprint: str = Field(..., description="告警指纹，用于去重")
    generator_url: Optional[str] = Field(None, description="产生告警的源地址")

    starts_at: datetime = Field(default_factory=datetime.now, description="告警开始时间")
    ends_at: Optional[datetime] = Field(None, description="告警结束时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    incident_id: Optional[str] = Field(None, description="关联的事故ID")
    ticket_id: Optional[str] = Field(None, description="关联的工单ID")

    tags: List[str] = Field(default_factory=list, description="自定义标签列表")
    extra: Dict[str, Any] = Field(default_factory=dict, description="扩展字段")
