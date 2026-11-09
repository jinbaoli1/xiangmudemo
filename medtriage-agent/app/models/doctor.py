"""医生数据模型"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Doctor(BaseModel):
    """医生信息"""

    id: str = Field(..., description="医生唯一ID")
    name: str = Field(..., description="医生姓名")
    department_id: str = Field(..., description="所属科室ID")
    department_name: str = Field(..., description="所属科室名称")
    title: str = Field(..., description="职称，如主任医师、副主任医师等")
    specialties: List[str] = Field(default_factory=list, description="专长领域")
    introduction: str = Field("", description="医生简介")
    avatar: str = Field("", description="头像URL")
    rating: float = Field(5.0, ge=0, le=5, description="患者评分")
    review_count: int = Field(0, ge=0, description="评价数量")
    consultation_fee: float = Field(0.0, ge=0, description="挂号费")
    years_of_experience: int = Field(0, ge=0, description="从业年限")
    education: str = Field("", description="最高学历")
    hospital: str = Field("智慧医院", description="所属医院")
