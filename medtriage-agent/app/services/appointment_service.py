"""预约服务."""
from __future__ import annotations

import uuid
from typing import List, Optional
from app.database import get_db
from app.models.schemas import Appointment
from app.services.schedule_service import ScheduleService


class AppointmentService:
    """预约服务类."""

    @staticmethod
    def get_by_id(appointment_id: int) -> Optional[Appointment]:
        """根据ID获取预约."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.*,
                    p.name as patient_name,
                    d.name as doctor_name,
                    dep.name as department_name
                FROM appointments a
                LEFT JOIN patients p ON a.patient_id = p.id
                LEFT JOIN doctors d ON a.doctor_id = d.id
                LEFT JOIN departments dep ON a.department_id = dep.id
                WHERE a.id = ?
                """,
                (appointment_id,)
            )
            row = cursor.fetchone()
            return Appointment(**dict(row)) if row else None

    @staticmethod
    def get_by_idempotency_key(idempotency_key: str) -> Optional[Appointment]:
        """根据幂等键获取预约（用于幂等控制）."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.*,
                    p.name as patient_name,
                    d.name as doctor_name,
                    dep.name as department_name
                FROM appointments a
                LEFT JOIN patients p ON a.patient_id = p.id
                LEFT JOIN doctors d ON a.doctor_id = d.id
                LEFT JOIN departments dep ON a.department_id = dep.id
                WHERE a.idempotency_key = ?
                """,
                (idempotency_key,)
            )
            row = cursor.fetchone()
            return Appointment(**dict(row)) if row else None

    @staticmethod
    def list_by_patient(patient_id: int, limit: int = 20) -> List[Appointment]:
        """获取患者的预约列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.*,
                    p.name as patient_name,
                    d.name as doctor_name,
                    dep.name as department_name
                FROM appointments a
                LEFT JOIN patients p ON a.patient_id = p.id
                LEFT JOIN doctors d ON a.doctor_id = d.id
                LEFT JOIN departments dep ON a.department_id = dep.id
                WHERE a.patient_id = ?
                ORDER BY a.created_at DESC
                LIMIT ?
                """,
                (patient_id, limit)
            )
            rows = cursor.fetchall()
            return [Appointment(**dict(row)) for row in rows]

    @staticmethod
    def create(appointment_data: dict) -> Optional[Appointment]:
        """创建预约（带幂等控制和号源检查）."""
        # 1. 幂等检查
        idempotency_key = appointment_data.get("idempotency_key")
        if idempotency_key:
            existing = AppointmentService.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing  # 直接返回已有预约，幂等

        # 2. 生成幂等键
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())

        schedule_id = appointment_data["schedule_id"]

        # 3. 检查号源并扣减
        with get_db() as conn:
            cursor = conn.cursor()

            # 使用行锁检查并扣减号源
            cursor.execute("BEGIN IMMEDIATE")

            try:
                # 检查号源
                cursor.execute(
                    "SELECT remaining_quota FROM schedules WHERE id = ?",
                    (schedule_id,)
                )
                row = cursor.fetchone()
                if not row or row["remaining_quota"] <= 0:
                    conn.rollback()
                    return None  # 号源不足

                # 扣减号源
                cursor.execute(
                    "UPDATE schedules SET remaining_quota = remaining_quota - 1 WHERE id = ? AND remaining_quota > 0",
                    (schedule_id,)
                )
                if cursor.rowcount == 0:
                    conn.rollback()
                    return None

                # 创建预约记录
                cursor.execute(
                    """
                    INSERT INTO appointments (
                        patient_id, schedule_id, doctor_id, department_id,
                        appointment_date, time_slot, status, symptoms,
                        initial_diagnosis, idempotency_key
                    ) VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?, ?, ?)
                    """,
                    (
                        appointment_data["patient_id"],
                        schedule_id,
                        appointment_data["doctor_id"],
                        appointment_data["department_id"],
                        appointment_data["appointment_date"],
                        appointment_data["time_slot"],
                        appointment_data.get("symptoms"),
                        appointment_data.get("initial_diagnosis"),
                        idempotency_key,
                    )
                )
                appointment_id = cursor.lastrowid
                conn.commit()

                return AppointmentService.get_by_id(appointment_id)

            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def cancel(appointment_id: int) -> bool:
        """取消预约（退还号源）."""
        appointment = AppointmentService.get_by_id(appointment_id)
        if not appointment or appointment.status == "cancelled":
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")

            try:
                # 更新预约状态
                cursor.execute(
                    "UPDATE appointments SET status = 'cancelled' WHERE id = ? AND status != 'cancelled'",
                    (appointment_id,)
                )
                if cursor.rowcount == 0:
                    conn.rollback()
                    return False

                # 退还号源
                cursor.execute(
                    """
                    UPDATE schedules
                    SET remaining_quota = remaining_quota + 1
                    WHERE id = ? AND remaining_quota < total_quota
                    """,
                    (appointment.schedule_id,)
                )

                conn.commit()
                return True

            except Exception:
                conn.rollback()
                raise
