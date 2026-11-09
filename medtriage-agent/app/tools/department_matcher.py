"""科室匹配工具."""
from __future__ import annotations

from typing import List, Dict, Any
from app.services.symptom_service import SymptomService
from app.services.department_service import DepartmentService
from app.models.schemas import DepartmentRecommendation


class DepartmentMatcherTool:
    """科室匹配工具.

    基于症状关键词匹配 + 权重打分 + 科室推荐 + 置信度
    """

    name = "department_matcher"
    description = "根据症状匹配推荐科室，计算置信度和推荐理由"

    def __init__(self):
        self.symptom_service = SymptomService()
        self.department_service = DepartmentService()

    def match(self, symptoms: List[str], symptom_ids: List[int] = None) -> Dict[str, Any]:
        """匹配科室.

        Args:
            symptoms: 症状名称列表
            symptom_ids: 症状ID列表（可选，用于疾病推断）

        Returns:
            科室推荐结果
        """
        dept_scores: Dict[int, Dict[str, Any]] = {}

        # 1. 基于症状-科室关联打分
        all_departments = self.department_service.list_all()
        dept_map = {d.id: d for d in all_departments}

        for sym_name in symptoms:
            sym = self.symptom_service.get_by_name(sym_name)
            if not sym:
                continue

            if sym.related_departments:
                related_depts = [d.strip() for d in sym.related_departments.split(",")]
                for dept_name in related_depts:
                    dept = self.department_service.get_by_name(dept_name)
                    if dept:
                        if dept.id not in dept_scores:
                            dept_scores[dept.id] = {
                                "department": dept,
                                "score": 0.0,
                                "matched_symptoms": [],
                                "reasons": [],
                            }
                        # 症状严重程度加权
                        weight = sym.severity / 3.0  # 归一化
                        dept_scores[dept.id]["score"] += weight
                        dept_scores[dept.id]["matched_symptoms"].append(sym.name)
                        dept_scores[dept.id]["reasons"].append(
                            f"症状「{sym.name}」常就诊于{dept.name}"
                        )

        # 2. 如果有症状ID，基于疾病推断补充科室
        if symptom_ids:
            diseases = self.symptom_service.get_diseases_by_symptoms(symptom_ids, limit=10)
            for disease in diseases:
                dept = self.department_service.get_by_name(disease.department)
                if dept and dept.id in dept_scores:
                    # 疾病概率加权
                    dept_scores[dept.id]["score"] += disease.probability * 2.0
                    dept_scores[dept.id]["reasons"].append(
                        f"疑似疾病「{disease.disease_name}」归属{dept.name}"
                    )
                elif dept:
                    dept_scores[dept.id] = {
                        "department": dept,
                        "score": disease.probability * 2.0,
                        "matched_symptoms": [],
                        "reasons": [f"疑似疾病「{disease.disease_name}」归属{dept.name}"],
                    }

        # 3. 归一化分数并排序
        if dept_scores:
            max_score = max(v["score"] for v in dept_scores.values())
            if max_score > 0:
                for v in dept_scores.values():
                    v["confidence"] = round(min(v["score"] / max_score, 1.0), 3)
            else:
                for v in dept_scores.values():
                    v["confidence"] = 0.0

        # 4. 转换为推荐列表
        recommendations = []
        sorted_depts = sorted(dept_scores.values(), key=lambda x: x["confidence"], reverse=True)

        for item in sorted_depts[:5]:
            dept = item["department"]
            reasons = item.get("reasons", [])
            reason_text = "；".join(reasons[:3]) if reasons else "基于症状分析推荐"

            recommendations.append(DepartmentRecommendation(
                department_id=dept.id,
                department_name=dept.name,
                confidence=item["confidence"],
                reason=reason_text,
            ))

        # 5. 如果没有匹配到任何科室，给通用建议
        if not recommendations:
            default_dept = self.department_service.get_by_name("全科医学科")
            if not default_dept:
                default_dept = all_departments[0] if all_departments else None
            if default_dept:
                recommendations.append(DepartmentRecommendation(
                    department_id=default_dept.id,
                    department_name=default_dept.name,
                    confidence=0.3,
                    reason="症状不典型，建议先到全科或内科初步就诊",
                ))

        return {
            "recommendations": recommendations,
            "top_department": recommendations[0] if recommendations else None,
            "confidence_level": "high" if recommendations and recommendations[0].confidence > 0.7 else (
                "medium" if recommendations and recommendations[0].confidence > 0.4 else "low"
            ),
        }
