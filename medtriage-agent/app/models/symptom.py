"""症状与分诊数据模型"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """病情严重程度"""
    LOW = "low"        # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"      # 高风险 - 需立即就医
    CRITICAL = "critical"  # 危急 - 立即拨打120


class TriageDepartment(BaseModel):
    """分诊结果中的科室项"""

    department_id: str = Field(..., description="科室ID")
    department_name: str = Field(..., description="科室名称")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    reason: str = Field("", description="匹配原因")
    is_emergency: bool = Field(False, description="是否急诊")


class TriageResult(BaseModel):
    """分诊结果"""

    symptoms: List[str] = Field(default_factory=list, description="识别出的症状")
    severity: SeverityLevel = Field(SeverityLevel.LOW, description="严重程度")
    severity_reason: str = Field("", description="严重程度判断依据")
    departments: List[TriageDepartment] = Field(default_factory=list, description="推荐科室列表（按置信度排序）")
    suggestions: List[str] = Field(default_factory=list, description="就诊建议")
    needs_emergency: bool = Field(False, description="是否需要急诊")


class SymptomRecord(BaseModel):
    """症状采集记录"""

    session_id: str = Field(..., description="会话ID")
    patient_age: Optional[int] = Field(None, description="患者年龄")
    patient_gender: Optional[str] = Field(None, description="患者性别")
    symptoms: List[str] = Field(default_factory=list, description="症状列表")
    symptom_description: str = Field("", description="原始症状描述")
    duration: str = Field("", description="持续时间")
    severity_desc: str = Field("", description="疼痛/严重程度描述")
    medical_history: List[str] = Field(default_factory=list, description="既往病史")
    extra_info: Dict[str, Any] = Field(default_factory=dict, description="额外信息")
