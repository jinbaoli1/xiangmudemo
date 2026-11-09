"""用药Agent - 用药建议+禁忌."""
from __future__ import annotations

from typing import Dict, Any, List
from app.agents.mock_llm import get_mock_llm
from app.tools.medication_check import MedicationCheckTool
from app.services.patient_service import PatientService
from app.models.schemas import SessionState, MedicationSuggestion


class MedicationAgent:
    """用药Agent.

    职责：
    1. 根据疾病推荐药物
    2. 检查药物相互作用
    3. 过敏提示
    4. 特殊人群禁忌
    """

    name = "medication_agent"
    description = "用药建议Agent，提供药物推荐和用药安全检查"

    def __init__(self):
        self.llm = get_mock_llm()
        self.medication_check = MedicationCheckTool()
        self.patient_service = PatientService()

    def run(self, state: SessionState) -> SessionState:
        """执行用药建议.

        Args:
            state: 会话状态

        Returns:
            更新后的会话状态
        """
        # 1. 获取患者信息（过敏史等）
        allergies = ""
        is_pregnant = False
        is_elderly = False
        is_child = False

        if state.patient_id:
            patient = self.patient_service.get_by_id(state.patient_id)
            if patient:
                allergies = patient.allergies or ""
                if patient.age and patient.age >= 65:
                    is_elderly = True
                if patient.age and patient.age < 18:
                    is_child = True
                if patient.gender == "女" and "孕" in (patient.medical_history or ""):
                    is_pregnant = True

        # 2. 根据诊断候选推荐药物
        all_medications = []
        medication_names = []

        for candidate in state.diagnosis_candidates[:3]:
            med_result = self.medication_check.recommend_medications(
                candidate.disease_name, limit=2
            )
            for med in med_result["medications"]:
                if med["name"] not in medication_names:
                    all_medications.append(
                        MedicationSuggestion(
                            medication_name=med["name"],
                            generic_name=med["generic_name"],
                            category=med["category"],
                            indication=med["indication"],
                            dosage=med["dosage"],
                            warnings=med["warnings"],
                        )
                    )
                    medication_names.append(med["name"])

        # 限制数量
        all_medications = all_medications[:5]
        medication_names = [m.medication_name for m in all_medications]

        # 3. 用药安全综合检查
        if medication_names:
            safety_result = self.medication_check.comprehensive_check(
                medication_names=medication_names,
                allergies=allergies,
                pregnant=is_pregnant,
                elderly=is_elderly,
                child=is_child,
            )
            risk_level = safety_result["risk_level"]
            # 将安全警告加入药物warnings
            if safety_result["interactions"]["has_risk"]:
                for inter in safety_result["interactions"]["interactions"]:
                    for med in all_medications:
                        if med.medication_name == inter["medication_1"]:
                            med.warnings.append(f"与{inter['medication_2']}存在{inter['severity']}级相互作用")
            if safety_result["allergies"].get("has_allergy_risk"):
                for alert in safety_result["allergies"]["allergy_alerts"]:
                    for med in all_medications:
                        if med.medication_name == alert["medication"]:
                            med.warnings.append(f"过敏风险：{alert['description']}")
        else:
            risk_level = "low"
            safety_result = {"overall_summary": "暂无药物推荐"}

        # 4. 生成用药建议回复
        med_dicts = [
            {
                "medication_name": m.medication_name,
                "name": m.medication_name,
                "category": m.category,
                "indication": m.indication,
                "dosage": m.dosage,
                "warnings": m.warnings,
            }
            for m in all_medications
        ]

        response_text = self.llm.generate_medication_response(
            medications=med_dicts,
            risk_level=risk_level,
        )

        # 5. 添加安全提示
        if medication_names:
            response_text += "\n\n" + safety_result.get("overall_summary", "")

        # 6. 生成追问
        follow_up = self.llm.generate_follow_up("medication", [s.name for s in state.symptoms])

        # 7. 更新状态
        state.medication_suggestions = all_medications
        state.follow_up_questions = follow_up
        state.current_stage = "medication_completed"

        # 添加回复消息
        from app.models.schemas import ChatMessage
        state.messages.append(ChatMessage(role="assistant", content=response_text))

        return state
