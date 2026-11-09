"""排班数据模型"""
from __future__ import annotations

from datetime import date, time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TimeSlot(str, Enum):
    """时段枚举"""
    MORNING = "morning"  # 上午
    AFTERNOON = "afternoon"  # 下午
    EVENING = "evening"  # 晚间


class ScheduleSlot(BaseModel):
    """单个排班时段"""

    id: str = Field(..., description="排班时段ID")
    doctor_id: str = Field(..., description="医生ID")
    doctor_name: str = Field(..., description="医生姓名")
    department_id: str = Field(..., description="科室ID")
    department_name: str = Field(..., description="科室名称")
    schedule_date: str = Field(..., description="出诊日期 YYYY-MM-DD")
    time_slot: TimeSlot = Field(..., description="时段")
    start_time: str = Field("", description="开始时间 HH:MM")
    end_time: str = Field("", description="结束时间 HH:MM")
    total_quota: int = Field(0, ge=0, description="总号源数")
    remaining_quota: int = Field(0, ge=0, description="剩余号源数")
    consultation_fee: float = Field(0.0, description="挂号费")
    location: str = Field("", description="出诊地点")

    @property
    def is_available(self) -> bool:
        """是否还有号源"""
        return self.remaining_quota > 0


class Schedule(BaseModel):
    """排班信息（医生维度聚合）"""

    doctor_id: str
    doctor_name: str
    department_id: str
    department_name: str
    slots: List[ScheduleSlot] = Field(default_factory=list)
