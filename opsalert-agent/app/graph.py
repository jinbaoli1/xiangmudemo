"""OpsAlert 分析状态机 - LangGraph编排四Agent协作流程"""
import uuid
from datetime import datetime
from typing import TypedDict, Dict, Any, List, Optional, Callable

from app.agents.detection_agent import DetectionAgent
from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.remediation_agent import RemediationAgent
from app.agents.report_agent import ReportAgent
from app.services.alert_service import get_alert_service
from app.services.incident_service import get_incident_service


class AgentState(TypedDict):
    """Agent状态"""
    # 输入
    alert: Dict[str, Any]
    trace_id: str

    # 各阶段结果
    detection_result: Optional[Dict[str, Any]]
    diagnosis_result: Optional[Dict[str, Any]]
    remediation_result: Optional[Dict[str, Any]]
    report_result: Optional[Dict[str, Any]]

    # 中间状态
    incident_id: Optional[str]
    ticket_id: Optional[str]
    incident_data: Optional[Dict[str, Any]]

    # 执行记录
    agent_steps: List[Dict[str, Any]]
    errors: List[str]

    # 当前状态
    current_step: str
    status: str  # pending, running, completed, failed
    started_at: str
    completed_at: Optional[str]


class OpsAlertGraph:
    """OpsAlert 分析状态机"""

    def __init__(self):
        self.detection_agent = DetectionAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.remediation_agent = RemediationAgent()
        self.report_agent = ReportAgent()
        self.alert_service = get_alert_service()
        self.incident_service = get_incident_service()

        # 流式回调
        self._stream_callback: Optional[Callable] = None

    def set_stream_callback(self, callback: Callable):
        """设置流式输出回调"""
        self._stream_callback = callback

    def _emit(self, event: str, data: Dict[str, Any]):
        """发送流式事件"""
        if self._stream_callback:
            self._stream_callback(event, data)

    def create_initial_state(self, alert: Dict[str, Any]) -> AgentState:
        """创建初始状态"""
        trace_id = f"trace-{uuid.uuid4().hex[:16]}"
        return {
            "alert": alert,
            "trace_id": trace_id,
            "detection_result": None,
            "diagnosis_result": None,
            "remediation_result": None,
            "report_result": None,
            "incident_id": None,
            "ticket_id": None,
            "incident_data": None,
            "agent_steps": [],
            "errors": [],
            "current_step": "init",
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
        }

    def _add_step(self, state: AgentState, step_name: str, description: str,
                  result: Dict[str, Any] = None):
        """记录执行步骤"""
        step = {
            "step": step_name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
        }
        state["agent_steps"].append(step)
        return step

    # ---- 节点函数 ----

    def node_orchestrator(self, state: AgentState) -> AgentState:
        """Orchestrator节点 - 接收告警，初始化分析"""
        state["current_step"] = "orchestrator"
        state["status"] = "running"

        alert = state["alert"]
        trace_id = state["trace_id"]

        self._emit("start", {
            "trace_id": trace_id,
            "alert_id": alert.get("id"),
            "alert_name": alert.get("alert_name"),
            "message": f"开始分析告警: {alert.get('alert_name')}",
        })

        self._add_step(state, "orchestrator", f"Orchestrator接收告警，trace_id={trace_id}")
        self._emit("step", {
            "step": "orchestrator",
            "agent": "Orchestrator",
            "message": "告警接入成功，启动多Agent分析流程",
            "status": "completed",
        })

        return state

    def node_detection(self, state: AgentState) -> AgentState:
        """DetectionAgent节点 - 告警分级"""
        state["current_step"] = "detection"

        self._emit("step", {
            "step": "detection",
            "agent": "DetectionAgent",
            "message": "正在进行告警分级和影响评估...",
            "status": "running",
        })

        try:
            result = self.detection_agent.analyze(state["alert"])
            state["detection_result"] = result

            # 更新告警的级别
            level = result.get("level")
            self.alert_service.update_alert(state["alert"]["id"], {
                "level": level,
                "level_score": result.get("level_score"),
            })

            self._add_step(state, "detection",
                           f"告警分级完成: {level} (得分: {result.get('level_score')})")

            self._emit("step", {
                "step": "detection",
                "agent": "DetectionAgent",
                "message": f"告警分级完成: {level}",
                "level": level,
                "level_score": result.get("level_score"),
                "impact_scope": result.get("impact_scope", {}),
                "status": "completed",
            })

        except Exception as e:
            state["errors"].append(f"DetectionAgent error: {str(e)}")
            self._emit("step", {
                "step": "detection",
                "agent": "DetectionAgent",
                "message": f"分级失败: {str(e)}",
                "status": "failed",
                "error": str(e),
            })

        return state

    def node_diagnosis(self, state: AgentState) -> AgentState:
        """DiagnosisAgent节点 - 根因分析"""
        state["current_step"] = "diagnosis"

        self._emit("step", {
            "step": "diagnosis",
            "agent": "DiagnosisAgent",
            "message": "正在进行根因诊断，查询指标、日志、历史数据...",
            "status": "running",
        })

        try:
            result = self.diagnosis_agent.analyze(
                state["alert"],
                state.get("detection_result") or {},
            )
            state["diagnosis_result"] = result

            top_cause = result.get("top_root_cause", {})
            self._add_step(state, "diagnosis",
                           f"根因分析完成: {top_cause.get('description', '未知')} "
                           f"(置信度: {top_cause.get('confidence', 0):.0%})")

            self._emit("step", {
                "step": "diagnosis",
                "agent": "DiagnosisAgent",
                "message": f"根因分析完成: {top_cause.get('description', '未知')}",
                "top_root_cause": top_cause,
                "hypotheses_count": len(result.get("hypotheses", [])),
                "similar_alerts_count": result.get("similar_alerts_count", 0),
                "status": "completed",
            })

        except Exception as e:
            state["errors"].append(f"DiagnosisAgent error: {str(e)}")
            self._emit("step", {
                "step": "diagnosis",
                "agent": "DiagnosisAgent",
                "message": f"诊断失败: {str(e)}",
                "status": "failed",
                "error": str(e),
            })

        return state

    def node_remediation(self, state: AgentState) -> AgentState:
        """RemediationAgent节点 - 处置建议"""
        state["current_step"] = "remediation"

        self._emit("step", {
            "step": "remediation",
            "agent": "RemediationAgent",
            "message": "正在生成处置建议和修复方案...",
            "status": "running",
        })

        try:
            result = self.remediation_agent.analyze(
                state["alert"],
                state.get("diagnosis_result") or {},
                state.get("detection_result") or {},
            )
            state["remediation_result"] = result

            # P0/P1级自动创建工单和事故
            level = (state.get("detection_result") or {}).get("level", "P3")
            if level in ("P0", "P1"):
                # 创建事故
                severity_map = {"P0": "SEV1", "P1": "SEV2", "P2": "SEV3", "P3": "SEV4"}
                incident = self.incident_service.create_incident(
                    state["alert"],
                    severity=severity_map.get(level, "SEV3"),
                )
                state["incident_id"] = incident["id"]
                state["incident_data"] = incident

                # 更新告警关联事故
                self.alert_service.update_alert(state["alert"]["id"], {
                    "incident_id": incident["id"],
                })

                # 创建工单
                ticket = self.remediation_agent.create_incident_ticket(
                    state["alert"],
                    state.get("diagnosis_result") or {},
                    level=level,
                )
                state["ticket_id"] = ticket["id"]

                # 通知On-Call
                self.incident_service.notify_oncall(incident["id"])

            steps_count = len(result.get("remediation_steps", []))
            self._add_step(state, "remediation",
                           f"处置方案生成: {steps_count}步, 预计{result.get('estimated_total_time_minutes')}分钟, "
                           f"风险等级: {result.get('overall_risk_level')}")

            self._emit("step", {
                "step": "remediation",
                "agent": "RemediationAgent",
                "message": f"处置方案生成完成，共{steps_count}步",
                "steps_count": steps_count,
                "estimated_time": result.get("estimated_total_time_minutes"),
                "risk_level": result.get("overall_risk_level"),
                "incident_id": state.get("incident_id"),
                "ticket_id": state.get("ticket_id"),
                "status": "completed",
            })

        except Exception as e:
            state["errors"].append(f"RemediationAgent error: {str(e)}")
            self._emit("step", {
                "step": "remediation",
                "agent": "RemediationAgent",
                "message": f"处置方案生成失败: {str(e)}",
                "status": "failed",
                "error": str(e),
            })

        return state

    def node_report(self, state: AgentState) -> AgentState:
        """ReportAgent节点 - 报告生成"""
        state["current_step"] = "report"

        self._emit("step", {
            "step": "report",
            "agent": "ReportAgent",
            "message": "正在生成分析报告和Postmortem...",
            "status": "running",
        })

        try:
            result = self.report_agent.generate_report(
                state["alert"],
                state.get("detection_result") or {},
                state.get("diagnosis_result") or {},
                state.get("remediation_result") or {},
                state.get("incident_data"),
            )
            state["report_result"] = result

            self._add_step(state, "report",
                           f"报告生成完成: {len(result.get('postmortem', {}).get('action_items', []))}个改进项")

            state["status"] = "completed"
            state["completed_at"] = datetime.now().isoformat()

            self._emit("step", {
                "step": "report",
                "agent": "ReportAgent",
                "message": "分析报告生成完成",
                "summary": result.get("summary", {}),
                "status": "completed",
            })

            self._emit("complete", {
                "trace_id": state["trace_id"],
                "alert_id": state["alert"].get("id"),
                "level": (state.get("detection_result") or {}).get("level"),
                "root_cause": (state.get("diagnosis_result") or {}).get("top_root_cause", {}).get("description"),
                "status": "completed",
                "total_steps": len(state["agent_steps"]),
            })

        except Exception as e:
            state["errors"].append(f"ReportAgent error: {str(e)}")
            state["status"] = "failed"
            self._emit("step", {
                "step": "report",
                "agent": "ReportAgent",
                "message": f"报告生成失败: {str(e)}",
                "status": "failed",
                "error": str(e),
            })
            self._emit("complete", {
                "trace_id": state["trace_id"],
                "status": "failed",
                "error": str(e),
            })

        return state

    # ---- 条件边 ----

    def should_create_incident(self, state: AgentState) -> str:
        """判断是否需要创建事故（根据级别路由）"""
        level = (state.get("detection_result") or {}).get("level", "P3")
        # P0/P1 走完整流程（含事故和工单），P2/P3 也走完整流程但不自动创建事故
        # 这里统一走完整流程，事故创建逻辑在remediation节点中判断
        return "remediation"

    # ---- 执行方法 ----

    def run(self, alert: Dict[str, Any], stream_callback: Callable = None) -> Dict[str, Any]:
        """
        同步执行完整分析流程
        :param alert: 告警数据
        :param stream_callback: 流式回调函数(event, data)
        :return: 最终状态
        """
        if stream_callback:
            self.set_stream_callback(stream_callback)

        state = self.create_initial_state(alert)

        # 顺序执行各节点
        state = self.node_orchestrator(state)
        state = self.node_detection(state)
        state = self.node_diagnosis(state)
        state = self.node_remediation(state)
        state = self.node_report(state)

        return self._state_to_result(state)

    async def arun(self, alert: Dict[str, Any], stream_callback: Callable = None):
        """
        异步生成器版本 - 用于SSE流式输出
        """
        if stream_callback:
            self.set_stream_callback(stream_callback)

        state = self.create_initial_state(alert)

        # 逐个节点执行，每个节点产生一个流式事件
        state = self.node_orchestrator(state)
        yield self._state_to_result(state)

        state = self.node_detection(state)
        yield self._state_to_result(state)

        state = self.node_diagnosis(state)
        yield self._state_to_result(state)

        state = self.node_remediation(state)
        yield self._state_to_result(state)

        state = self.node_report(state)
        yield self._state_to_result(state)

    def _state_to_result(self, state: AgentState) -> Dict[str, Any]:
        """将状态转换为结果格式"""
        detection = state.get("detection_result") or {}
        diagnosis = state.get("diagnosis_result") or {}
        remediation = state.get("remediation_result") or {}
        report = state.get("report_result") or {}

        return {
            "trace_id": state["trace_id"],
            "alert_id": state["alert"].get("id"),
            "alert": state["alert"],

            "level": detection.get("level"),
            "level_score": detection.get("level_score"),
            "level_reason": detection.get("level_reason", ""),

            "incident_id": state.get("incident_id"),
            "incident_severity": (state.get("incident_data") or {}).get("severity"),
            "ticket_id": state.get("ticket_id"),

            "impact_scope": detection.get("impact_scope", {}).get("impact_level", ""),
            "affected_services": [state["alert"].get("service", "")],
            "affected_upstream": detection.get("affected_upstream", []),
            "affected_downstream": detection.get("affected_downstream", []),

            "root_cause_hypotheses": diagnosis.get("hypotheses", []),
            "top_root_cause": diagnosis.get("top_root_cause"),

            "remediation_steps": remediation.get("remediation_steps", []),
            "estimated_fix_time": remediation.get("estimated_total_time_minutes", 0),
            "overall_risk_level": remediation.get("overall_risk_level", ""),

            "similar_historical_alerts": diagnosis.get("similar_alerts", []),
            "related_knowledge": diagnosis.get("related_knowledge", []),

            "postmortem": report.get("postmortem"),
            "timeline": report.get("timeline", []),

            "agent_steps": state["agent_steps"],
            "current_step": state["current_step"],
            "status": state["status"],
            "errors": state["errors"],

            "started_at": state["started_at"],
            "completed_at": state.get("completed_at"),
        }


# 全局单例
_ops_alert_graph: Optional[OpsAlertGraph] = None


def get_ops_alert_graph() -> OpsAlertGraph:
    global _ops_alert_graph
    if _ops_alert_graph is None:
        _ops_alert_graph = OpsAlertGraph()
    return _ops_alert_graph
