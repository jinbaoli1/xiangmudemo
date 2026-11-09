"""根因诊断 Agent - 负责故障根因分析"""
from typing import Dict, Any, List
from app.mock_llm import get_mock_llm
from app.services.metric_service import get_metric_service
from app.services.log_service import get_log_service
from app.services.cmdb_service import get_cmdb_service
from app.services.knowledge_service import get_knowledge_service
from app.tools.tools_impl import analyze_root_cause


class DiagnosisAgent:
    """根因诊断Agent
    职责：分析告警根因，给出假设和置信度
    """

    def __init__(self):
        self.llm = get_mock_llm()
        self.metric_service = get_metric_service()
        self.log_service = get_log_service()
        self.cmdb_service = get_cmdb_service()
        self.knowledge_service = get_knowledge_service()
        self.name = "DiagnosisAgent"

    def analyze(self, alert: Dict[str, Any], detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行根因诊断
        :param alert: 告警数据
        :param detection_result: 检测分级结果
        :return: 诊断结果
        """
        service = alert.get("service", "")
        host = alert.get("host", "")
        metric_name = alert.get("metric_name", "")

        # 1. 查询相关指标
        related_metrics = self._get_related_metrics(metric_name)
        metrics_data = self.metric_service.get_metrics(
            host, related_metrics, service=service, time_range_minutes=30
        )

        # 2. 查询相关错误日志
        logs_data = self.log_service.search_logs(
            host, service, level="ERROR", limit=20, time_range_minutes=30
        )

        # 3. 查询拓扑信息
        topology = self.cmdb_service.get_topology(service, host=host, depth=2)

        # 4. 匹配历史相似告警
        similar_alerts = self.knowledge_service.find_similar_alerts(
            alert, top_k=5, service=service
        )

        # 5. 检索相关知识库
        knowledge_query = f"{alert.get('alert_name')} {alert.get('summary', '')} {metric_name}"
        related_knowledge = self.knowledge_service.search_knowledge(
            knowledge_query, top_k=3, service=service
        )

        # 6. 执行根因分析（规则引擎 + 知识匹配）
        root_cause_result = analyze_root_cause(
            alert_data=alert,
            metrics_data=metrics_data,
            logs_data=logs_data,
            topology_data=topology,
            similar_alerts=similar_alerts,
        )

        # 7. 调用LLM生成分析说明
        llm_result = self.llm.chat([
            {"role": "system", "content": "你是一个根因诊断专家diagnosis，负责分析告警的根本原因。"},
            {"role": "user", "content": f"请分析以下告警的根因：\n"
                                        f"告警: {alert.get('alert_name')}\n"
                                        f"指标: {metric_name}\n"
                                        f"服务: {service}\n"
                                        f"错误日志数: {logs_data.get('total_found', 0)}\n"
                                        f"相似告警数: {len(similar_alerts)}\n"
                                        f"最可能根因: {root_cause_result.get('top_hypothesis', {}).get('description', '')}\n"},
        ])

        # 构建假设列表
        hypotheses = []
        for i, hypo in enumerate(root_cause_result.get("hypotheses", [])):
            # 匹配知识库
            kb_ids = []
            for kb in related_knowledge:
                if any(tag in hypo.get("description", "") for tag in kb.get("tags", [])):
                    kb_ids.append(kb.get("id"))

            hypotheses.append({
                "id": hypo.get("id", f"hypo-{i:02d}"),
                "description": hypo.get("description", ""),
                "category": hypo.get("category", "unknown"),
                "confidence": hypo.get("confidence", 0),
                "evidence": hypo.get("evidence", []),
                "supporting_metrics": hypo.get("supporting_metrics", []),
                "supporting_logs": hypo.get("supporting_logs", []),
                "related_knowledge_ids": kb_ids,
            })

        # 取置信度最高的作为top
        top_hypo = hypotheses[0] if hypotheses else None

        return {
            "agent": self.name,
            "hypotheses": hypotheses,
            "top_root_cause": top_hypo,
            "related_metrics": list(metrics_data.get("metrics", {}).keys()),
            "error_logs_found": logs_data.get("total_found", 0),
            "similar_alerts_count": len(similar_alerts),
            "similar_alerts": similar_alerts[:3],
            "related_knowledge": [
                {
                    "id": kb.get("id"),
                    "title": kb.get("title"),
                    "score": kb.get("retrieval_score"),
                }
                for kb in related_knowledge
            ],
            "llm_explanation": llm_result.get("content", ""),
            "analysis_method": root_cause_result.get("analysis_method", ""),
            "status": "completed",
        }

    def _get_related_metrics(self, metric_name: str) -> List[str]:
        """获取相关的指标列表"""
        # 指标关联规则
        related_map = {
            "cpu_usage": ["cpu_usage", "load_average", "memory_usage", "http_response_time_p99"],
            "memory_usage": ["memory_usage", "jvm_heap_usage", "cpu_usage", "http_response_time_p99"],
            "http_error_rate": ["http_error_rate", "http_response_time_p99", "db_connections", "jvm_heap_usage"],
            "http_response_time_p99": ["http_response_time_p99", "db_slow_queries", "db_connections",
                                       "cpu_usage", "cache_hit_rate"],
            "db_connections": ["db_connections", "db_slow_queries", "db_cpu_usage", "http_response_time_p99"],
            "db_slow_queries": ["db_slow_queries", "db_cpu_usage", "db_connections", "http_response_time_p99"],
            "jvm_heap_usage": ["jvm_heap_usage", "jvm_gc_duration", "memory_usage", "cpu_usage"],
            "mq_queue_size": ["mq_queue_size", "mq_consume_latency", "http_response_time_p99"],
            "redis_memory_usage": ["redis_memory_usage", "redis_latency", "cache_hit_rate"],
            "service_up": ["cpu_usage", "memory_usage", "http_qps", "http_error_rate"],
        }
        return related_map.get(metric_name, [metric_name, "cpu_usage", "memory_usage"])
