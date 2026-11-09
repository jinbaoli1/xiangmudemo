"""预约数据模型"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AppointmentStatus(str, Enum):
    """预约状态"""
    PENDING = "pending"          # 待确认
    CONFIRMED = "confirmed"      # 已确认
    CANCELLED = "cancelled"      # 已取消
    COMPLETED = "completed"      # 已完成
    NO_SHOW = "no_show"          # 爽约


class AppointmentCreate(BaseModel):
    """创建预约请求"""

    patient_name: str = Field(..., description="患者姓名", min_length=1)
    patient_phone: str = Field(..., description="患者手机号", min_length=11)
    patient_id_card: str = Field("", description="患者身份证号")
    doctor_id: str = Field(..., description="医生ID")
    schedule_slot_id: str = Field(..., description="排班时段ID")
    symptom_desc: str = Field("", description="症状描述")
    idempotency_key: str = Field(..., description="幂等键，防止重复提交")


class Appointment(BaseModel):
    """预约记录"""

    id: str = Field(..., description="预约ID")
    patient_name: str = Field(..., description="患者姓名")
    patient_phone: str = Field(..., description="患者手机号")
    patient_id_card: str = Field("", description="患者身份证号")
    doctor_id: str = Field(..., description="医生ID")
    doctor_name: str = Field(..., description="医生姓名")
    department_id: str = Field(..., description="科室ID")
    department_name: str = Field(..., description="科室名称")
    schedule_slot_id: str = Field(..., description="排班时段ID")
    schedule_date: str = Field(..., description="就诊日期")
    time_slot: str = Field(..., description="就诊时段")
    consultation_fee: float = Field(0.0, description="挂号费")
    symptom_desc: str = Field("", description="症状描述")
    status: AppointmentStatus = Field(AppointmentStatus.PENDING, description="预约状态")
    idempotency_key: str = Field("", description="幂等键")
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
