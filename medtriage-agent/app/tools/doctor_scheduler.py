"""医生排班查询工具."""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from app.services.doctor_service import DoctorService
from app.services.schedule_service import ScheduleService


class DoctorSchedulerTool:
    """医生排班查询工具.

    功能：
    1. 根据科室推荐医生（综合专长、评分、经验、排班）
    2. 查询医生排班信息
    3. 查询号源余量
    """

    name = "doctor_scheduler"
    description = "根据科室推荐医生，查询排班和号源情况"

    def __init__(self):
        self.doctor_service = DoctorService()
        self.schedule_service = ScheduleService()

    def recommend_doctors(
        self,
        department_id: int,
        specialty: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """推荐医生并返回排班信息.

        Args:
            department_id: 科室ID
            specialty: 专长关键词
            limit: 返回数量

        Returns:
            推荐医生列表及排班信息
        """
        # 1. 推荐医生
        doctors = self.doctor_service.recommend_doctors(
            department_id=department_id,
            specialty=specialty,
            limit=limit,
        )

        # 2. 查询每个医生的排班
        doctor_list = []
        for doc in doctors:
            schedules = self.schedule_service.list_by_doctor(doc.id, days=7)
            # 统计有号的天数
            available_days = sum(
                1 for s in schedules if s.remaining_quota > 0
            )

            doctor_list.append({
                "doctor_id": doc.id,
                "doctor_name": doc.name,
                "title": doc.title,
                "specialty": doc.specialty,
                "rating": doc.rating,
                "experience_years": doc.experience_years,
                "consultation_count": doc.consultation_count,
                "department_name": doc.department_name,
                "available_days": available_days,
                "schedules": [
                    {
                        "schedule_id": s.id,
                        "date": s.date,
                        "time_slot": s.time_slot,
                        "remaining_quota": s.remaining_quota,
                        "total_quota": s.total_quota,
                        "fee": s.fee,
                    }
                    for s in schedules[:7]  # 最多返回7天排班
                ],
            })

        return {
            "department_id": department_id,
            "doctors": doctor_list,
            "total_count": len(doctor_list),
        }

    def get_schedule_detail(self, schedule_id: int) -> Dict[str, Any]:
        """获取排班详情."""
        schedule = self.schedule_service.get_by_id(schedule_id)
        if not schedule:
            return {"found": False, "schedule": None}

        return {
            "found": True,
            "schedule": {
                "schedule_id": schedule.id,
                "doctor_id": schedule.doctor_id,
                "doctor_name": schedule.doctor_name,
                "department_id": schedule.department_id,
                "department_name": schedule.department_name,
                "date": schedule.date,
                "time_slot": schedule.time_slot,
                "total_quota": schedule.total_quota,
                "remaining_quota": schedule.remaining_quota,
                "fee": schedule.fee,
                "available": schedule.remaining_quota > 0,
            }
        }

    def get_department_schedules(
        self,
        department_id: int,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取科室排班列表."""
        schedules = self.schedule_service.list_by_department(department_id, date=date)

        schedule_list = [
            {
                "schedule_id": s.id,
                "doctor_id": s.doctor_id,
                "doctor_name": s.doctor_name,
                "date": s.date,
                "time_slot": s.time_slot,
                "remaining_quota": s.remaining_quota,
                "total_quota": s.total_quota,
                "fee": s.fee,
                "available": s.remaining_quota > 0,
            }
            for s in schedules
        ]

        return {
            "department_id": department_id,
            "schedules": schedule_list,
            "total_count": len(schedule_list),
        }
