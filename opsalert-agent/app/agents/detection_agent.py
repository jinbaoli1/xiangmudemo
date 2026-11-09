"""检测分级 Agent - 负责告警分级和影响评估"""
from typing import Dict, Any, Tuple
from app.mock_llm import get_mock_llm
from app.services.cmdb_service import get_cmdb_service
from app.services.knowledge_service import get_knowledge_service


class DetectionAgent:
    """检测分级Agent
    职责：对告警进行P0-P3分级，评估影响范围
    """

    def __init__(self):
        self.llm = get_mock_llm()
        self.cmdb_service = get_cmdb_service()
        self.knowledge_service = get_knowledge_service()
        self.name = "DetectionAgent"

    def analyze(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行告警分级分析
        :param alert: 告警数据
        :return: 分级结果
        """
        # 1. 获取CMDB拓扑信息，评估影响范围
        service = alert.get("service", "unknown")
        topology = self.cmdb_service.calculate_impact_scope(service)
        business_priority = topology.get("business_priority", 3)
        impact_score = topology.get("impact_score", 30)

        # 2. 获取历史告警频率
        freq_info = self.knowledge_service.get_alert_frequency(
            alert.get("metric_name", ""),
            service=service,
            days=30,
        )

        # 3. 计算分级得分（基于规则的打分系统）
        score = self._calculate_level_score(alert, business_priority, impact_score, freq_info)

        # 4. 确定级别
        level, reason = self._determine_level(score, alert, business_priority)

        # 5. 调用LLM生成分析说明（模拟）
        llm_result = self.llm.chat([
            {"role": "system", "content": "你是一个告警分级专家，负责对告警进行P0-P3分级检测detection。"},
            {"role": "user", "content": f"请分析以下告警并给出分级：\n"
                                        f"告警名称: {alert.get('alert_name')}\n"
                                        f"严重程度: {alert.get('severity')}\n"
                                        f"服务: {service}\n"
                                        f"计算得分: {score}\n"
                                        f"业务优先级: {business_priority}\n"},
        ])

        return {
            "agent": self.name,
            "level": level,
            "level_score": score,
            "level_reason": reason,
            "business_priority": business_priority,
            "impact_scope": topology,
            "historical_frequency": freq_info,
            "affected_upstream": topology.get("upstream_services", []),
            "affected_downstream": topology.get("downstream_services", []),
            "llm_explanation": llm_result.get("content", ""),
            "status": "completed",
        }

    def _calculate_level_score(self, alert: Dict[str, Any], business_priority: int,
                               impact_score: float, freq_info: Dict[str, Any]) -> float:
        """
        计算分级得分 (0-100)
        维度：严重程度(30%) + 影响范围(30%) + 业务优先级(25%) + 历史频率(15%)
        """
        severity = alert.get("severity", "warning")

        # 严重程度得分 (30%)
        severity_scores = {"critical": 30, "warning": 18, "info": 8}
        severity_score = severity_scores.get(severity, 15)

        # 超出阈值程度
        threshold = float(alert.get("threshold", 1))
        value = float(alert.get("metric_value", 0))
        if threshold > 0:
            ratio = value / threshold
            if ratio >= 2.0:
                severity_score = min(30, severity_score + 5)
            elif ratio >= 1.5:
                severity_score = min(30, severity_score + 3)

        # 影响范围得分 (30%)
        # 归一化到0-30
        impact_normalized = min(30, impact_score / 4)

        # 业务优先级得分 (25%)
        priority_score = (business_priority / 5) * 25

        # 历史频率得分 (15%)
        # 频率越高说明问题越常见，级别适当降低（但不绝对）
        total_count = freq_info.get("total_count", 0)
        if total_count > 30:
            freq_score = 8  # 频繁发生但没解决，说明有一定重要性
        elif total_count > 10:
            freq_score = 10
        elif total_count > 0:
            freq_score = 12
        else:
            freq_score = 15  # 首次发生的异常可能更严重

        total_score = severity_score + impact_normalized + priority_score + freq_score
        return round(min(100, max(0, total_score)), 1)

    def _determine_level(self, score: float, alert: Dict[str, Any],
                         business_priority: int) -> Tuple[str, str]:
        """根据得分确定告警级别"""
        severity = alert.get("severity", "warning")

        # 基础分级
        if score >= 85:
            level = "P0"
            reason = "得分极高，属于重大故障级别，需要立即响应"
        elif score >= 70:
            level = "P1"
            reason = "得分较高，属于严重故障级别，需要紧急处理"
        elif score >= 50:
            level = "P2"
            reason = "得分中等，属于一般故障级别，需要尽快处理"
        else:
            level = "P3"
            reason = "得分较低，属于轻微告警，可按常规流程处理"

        # 特殊情况调整
        if severity == "critical" and business_priority >= 4 and score >= 60:
            if level == "P2":
                level = "P1"
                reason += "；由于是核心服务的critical告警，升级为P1"

        return level, reason
