"""指标服务"""
from typing import List, Dict, Any, Optional
from app.tools.tools_impl import query_metrics


class MetricService:
    """指标查询服务"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def get_metrics(self, host: str, metric_names: List[str],
                    service: str = None, time_range_minutes: int = 30) -> Dict[str, Any]:
        return query_metrics(host, metric_names, service, time_range_minutes)

    def get_current_value(self, host: str, metric_name: str, service: str = None) -> Optional[float]:
        result = query_metrics(host, [metric_name], service, 5)
        metrics = result.get("metrics", {})
        metric_data = metrics.get(metric_name, {})
        return metric_data.get("current_value")

    def get_metric_trend(self, host: str, metric_name: str,
                         service: str = None, time_range_minutes: int = 60) -> Dict[str, Any]:
        result = query_metrics(host, [metric_name], service, time_range_minutes)
        metric_data = result.get("metrics", {}).get(metric_name, {})
        return {
            "metric_name": metric_name,
            "host": host,
            "service": service,
            "trend": metric_data.get("trend", "stable"),
            "current": metric_data.get("current_value"),
            "avg": metric_data.get("avg_value"),
            "max": metric_data.get("max_value"),
            "min": metric_data.get("min_value"),
            "data_points": metric_data.get("data_points", []),
        }


_metric_service: Optional[MetricService] = None


def get_metric_service() -> MetricService:
    global _metric_service
    if _metric_service is None:
        _metric_service = MetricService()
    return _metric_service
