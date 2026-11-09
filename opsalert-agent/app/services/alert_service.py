"""告警服务"""
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertLevel


class AlertService:
    """告警管理服务"""

    def __init__(self):
        self._alerts: Dict[str, Dict[str, Any]] = {}
        self._fingerprint_index: Dict[str, str] = {}  # fingerprint -> alert_id

    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建告警"""
        alert_id = alert_data.get("id") or f"alert-{uuid.uuid4().hex[:12]}"

        # 生成指纹
        fingerprint = alert_data.get("fingerprint")
        if not fingerprint:
            fp_src = f"{alert_data.get('metric_name')}|{alert_data.get('host')}|{alert_data.get('service')}"
            fingerprint = hashlib.md5(fp_src.encode()).hexdigest()[:16]

        # 检查是否已存在相同指纹的活跃告警
        existing_id = self._fingerprint_index.get(fingerprint)
        if existing_id and self._alerts.get(existing_id, {}).get("status") == "open":
            # 更新现有告警
            existing = self._alerts[existing_id]
            existing["updated_at"] = datetime.now().isoformat()
            existing["metric_value"] = alert_data.get("metric_value", existing["metric_value"])
            return existing

        alert_dict = {
            "id": alert_id,
            "alert_name": alert_data.get("alert_name", "Unknown Alert"),
            "severity": alert_data.get("severity", "warning"),
            "status": alert_data.get("status", "open"),
            "level": alert_data.get("level"),
            "level_score": alert_data.get("level_score"),
            "host": alert_data.get("host", "unknown"),
            "service": alert_data.get("service", "unknown"),
            "metric_name": alert_data.get("metric_name", "unknown"),
            "metric_value": alert_data.get("metric_value", 0),
            "threshold": alert_data.get("threshold", 0),
            "unit": alert_data.get("unit", "%"),
            "summary": alert_data.get("summary", ""),
            "description": alert_data.get("description", ""),
            "labels": alert_data.get("labels", {}),
            "annotations": alert_data.get("annotations", {}),
            "fingerprint": fingerprint,
            "generator_url": alert_data.get("generator_url", ""),
            "starts_at": alert_data.get("starts_at", datetime.now().isoformat()),
            "ends_at": alert_data.get("ends_at"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "incident_id": alert_data.get("incident_id"),
            "ticket_id": alert_data.get("ticket_id"),
            "tags": alert_data.get("tags", []),
            "extra": alert_data.get("extra", {}),
        }

        self._alerts[alert_id] = alert_dict
        self._fingerprint_index[fingerprint] = alert_id
        return alert_dict

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        return self._alerts.get(alert_id)

    def list_alerts(self, status: str = None, service: str = None,
                    level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        alerts = list(self._alerts.values())
        if status:
            alerts = [a for a in alerts if a.get("status") == status]
        if service:
            alerts = [a for a in alerts if a.get("service") == service]
        if level:
            alerts = [a for a in alerts if a.get("level") == level]
        alerts.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return alerts[:limit]

    def update_alert(self, alert_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if alert_id not in self._alerts:
            return None
        alert = self._alerts[alert_id]
        alert.update(updates)
        alert["updated_at"] = datetime.now().isoformat()
        return alert

    def resolve_alert(self, alert_id: str, resolution: str = "") -> Optional[Dict[str, Any]]:
        return self.update_alert(alert_id, {
            "status": "resolved",
            "ends_at": datetime.now().isoformat(),
            "extra": {"resolution": resolution},
        })

    def acknowledge_alert(self, alert_id: str, assignee: str = "") -> Optional[Dict[str, Any]]:
        return self.update_alert(alert_id, {
            "status": "acknowledged",
            "extra": {"assignee": assignee},
        })

    def count_by_level(self) -> Dict[str, int]:
        counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "unclassified": 0}
        for alert in self._alerts.values():
            if alert.get("status") == "open":
                level = alert.get("level") or "unclassified"
                counts[level] = counts.get(level, 0) + 1
        return counts


_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
