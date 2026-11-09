"""排班服务."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.schemas import Schedule


class ScheduleService:
    """排班服务类."""

    @staticmethod
    def list_by_department(
        department_id: int,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Schedule]:
        """获取科室排班."""
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
                SELECT s.*, d.name as doctor_name, dep.name as department_name
                FROM schedules s
                LEFT JOIN doctors d ON s.doctor_id = d.id
                LEFT JOIN departments dep ON s.department_id = dep.id
                WHERE s.department_id = ?
            """
            params = [department_id]

            if date:
                query += " AND s.date = ?"
                params.append(date)
            elif start_date and end_date:
                query += " AND s.date BETWEEN ? AND ?"
                params.extend([start_date, end_date])

            query += " ORDER BY s.date, s.time_slot, d.rating DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Schedule(**dict(row)) for row in rows]

    @staticmethod
    def list_by_doctor(doctor_id: int, days: int = 14) -> List[Schedule]:
        """获取医生排班."""
        with get_db() as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                """
                SELECT s.*, d.name as doctor_name, dep.name as department_name
                FROM schedules s
                LEFT JOIN doctors d ON s.doctor_id = d.id
                LEFT JOIN departments dep ON s.department_id = dep.id
                WHERE s.doctor_id = ? AND s.date >= ?
                ORDER BY s.date, s.time_slot
                """,
                (doctor_id, today)
            )
            rows = cursor.fetchall()
            return [Schedule(**dict(row)) for row in rows]

    @staticmethod
    def get_by_id(schedule_id: int) -> Optional[Schedule]:
        """根据ID获取排班."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.*, d.name as doctor_name, dep.name as department_name
                FROM schedules s
                LEFT JOIN doctors d ON s.doctor_id = d.id
                LEFT JOIN departments dep ON s.department_id = dep.id
                WHERE s.id = ?
                """,
                (schedule_id,)
            )
            row = cursor.fetchone()
            return Schedule(**dict(row)) if row else None

    @staticmethod
    def check_availability(schedule_id: int) -> bool:
        """检查排班是否还有号源."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT remaining_quota FROM schedules WHERE id = ?",
                (schedule_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            return row["remaining_quota"] > 0

    @staticmethod
    def decrement_quota(schedule_id: int) -> bool:
        """减少号源（预约成功时调用）."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE schedules
                SET remaining_quota = remaining_quota - 1
                WHERE id = ? AND remaining_quota > 0
                """,
                (schedule_id,)
            )
            return cursor.rowcount > 0

    @staticmethod
    def increment_quota(schedule_id: int) -> bool:
        """增加号源（取消预约时调用）."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE schedules
                SET remaining_quota = remaining_quota + 1
                WHERE id = ? AND remaining_quota < total_quota
                """,
                (schedule_id,)
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_available_dates(department_id: int, days: int = 14) -> List[str]:
        """获取科室有号的日期列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                """
                SELECT DISTINCT s.date
                FROM schedules s
                WHERE s.department_id = ? AND s.date >= ? AND s.remaining_quota > 0
                ORDER BY s.date
                LIMIT ?
                """,
                (department_id, today, days)
            )
            rows = cursor.fetchall()
            return [row["date"] for row in rows]
