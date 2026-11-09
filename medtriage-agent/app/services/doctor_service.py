"""医生服务."""
from __future__ import annotations

from typing import List, Optional
from app.database import get_db
from app.models.schemas import Doctor


class DoctorService:
    """医生服务类."""

    @staticmethod
    def list_all(department_id: Optional[int] = None, limit: int = 100) -> List[Doctor]:
        """获取医生列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            if department_id:
                cursor.execute(
                    """
                    SELECT d.*, dep.name as department_name
                    FROM doctors d
                    LEFT JOIN departments dep ON d.department_id = dep.id
                    WHERE d.department_id = ?
                    ORDER BY d.rating DESC, d.consultation_count DESC
                    LIMIT ?
                    """,
                    (department_id, limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT d.*, dep.name as department_name
                    FROM doctors d
                    LEFT JOIN departments dep ON d.department_id = dep.id
                    ORDER BY d.rating DESC, d.consultation_count DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
            rows = cursor.fetchall()
            return [Doctor(**dict(row)) for row in rows]

    @staticmethod
    def get_by_id(doctor_id: int) -> Optional[Doctor]:
        """根据ID获取医生."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.*, dep.name as department_name
                FROM doctors d
                LEFT JOIN departments dep ON d.department_id = dep.id
                WHERE d.id = ?
                """,
                (doctor_id,)
            )
            row = cursor.fetchone()
            return Doctor(**dict(row)) if row else None

    @staticmethod
    def search(keyword: str, department_id: Optional[int] = None, limit: int = 20) -> List[Doctor]:
        """搜索医生."""
        with get_db() as conn:
            cursor = conn.cursor()
            if department_id:
                cursor.execute(
                    """
                    SELECT d.*, dep.name as department_name
                    FROM doctors d
                    LEFT JOIN departments dep ON d.department_id = dep.id
                    WHERE d.department_id = ? AND (d.name LIKE ? OR d.specialty LIKE ?)
                    ORDER BY d.rating DESC
                    LIMIT ?
                    """,
                    (department_id, f"%{keyword}%", f"%{keyword}%", limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT d.*, dep.name as department_name
                    FROM doctors d
                    LEFT JOIN departments dep ON d.department_id = dep.id
                    WHERE d.name LIKE ? OR d.specialty LIKE ?
                    ORDER BY d.rating DESC
                    LIMIT ?
                    """,
                    (f"%{keyword}%", f"%{keyword}%", limit)
                )
            rows = cursor.fetchall()
            return [Doctor(**dict(row)) for row in rows]

    @staticmethod
    def recommend_doctors(
        department_id: int,
        specialty: Optional[str] = None,
        limit: int = 5,
    ) -> List[Doctor]:
        """推荐医生 - 综合评分、经验、接诊量排序."""
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
                SELECT d.*, dep.name as department_name
                FROM doctors d
                LEFT JOIN departments dep ON d.department_id = dep.id
                WHERE d.department_id = ?
            """
            params = [department_id]

            if specialty:
                query += " AND d.specialty LIKE ?"
                params.append(f"%{specialty}%")

            # 综合评分：rating * 0.4 + experience/30 * 0.3 + consultation_count归一化 * 0.3
            query += """
                ORDER BY (
                    d.rating * 0.4 +
                    CAST(d.experience_years AS REAL) / 30.0 * 0.3 +
                    CAST(MIN(d.consultation_count, 5000) AS REAL) / 5000.0 * 0.3
                ) DESC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Doctor(**dict(row)) for row in rows]
