"""患者服务."""
from __future__ import annotations

from typing import Optional
from app.database import get_db
from app.models.schemas import Patient


class PatientService:
    """患者服务类."""

    @staticmethod
    def get_by_id(patient_id: int) -> Optional[Patient]:
        """根据ID获取患者."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            row = cursor.fetchone()
            return Patient(**dict(row)) if row else None

    @staticmethod
    def get_by_phone(phone: str) -> Optional[Patient]:
        """根据手机号获取患者."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE phone = ?", (phone,))
            row = cursor.fetchone()
            return Patient(**dict(row)) if row else None

    @staticmethod
    def create(patient_data: dict) -> Patient:
        """创建患者档案."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO patients (name, gender, age, phone, id_card, allergies, medical_history)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_data.get("name"),
                    patient_data.get("gender"),
                    patient_data.get("age"),
                    patient_data.get("phone"),
                    patient_data.get("id_card"),
                    patient_data.get("allergies"),
                    patient_data.get("medical_history"),
                )
            )
            patient_id = cursor.lastrowid
            return PatientService.get_by_id(patient_id)

    @staticmethod
    def update(patient_id: int, patient_data: dict) -> Optional[Patient]:
        """更新患者信息."""
        patient = PatientService.get_by_id(patient_id)
        if not patient:
            return None

        with get_db() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            for key in ["name", "gender", "age", "phone", "id_card", "allergies", "medical_history"]:
                if key in patient_data:
                    fields.append(f"{key} = ?")
                    values.append(patient_data[key])
            values.append(patient_id)

            cursor.execute(
                f"UPDATE patients SET {', '.join(fields)} WHERE id = ?",
                values
            )
            return PatientService.get_by_id(patient_id)

    @staticmethod
    def get_or_create(phone: str, patient_data: dict = None) -> Patient:
        """获取或创建患者."""
        patient = PatientService.get_by_phone(phone)
        if patient:
            return patient

        data = patient_data or {}
        data["phone"] = phone
        return PatientService.create(data)
