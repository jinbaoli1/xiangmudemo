"""症状服务."""
from __future__ import annotations

from typing import List, Optional, Dict, Tuple
from app.database import get_db
from app.models.schemas import Symptom, Disease, DiagnosisCandidate


class SymptomService:
    """症状服务类."""

    @staticmethod
    def list_all() -> List[Symptom]:
        """获取所有症状."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM symptoms ORDER BY id")
            rows = cursor.fetchall()
            return [Symptom(**dict(row)) for row in rows]

    @staticmethod
    def get_by_id(symptom_id: int) -> Optional[Symptom]:
        """根据ID获取症状."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM symptoms WHERE id = ?", (symptom_id,))
            row = cursor.fetchone()
            return Symptom(**dict(row)) if row else None

    @staticmethod
    def get_by_name(name: str) -> Optional[Symptom]:
        """根据名称获取症状."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM symptoms WHERE name = ?", (name,))
            row = cursor.fetchone()
            return Symptom(**dict(row)) if row else None

    @staticmethod
    def search(keyword: str) -> List[Symptom]:
        """搜索症状."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM symptoms WHERE name LIKE ? OR description LIKE ? ORDER BY severity DESC",
                (f"%{keyword}%", f"%{keyword}%")
            )
            rows = cursor.fetchall()
            return [Symptom(**dict(row)) for row in rows]

    @staticmethod
    def get_critical_symptoms() -> List[Symptom]:
        """获取危急症状列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM symptoms WHERE is_critical = 1")
            rows = cursor.fetchall()
            return [Symptom(**dict(row)) for row in rows]

    @staticmethod
    def detect_critical_symptoms(text: str) -> List[Symptom]:
        """检测文本中的危急症状."""
        critical = SymptomService.get_critical_symptoms()
        detected = []
        text_lower = text
        for sym in critical:
            if sym.name in text_lower:
                detected.append(sym)
        return detected

    @staticmethod
    def match_symptoms_from_text(text: str) -> List[Tuple[Symptom, float]]:
        """从文本中匹配症状，返回(症状, 置信度)列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM symptoms")
            all_symptoms = [Symptom(**dict(row)) for row in cursor.fetchall()]

        matched = []
        text_lower = text

        for sym in all_symptoms:
            if sym.name in text_lower:
                # 完全匹配，置信度高
                confidence = 0.9
                matched.append((sym, confidence))
            else:
                # 检查部分匹配或同义词（简化处理）
                # 这里可以扩展同义词词典
                pass

        # 按置信度排序
        matched.sort(key=lambda x: x[1], reverse=True)
        return matched

    @staticmethod
    def get_diseases_by_symptoms(symptom_ids: List[int], limit: int = 10) -> List[DiagnosisCandidate]:
        """根据症状ID列表推断可能的疾病."""
        if not symptom_ids:
            return []

        with get_db() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(symptom_ids))

            # 查询疾病及其症状匹配情况
            cursor.execute(f"""
                SELECT
                    d.id,
                    d.name,
                    d.description,
                    d.severity_level,
                    d.common_symptoms,
                    dep.name as department_name,
                    SUM(sdm.weight) as total_weight,
                    COUNT(sdm.symptom_id) as matched_symptoms
                FROM diseases d
                LEFT JOIN departments dep ON d.department_id = dep.id
                JOIN symptom_disease_map sdm ON d.id = sdm.disease_id
                WHERE sdm.symptom_id IN ({placeholders})
                GROUP BY d.id
                ORDER BY total_weight DESC, matched_symptoms DESC
                LIMIT ?
            """, (*symptom_ids, limit))

            rows = cursor.fetchall()

            if not rows:
                return []

            # 计算概率（归一化）
            max_weight = max(row["total_weight"] for row in rows) if rows else 1

            results = []
            for row in rows:
                probability = round(row["total_weight"] / (max_weight + 1), 3)
                symptoms_list = row["common_symptoms"].split(",") if row["common_symptoms"] else []
                results.append(DiagnosisCandidate(
                    disease_name=row["name"],
                    probability=probability,
                    department=row["department_name"] or "未确定",
                    description=row["description"] or "",
                    key_symptoms=symptoms_list[:5],
                ))

            return results

    @staticmethod
    def get_symptoms_by_disease(disease_name: str) -> List[Symptom]:
        """根据疾病名称获取相关症状."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.*
                FROM symptoms s
                JOIN symptom_disease_map sdm ON s.id = sdm.symptom_id
                JOIN diseases d ON sdm.disease_id = d.id
                WHERE d.name = ?
                ORDER BY sdm.weight DESC
                """,
                (disease_name,)
            )
            rows = cursor.fetchall()
            return [Symptom(**dict(row)) for row in rows]

    @staticmethod
    def get_all_diseases() -> List[Disease]:
        """获取所有疾病."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.*, dep.name as department_name
                FROM diseases d
                LEFT JOIN departments dep ON d.department_id = dep.id
                ORDER BY d.id
                """
            )
            rows = cursor.fetchall()
            return [Disease(**dict(row)) for row in rows]
