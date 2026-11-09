"""LangGraph 分诊状态机 - 多Agent协作主流程."""
from __future__ import annotations

import uuid
import json
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from enum import Enum

from app.models.schemas import SessionState, ChatMessage
from app.agents.triage_agent import TriageAgent
from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.medication_agent import MedicationAgent
from app.tools.doctor_scheduler import DoctorSchedulerTool


class TriageStage(str, Enum):
    """分诊阶段."""
    INIT = "init"
    TRIAGE = "triage"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    DOCTOR_RECOMMEND = "doctor_recommend"
    BOOKING = "booking"
    DONE = "done"


class MedTriageGraph:
    """MedTriage 分诊状态机.

    流程：
    1. init → triage (分诊Agent：症状采集 + 科室推荐)
    2. triage → diagnosis (诊断Agent：疾病分析鉴别)
    3. diagnosis → medication (用药Agent：用药建议 + 安全检查)
    4. medication → doctor_recommend (医生推荐)
    5. doctor_recommend → done (完成)

    特殊情况：
    - 检测到危急症状 → 直接跳到紧急提示
    - 信息不足 → 停留在当前阶段追问
    """

    def __init__(self):
        self.triage_agent = TriageAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.medication_agent = MedicationAgent()
        self.doctor_scheduler = DoctorSchedulerTool()

    def create_session(
        self,
        session_id: Optional[str] = None,
        patient_id: Optional[int] = None,
    ) -> SessionState:
        """创建新会话."""
        if not session_id:
            session_id = str(uuid.uuid4())

        trace_id = str(uuid.uuid4())

        state = SessionState(
            session_id=session_id,
            patient_id=patient_id,
            trace_id=trace_id,
            current_stage="init",
        )

        # 添加欢迎消息
        state.messages.append(ChatMessage(
            role="assistant",
            content="您好！我是智能分诊助手，请描述一下您的症状，我会帮您分析并推荐合适的科室和医生。"
        ))

        return state

    def process_message(
        self,
        state: SessionState,
        user_input: str,
    ) -> SessionState:
        """处理用户消息，驱动状态机流转.

        Args:
            state: 当前会话状态
            user_input: 用户输入文本

        Returns:
            更新后的状态
        """
        # 1. 添加用户消息
        state.patient_input = user_input
        state.messages.append(ChatMessage(role="user", content=user_input))

        # 2. 确定当前阶段并执行相应Agent
        current_stage = state.current_stage

        if current_stage in ("init", "triage", "triage_completed"):
            # 执行分诊Agent
            state = self.triage_agent.run(state)

            # 如果有足够的症状信息，进入诊断阶段
            if len(state.symptoms) >= 1 and not state.is_critical:
                # 继续执行诊断
                state = self.diagnosis_agent.run(state)

                # 继续执行用药建议
                if state.diagnosis_candidates:
                    state = self.medication_agent.run(state)

                # 医生推荐
                state = self._recommend_doctors(state)
                state.current_stage = "completed"
            elif state.is_critical:
                # 危急情况，直接完成（已给出急诊建议）
                state.current_stage = "critical"
            else:
                state.current_stage = "triage"

        return state

    def _recommend_doctors(self, state: SessionState) -> SessionState:
        """医生推荐子流程."""
        if not state.department_recommendations:
            return state

        top_dept = state.department_recommendations[0]
        dept_id = top_dept.department_id

        # 推荐医生
        result = self.doctor_scheduler.recommend_doctors(
            department_id=dept_id,
            limit=3,
        )

        state.doctor_recommendations = result["doctors"]

        # 添加医生推荐消息
        from app.models.schemas import ChatMessage

        if result["doctors"]:
            msg = f"\n👨‍⚕️ 为您推荐{top_dept.department_name}的医生：\n\n"
            for i, doc in enumerate(result["doctors"][:3], 1):
                msg += f"{i}. {doc['doctor_name']} - {doc['title']}\n"
                msg += f"   专长：{doc['specialty']}\n"
                msg += f"   评分：{doc['rating']} | 经验：{doc['experience_years']}年\n"
                msg += f"   近期可预约天数：{doc['available_days']}天\n\n"
            msg += "您可以告诉我想预约哪位医生，或选择具体日期，我可以帮您预约挂号。"
            state.messages.append(ChatMessage(role="assistant", content=msg))

        return state

    def get_triage_result(self, state: SessionState) -> Dict[str, Any]:
        """获取完整的分诊结果."""
        return {
            "session_id": state.session_id,
            "trace_id": state.trace_id,
            "current_stage": state.current_stage,
            "is_critical": state.is_critical,
            "critical_warning": state.critical_warning,
            "symptoms": [s.model_dump() for s in state.symptoms],
            "department_recommendations": [d.model_dump() for d in state.department_recommendations],
            "diagnosis_candidates": [c.model_dump() for c in state.diagnosis_candidates],
            "medication_suggestions": [m.model_dump() for m in state.medication_suggestions],
            "doctor_recommendations": state.doctor_recommendations,
            "follow_up_questions": state.follow_up_questions,
            "messages": [m.model_dump() for m in state.messages[-5:]],  # 最近5条消息
        }

    def stream_process(
        self,
        state: SessionState,
        user_input: str,
    ):
        """流式处理，生成SSE事件.

        Yields:
            事件字典
        """
        trace_id = state.trace_id

        # 事件1: 开始处理
        yield {
            "event": "processing_start",
            "data": {
                "trace_id": trace_id,
                "stage": state.current_stage,
                "message": "正在分析您的症状...",
            },
        }

        # 执行处理
        state = self.process_message(state, user_input)

        # 事件2: 症状分析完成
        if state.symptoms:
            yield {
                "event": "symptom_analysis",
                "data": {
                    "trace_id": trace_id,
                    "symptoms": [s.model_dump() for s in state.symptoms],
                    "is_critical": state.is_critical,
                    "message": f"识别到{len(state.symptoms)}个症状",
                },
            }

        # 事件3: 危急警告
        if state.is_critical:
            yield {
                "event": "critical_alert",
                "data": {
                    "trace_id": trace_id,
                    "warning": state.critical_warning,
                    "message": "检测到危急症状，请立即就医！",
                },
            }

        # 事件4: 科室推荐
        if state.department_recommendations:
            yield {
                "event": "department_recommendation",
                "data": {
                    "trace_id": trace_id,
                    "departments": [d.model_dump() for d in state.department_recommendations],
                    "message": f"推荐{len(state.department_recommendations)}个相关科室",
                },
            }

        # 事件5: 诊断分析
        if state.diagnosis_candidates:
            yield {
                "event": "diagnosis_analysis",
                "data": {
                    "trace_id": trace_id,
                    "candidates": [c.model_dump() for c in state.diagnosis_candidates],
                    "message": f"分析出{len(state.diagnosis_candidates)}个可能的疾病方向",
                },
            }

        # 事件6: 用药建议
        if state.medication_suggestions:
            yield {
                "event": "medication_suggestion",
                "data": {
                    "trace_id": trace_id,
                    "medications": [m.model_dump() for m in state.medication_suggestions],
                    "message": f"提供{len(state.medication_suggestions)}个用药建议",
                },
            }

        # 事件7: 医生推荐
        if state.doctor_recommendations:
            yield {
                "event": "doctor_recommendation",
                "data": {
                    "trace_id": trace_id,
                    "doctors": state.doctor_recommendations,
                    "message": f"推荐{len(state.doctor_recommendations)}位医生",
                },
            }

        # 事件8: 处理完成
        yield {
            "event": "processing_complete",
            "data": {
                "trace_id": trace_id,
                "stage": state.current_stage,
                "result": self.get_triage_result(state),
                "message": "分诊分析完成",
            },
        }


# 全局图实例
_graph_instance: Optional[MedTriageGraph] = None


def get_graph() -> MedTriageGraph:
    """获取图实例（单例）."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = MedTriageGraph()
    return _graph_instance
