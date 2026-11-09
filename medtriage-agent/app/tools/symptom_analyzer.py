"""症状分析工具."""
from __future__ import annotations

from typing import List, Tuple, Dict, Any
from app.services.symptom_service import SymptomService
from app.models.schemas import TriageSymptom


class SymptomAnalyzerTool:
    """症状分析工具.

    功能：
    1. 从用户描述中提取症状
    2. 识别危急症状
    3. 评估症状严重程度
    """

    name = "symptom_analyzer"
    description = "从用户描述中分析症状，识别危急症状，评估严重程度"

    def __init__(self):
        self.symptom_service = SymptomService()

    def analyze(self, text: str) -> Dict[str, Any]:
        """分析症状.

        Args:
            text: 用户输入的症状描述文本

        Returns:
            分析结果字典
        """
        # 1. 匹配症状
        matched = self.symptom_service.match_symptoms_from_text(text)

        # 2. 转换为TriageSymptom
        symptoms = []
        for sym, confidence in matched:
            symptoms.append(TriageSymptom(
                name=sym.name,
                confidence=confidence,
                severity=sym.severity,
                body_part=sym.body_part,
            ))

        # 3. 检测危急症状
        critical_symptoms = self.symptom_service.detect_critical_symptoms(text)
        is_critical = len(critical_symptoms) > 0

        # 4. 生成危急警告
        critical_warning = ""
        if is_critical:
            critical_names = "、".join([s.name for s in critical_symptoms])
            critical_warning = (
                f"⚠️ 检测到危急症状：{critical_names}。"
                "这些症状可能提示严重疾病，建议您立即前往急诊科就诊或拨打急救电话！"
            )

        # 5. 如果没有匹配到明确症状，生成追问建议
        follow_up = []
        if not symptoms:
            follow_up = [
                "您能具体描述一下哪里不舒服吗？",
                "症状持续多久了？有没有其他伴随症状？",
                "请问症状的严重程度如何？是轻微、中等还是比较严重？",
            ]

        return {
            "symptoms": symptoms,
            "is_critical": is_critical,
            "critical_symptoms": [s.name for s in critical_symptoms],
            "critical_warning": critical_warning,
            "symptom_ids": [sym.id for sym, _ in matched if hasattr(sym, 'id')],
            "follow_up_questions": follow_up,
        }
