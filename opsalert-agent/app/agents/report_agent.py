"""报告生成 Agent - 负责生成事故报告和Postmortem"""
from typing import Dict, Any, List
from datetime import datetime
from app.mock_llm import get_mock_llm
from app.tools.tools_impl import generate_postmortem


class ReportAgent:
    """报告生成Agent
    职责：生成事故报告、时间线、改进项
    """

    def __init__(self):
        self.llm = get_mock_llm()
        self.name = "ReportAgent"

    def generate_report(self, alert: Dict[str, Any], detection_result: Dict[str, Any],
                        diagnosis_result: Dict[str, Any], remediation_result: Dict[str, Any],
                        incident_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成完整的分析报告
        :param alert: 告警数据
        :param detection_result: 检测结果
        :param diagnosis_result: 诊断结果
        :param remediation_result: 处置结果
        :param incident_data: 事故数据
        :return: 报告
        """
        # 构建时间线
        timeline = self._build_timeline(alert, detection_result, diagnosis_result,
                                        remediation_result, incident_data)

        # 构建根因数据
        root_cause_data = {
            "top_hypothesis": diagnosis_result.get("top_root_cause", {}),
        }

        # 构建事故数据
        incident = incident_data or {
            "id": alert.get("incident_id", ""),
            "severity": self._level_to_severity(detection_result.get("level", "P3")),
            "started_at": alert.get("starts_at"),
            "resolved_at": None,
            "impact_scope": detection_result.get("impact_scope", {}).get("impact_level", ""),
            "affected_services": [alert.get("service", "")],
        }

        # 生成Postmortem
        postmortem = generate_postmortem(
            incident_data=incident,
            alert_data=alert,
            root_cause=root_cause_data,
            remediation=remediation_result,
            timeline=timeline,
        )

        # 调用LLM生成报告说明
        llm_result = self.llm.chat([
            {"role": "system", "content": "你是一个事故报告专家report，负责生成专业的Postmortem报告。"},
            {"role": "user", "content": f"请生成以下事故的Postmortem报告：\n"
                                        f"告警: {alert.get('alert_name')}\n"
                                        f"级别: {detection_result.get('level')}\n"
                                        f"服务: {alert.get('service')}\n"
                                        f"根因: {diagnosis_result.get('top_root_cause', {}).get('description', '')}\n"
                                        f"时间线条数: {len(timeline)}\n"},
        ])

        return {
            "agent": self.name,
            "postmortem": postmortem,
            "timeline": timeline,
            "summary": {
                "alert_name": alert.get("alert_name"),
                "service": alert.get("service"),
                "level": detection_result.get("level"),
                "root_cause": diagnosis_result.get("top_root_cause", {}).get("description", ""),
                "estimated_fix_time": remediation_result.get("estimated_total_time_minutes", 0),
                "risk_level": remediation_result.get("overall_risk_level", ""),
                "action_items_count": len(postmortem.get("action_items", [])),
            },
            "llm_explanation": llm_result.get("content", ""),
            "status": "completed",
        }

    def _build_timeline(self, alert: Dict[str, Any], detection_result: Dict[str, Any],
                        diagnosis_result: Dict[str, Any], remediation_result: Dict[str, Any],
                        incident_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """构建事件时间线"""
        timeline = []
        starts_at = alert.get("starts_at", datetime.now().isoformat())

        timeline.append({
            "time": starts_at,
            "event": "告警触发",
            "description": f"{alert.get('alert_name')}: {alert.get('summary', '')}",
            "agent": "monitoring",
        })

        timeline.append({
            "time": "T+0s",
            "event": "OpsAlert Agent接收告警",
            "description": "告警被接入分析系统，启动自动化分析流程",
            "agent": "system",
        })

        timeline.append({
            "time": "T+3s",
            "event": "检测分级完成",
            "description": f"告警级别: {detection_result.get('level')} "
                           f"(得分: {detection_result.get('level_score')})",
            "agent": "DetectionAgent",
        })

        timeline.append({
            "time": "T+10s",
            "event": "根因诊断完成",
            "description": f"最可能根因: {diagnosis_result.get('top_root_cause', {}).get('description', '未知')} "
                           f"(置信度: {diagnosis_result.get('top_root_cause', {}).get('confidence', 0):.0%})",
            "agent": "DiagnosisAgent",
        })

        timeline.append({
            "time": "T+15s",
            "event": "处置方案生成",
            "description": f"生成{len(remediation_result.get('remediation_steps', []))}步处置方案，"
                           f"预计{remediation_result.get('estimated_total_time_minutes', 0)}分钟完成",
            "agent": "RemediationAgent",
        })

        if incident_data and incident_data.get("ticket_id"):
            timeline.append({
                "time": "T+20s",
                "event": "工单创建",
                "description": f"自动创建工单: {incident_data.get('ticket_id')}",
                "agent": "RemediationAgent",
            })

        timeline.append({
            "time": "T+25s",
            "event": "分析报告生成",
            "description": "完整的分析报告和Postmortem已生成",
            "agent": "ReportAgent",
        })

        return timeline

    def _level_to_severity(self, level: str) -> str:
        """告警级别转事故级别"""
        mapping = {
            "P0": "SEV1",
            "P1": "SEV2",
            "P2": "SEV3",
            "P3": "SEV4",
        }
        return mapping.get(level, "SEV3")
