"""分诊Agent - 症状采集与分诊."""
from __future__ import annotations

from typing import Dict, Any, List
from app.agents.mock_llm import get_mock_llm
from app.tools.symptom_analyzer import SymptomAnalyzerTool
from app.tools.department_matcher import DepartmentMatcherTool
from app.models.schemas import SessionState, TriageSymptom, DepartmentRecommendation


class TriageAgent:
    """分诊Agent.

    职责：
    1. 接收患者症状描述
    2. 分析提取症状
    3. 识别危急症状
    4. 推荐就诊科室
    5. 生成追问问题
    """

    name = "triage_agent"
    description = "症状采集与分诊Agent，负责分析症状、识别危急情况、推荐科室"

    def __init__(self):
        self.llm = get_mock_llm()
        self.symptom_analyzer = SymptomAnalyzerTool()
        self.department_matcher = DepartmentMatcherTool()

    def run(self, state: SessionState) -> SessionState:
        """执行分诊流程.

        Args:
            state: 会话状态

        Returns:
            更新后的会话状态
        """
        patient_input = state.patient_input

        # 1. 症状分析
        analysis_result = self.symptom_analyzer.analyze(patient_input)

        # 合并已有症状（去重）
        existing_symptom_names = {s.name for s in state.symptoms}
        new_symptoms = [s for s in analysis_result["symptoms"] if s.name not in existing_symptom_names]
        all_symptoms = list(state.symptoms) + new_symptoms

        # 2. 危急值识别
        is_critical = analysis_result["is_critical"] or state.is_critical
        critical_warning = analysis_result["critical_warning"] or state.critical_warning

        # 3. 科室匹配
        symptom_names = [s.name for s in all_symptoms]
        # 获取症状ID列表
        from app.services.symptom_service import SymptomService
        symptom_service = SymptomService()
        symptom_ids = []
        for s in all_symptoms:
            sym_obj = symptom_service.get_by_name(s.name)
            if sym_obj:
                symptom_ids.append(sym_obj.id)

        dept_result = self.department_matcher.match(symptom_names, symptom_ids)

        # 4. 生成回复文本
        dept_dicts = [
            {"department_name": d.department_name, "confidence": d.confidence, "reason": d.reason}
            for d in dept_result["recommendations"]
        ]
        response_text = self.llm.generate_triage_response(
            symptoms=symptom_names,
            is_critical=is_critical,
            departments=dept_dicts,
        )

        # 5. 生成追问问题
        follow_up_questions = self.llm.generate_follow_up("triage", symptom_names)

        # 6. 更新状态
        state.symptoms = all_symptoms
        state.is_critical = is_critical
        state.critical_warning = critical_warning
        state.department_recommendations = dept_result["recommendations"]
        state.follow_up_questions = follow_up_questions
        state.current_stage = "triage_completed"

        # 添加回复消息
        from app.models.schemas import ChatMessage
        state.messages.append(ChatMessage(role="assistant", content=response_text))

        return state
