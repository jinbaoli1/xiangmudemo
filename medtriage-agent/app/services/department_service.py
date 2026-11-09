"""科室服务."""
from __future__ import annotations

from typing import List, Optional
from app.database import get_db
from app.models.schemas import Department


class DepartmentService:
    """科室服务类."""

    @staticmethod
    def list_all(category: Optional[str] = None) -> List[Department]:
        """获取所有科室."""
        with get_db() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM departments WHERE category = ? ORDER BY id",
                    (category,)
                )
            else:
                cursor.execute("SELECT * FROM departments ORDER BY id")
            rows = cursor.fetchall()
            return [Department(**dict(row)) for row in rows]

    @staticmethod
    def get_by_id(dept_id: int) -> Optional[Department]:
        """根据ID获取科室."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments WHERE id = ?", (dept_id,))
            row = cursor.fetchone()
            return Department(**dict(row)) if row else None

    @staticmethod
    def get_by_name(name: str) -> Optional[Department]:
        """根据名称获取科室."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments WHERE name = ?", (name,))
            row = cursor.fetchone()
            return Department(**dict(row)) if row else None

    @staticmethod
    def get_by_code(code: str) -> Optional[Department]:
        """根据编码获取科室."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments WHERE code = ?", (code,))
            row = cursor.fetchone()
            return Department(**dict(row)) if row else None

    @staticmethod
    def search(keyword: str) -> List[Department]:
        """搜索科室."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM departments WHERE name LIKE ? OR description LIKE ? ORDER BY id",
                (f"%{keyword}%", f"%{keyword}%")
            )
            rows = cursor.fetchall()
            return [Department(**dict(row)) for row in rows]

    @staticmethod
    def get_categories() -> List[str]:
        """获取科室分类列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM departments WHERE category IS NOT NULL")
            rows = cursor.fetchall()
            return [row["category"] for row in rows]
