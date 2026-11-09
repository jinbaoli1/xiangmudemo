"""日志服务"""
from typing import List, Dict, Any, Optional
from app.tools.tools_impl import query_logs


class LogService:
    """日志查询服务"""

    def __init__(self):
        self._log_samples: List[Dict[str, Any]] = []

    def set_log_samples(self, samples: List[Dict[str, Any]]):
        self._log_samples = samples

    def search_logs(self, host: str, service: str, keywords: List[str] = None,
                    level: str = "ERROR", limit: int = 20,
                    time_range_minutes: int = 30) -> Dict[str, Any]:
        # 优先从样本中过滤
        if self._log_samples:
            filtered = [
                log for log in self._log_samples
                if log.get("service") == service and log.get("level") == level
            ]
            if host:
                filtered = [l for l in filtered if l.get("host") == host]
            if keywords:
                kw_lower = [k.lower() for k in keywords]
                filtered = [
                    l for l in filtered
                    if any(kw in l.get("message", "").lower() for kw in kw_lower)
                ]
            return {
                "host": host,
                "service": service,
                "level": level,
                "total_found": len(filtered),
                "logs": filtered[:limit],
                "source": "samples",
            }
        # 否则使用模拟工具
        return query_logs(host, service, keywords, level, limit, time_range_minutes)

    def get_error_summary(self, service: str, host: str = None,
                          time_range_minutes: int = 60) -> Dict[str, Any]:
        """获取错误日志统计摘要"""
        logs = self.search_logs(host or "all", service, level="ERROR",
                                limit=50, time_range_minutes=time_range_minutes)
        error_types = {}
        for log in logs.get("logs", []):
            category = log.get("metadata", {}).get("category", "unknown")
            error_types[category] = error_types.get(category, 0) + 1

        return {
            "service": service,
            "total_errors": logs.get("total_found", 0),
            "error_type_distribution": error_types,
            "top_errors": sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5],
            "sample_logs": logs.get("logs", [])[:5],
        }


_log_service: Optional[LogService] = None


def get_log_service() -> LogService:
    global _log_service
    if _log_service is None:
        _log_service = LogService()
    return _log_service
