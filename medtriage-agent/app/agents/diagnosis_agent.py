"""诊断Agent - 疾病分析鉴别."""
from __future__ import annotations

from typing import Dict, Any, List
from app.agents.mock_llm import get_mock_llm
from app.services.symptom_service import SymptomService
from app.models.schemas import SessionState, DiagnosisCandidate


class DiagnosisAgent:
    """诊断Agent.

    职责：
    1. 根据症状分析可能的疾病
    2. 疾病鉴别诊断
    3. 提供疾病详细信息
    """

    name = "diagnosis_agent"
    description = "疾病分析鉴别Agent，根据症状推断可能的疾病并进行鉴别分析"

    def __init__(self):
        self.llm = get_mock_llm()
        self.symptom_service = SymptomService()

    def run(self, state: SessionState) -> SessionState:
        """执行疾病分析.

        Args:
            state: 会话状态

        Returns:
            更新后的会话状态
        """
        # 1. 获取症状ID列表
        symptom_ids = []
        symptom_names = [s.name for s in state.symptoms]
        for s in state.symptoms:
            sym_obj = self.symptom_service.get_by_name(s.name)
            if sym_obj:
                symptom_ids.append(sym_obj.id)

        # 2. 推断可能的疾病
        if symptom_ids:
            candidates = self.symptom_service.get_diseases_by_symptoms(
                symptom_ids, limit=10
            )
        else:
            candidates = []

        # 3. 合并已有候选
        existing_diseases = {c.disease_name for c in state.diagnosis_candidates}
        new_candidates = [c for c in candidates if c.disease_name not in existing_diseases]
        all_candidates = list(state.diagnosis_candidates) + new_candidates

        # 按概率排序，取前5个
        all_candidates.sort(key=lambda x: x.probability, reverse=True)
        all_candidates = all_candidates[:5]

        # 4. 生成诊断分析回复
        candidate_dicts = [
            {
                "disease_name": c.disease_name,
                "probability": c.probability,
                "description": c.description,
                "key_symptoms": c.key_symptoms,
                "department": c.department,
            }
            for c in all_candidates
        ]

        response_text = self.llm.generate_diagnosis_response(
            symptoms=symptom_names,
            candidates=candidate_dicts,
        )

        # 5. 生成追问问题
        follow_up = self.llm.generate_follow_up("diagnosis", symptom_names)

        # 6. 更新状态
        state.diagnosis_candidates = all_candidates
        state.follow_up_questions = follow_up
        state.current_stage = "diagnosis_completed"

        # 添加回复消息
        from app.models.schemas import ChatMessage
        state.messages.append(ChatMessage(role="assistant", content=response_text))

        return state
