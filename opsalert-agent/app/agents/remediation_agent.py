"""处置建议 Agent - 负责生成修复方案和处置建议"""
from typing import Dict, Any, List
from app.mock_llm import get_mock_llm
from app.services.knowledge_service import get_knowledge_service
from app.tools.tools_impl import generate_fix_plan, create_ticket


class RemediationAgent:
    """处置建议Agent
    职责：生成处置方案、风险评估、回滚方案、创建工单
    """

    def __init__(self):
        self.llm = get_mock_llm()
        self.knowledge_service = get_knowledge_service()
        self.name = "RemediationAgent"

    def analyze(self, alert: Dict[str, Any], diagnosis_result: Dict[str, Any],
                detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成处置建议
        :param alert: 告警数据
        :param diagnosis_result: 诊断结果
        :param detection_result: 检测结果
        :return: 处置建议
        """
        # 1. 获取相关知识库条目
        top_cause = diagnosis_result.get("top_root_cause", {})
        category = top_cause.get("category", "")
        description = top_cause.get("description", "")

        # 用根因描述搜索知识库
        kb_query = f"{description} {category} {alert.get('alert_name', '')}"
        knowledge_entries = self.knowledge_service.search_knowledge(
            kb_query, top_k=3, service=alert.get("service")
        )

        # 2. 构造根因分析结果格式
        root_cause_data = {
            "top_hypothesis": top_cause,
            "hypotheses": diagnosis_result.get("hypotheses", []),
        }

        # 3. 生成修复方案
        fix_plan = generate_fix_plan(
            root_cause=root_cause_data,
            alert_data=alert,
            knowledge_entries=knowledge_entries,
        )

        # 4. 调用LLM生成说明
        llm_result = self.llm.chat([
            {"role": "system", "content": "你是一个运维专家remediation，负责生成故障处置建议。"},
            {"role": "user", "content": f"请为以下故障生成处置建议：\n"
                                        f"告警: {alert.get('alert_name')}\n"
                                        f"根因: {description}\n"
                                        f"类别: {category}\n"
                                        f"步骤数: {len(fix_plan.get('remediation_steps', []))}\n"
                                        f"预计时间: {fix_plan.get('estimated_total_time_minutes')}分钟\n"},
        ])

        # 5. 生成回滚方案摘要
        rollback_steps = fix_plan.get("rollback_plan", [])

        # 6. 构建处置步骤详情
        remediation_steps = []
        for step in fix_plan.get("remediation_steps", []):
            remediation_steps.append({
                "order": step["order"],
                "action": step["action"],
                "description": step["description"],
                "estimated_time_minutes": step["estimated_time_minutes"],
                "risk_level": step["risk_level"],
                "rollback_step": step["rollback_step"],
                "automation_available": step["automation_available"],
                "command": step["command"],
            })

        return {
            "agent": self.name,
            "remediation_steps": remediation_steps,
            "estimated_total_time_minutes": fix_plan.get("estimated_total_time_minutes", 0),
            "overall_risk_level": fix_plan.get("overall_risk_level", "medium"),
            "rollback_plan": rollback_steps,
            "knowledge_references": fix_plan.get("knowledge_references", []),
            "related_knowledge": [
                {
                    "id": kb.get("id"),
                    "title": kb.get("title"),
                    "score": kb.get("retrieval_score"),
                }
                for kb in knowledge_entries
            ],
            "llm_explanation": llm_result.get("content", ""),
            "status": "completed",
        }

    def create_incident_ticket(self, alert: Dict[str, Any], analysis_result: Dict[str, Any],
                               level: str = "P3") -> Dict[str, Any]:
        """创建工单"""
        priority_map = {
            "P0": "Highest",
            "P1": "High",
            "P2": "Medium",
            "P3": "Low",
        }
        priority = priority_map.get(level, "Medium")

        ticket = create_ticket(
            alert_data=alert,
            analysis_result=analysis_result,
            priority=priority,
        )
        return ticket
