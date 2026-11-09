"""知识服务 - 知识库检索 + 历史告警匹配"""
from typing import List, Dict, Any, Optional
from app.retrieval.knowledge_retriever import KnowledgeRetriever
from app.retrieval.alert_retriever import AlertRetriever


class KnowledgeService:
    """知识管理与检索服务"""

    def __init__(self):
        self._knowledge_retriever: Optional[KnowledgeRetriever] = None
        self._alert_retriever: Optional[AlertRetriever] = None
        self._knowledge_entries: List[Dict[str, Any]] = []
        self._historical_alerts: List[Dict[str, Any]] = []

    def load_knowledge_base(self, entries: List[Dict[str, Any]]):
        """加载知识库并构建索引"""
        self._knowledge_entries = entries
        self._knowledge_retriever = KnowledgeRetriever(entries)

    def load_historical_alerts(self, alerts: List[Dict[str, Any]]):
        """加载历史告警并构建索引"""
        self._historical_alerts = alerts
        self._alert_retriever = AlertRetriever(alerts)

    def search_knowledge(self, query: str, top_k: int = 5,
                         category: str = None, service: str = None) -> List[Dict[str, Any]]:
        """搜索知识库"""
        if not self._knowledge_retriever:
            return []
        return self._knowledge_retriever.search(query, top_k, category, service)

    def search_knowledge_by_tags(self, tags: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """按标签搜索知识库"""
        if not self._knowledge_retriever:
            return []
        return self._knowledge_retriever.search_by_tags(tags, top_k)

    def find_similar_alerts(self, alert_dict: Dict[str, Any],
                            top_k: int = 5, service: str = None) -> List[Dict[str, Any]]:
        """查找相似历史告警"""
        if not self._alert_retriever:
            return []
        return self._alert_retriever.find_similar(alert_dict, top_k, service)

    def get_alert_frequency(self, metric_name: str, service: str = None,
                            days: int = 30) -> Dict[str, Any]:
        """获取告警频率统计"""
        if not self._alert_retriever:
            return {"metric_name": metric_name, "total_count": 0}
        return self._alert_retriever.get_alert_frequency(metric_name, service, days)

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """获取知识库统计"""
        categories = {}
        for entry in self._knowledge_entries:
            cat = entry.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_entries": len(self._knowledge_entries),
            "category_distribution": categories,
            "avg_rating": round(
                sum(e.get("rating", 0) for e in self._knowledge_entries) / max(len(self._knowledge_entries), 1),
                2,
            ),
            "total_usage": sum(e.get("usage_count", 0) for e in self._knowledge_entries),
        }

    def get_historical_alert_stats(self) -> Dict[str, Any]:
        """获取历史告警统计"""
        severity_counts = {}
        status_counts = {}
        service_counts = {}

        for alert in self._historical_alerts:
            sev = alert.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

            status = alert.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            svc = alert.get("service", "unknown")
            service_counts[svc] = service_counts.get(svc, 0) + 1

        return {
            "total_alerts": len(self._historical_alerts),
            "severity_distribution": severity_counts,
            "status_distribution": status_counts,
            "top_services": sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        }


_knowledge_service: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service
