"""预约挂号工具."""
from __future__ import annotations

from typing import Dict, Any, Optional
from app.services.appointment_service import AppointmentService
from app.services.schedule_service import ScheduleService
from app.services.patient_service import PatientService


class AppointmentBookingTool:
    """预约挂号工具.

    功能：
    1. 查询排班余量
    2. 创建预约
    3. 幂等控制
    4. 取消预约
    """

    name = "appointment_booking"
    description = "预约挂号工具，支持查询号源、创建预约、取消预约"

    def __init__(self):
        self.appointment_service = AppointmentService()
        self.schedule_service = ScheduleService()
        self.patient_service = PatientService()

    def check_availability(self, schedule_id: int) -> Dict[str, Any]:
        """检查号源可用性."""
        schedule = self.schedule_service.get_by_id(schedule_id)
        if not schedule:
            return {
                "available": False,
                "reason": "排班不存在",
                "schedule": None,
            }

        return {
            "available": schedule.remaining_quota > 0,
            "remaining_quota": schedule.remaining_quota,
            "total_quota": schedule.total_quota,
            "doctor_name": schedule.doctor_name,
            "department_name": schedule.department_name,
            "date": schedule.date,
            "time_slot": schedule.time_slot,
            "fee": schedule.fee,
        }

    def book_appointment(
        self,
        schedule_id: int,
        patient_id: int,
        symptoms: Optional[str] = None,
        initial_diagnosis: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建预约.

        Args:
            schedule_id: 排班ID
            patient_id: 患者ID
            symptoms: 症状描述
            initial_diagnosis: 初步诊断
            idempotency_key: 幂等键

        Returns:
            预约结果
        """
        # 1. 获取排班信息
        schedule = self.schedule_service.get_by_id(schedule_id)
        if not schedule:
            return {
                "success": False,
                "error": "排班不存在",
                "appointment": None,
            }

        # 2. 检查患者
        patient = self.patient_service.get_by_id(patient_id)
        if not patient:
            return {
                "success": False,
                "error": "患者不存在",
                "appointment": None,
            }

        # 3. 创建预约
        appointment = self.appointment_service.create({
            "schedule_id": schedule_id,
            "patient_id": patient_id,
            "doctor_id": schedule.doctor_id,
            "department_id": schedule.department_id,
            "appointment_date": schedule.date,
            "time_slot": schedule.time_slot,
            "symptoms": symptoms,
            "initial_diagnosis": initial_diagnosis,
            "idempotency_key": idempotency_key,
        })

        if not appointment:
            return {
                "success": False,
                "error": "号源不足或预约失败",
                "appointment": None,
            }

        return {
            "success": True,
            "message": "预约成功",
            "appointment": {
                "appointment_id": appointment.id,
                "patient_name": appointment.patient_name,
                "doctor_name": appointment.doctor_name,
                "department_name": appointment.department_name,
                "date": appointment.appointment_date,
                "time_slot": appointment.time_slot,
                "status": appointment.status,
            },
        }

    def cancel_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """取消预约."""
        result = self.appointment_service.cancel(appointment_id)
        if result:
            return {
                "success": True,
                "message": "预约已取消，号源已退还",
            }
        else:
            return {
                "success": False,
                "error": "取消失败，预约可能不存在或已取消",
            }

    def get_appointment(self, appointment_id: int) -> Dict[str, Any]:
        """查询预约详情."""
        appointment = self.appointment_service.get_by_id(appointment_id)
        if not appointment:
            return {"found": False, "appointment": None}

        return {
            "found": True,
            "appointment": {
                "appointment_id": appointment.id,
                "patient_name": appointment.patient_name,
                "doctor_name": appointment.doctor_name,
                "department_name": appointment.department_name,
                "date": appointment.appointment_date,
                "time_slot": appointment.time_slot,
                "status": appointment.status,
                "symptoms": appointment.symptoms,
                "initial_diagnosis": appointment.initial_diagnosis,
                "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
            },
        }

    def list_patient_appointments(self, patient_id: int, limit: int = 10) -> Dict[str, Any]:
        """获取患者预约列表."""
        appointments = self.appointment_service.list_by_patient(patient_id, limit=limit)
        return {
            "patient_id": patient_id,
            "appointments": [
                {
                    "appointment_id": a.id,
                    "doctor_name": a.doctor_name,
                    "department_name": a.department_name,
                    "date": a.appointment_date,
                    "time_slot": a.time_slot,
                    "status": a.status,
                }
                for a in appointments
            ],
            "total_count": len(appointments),
        }
