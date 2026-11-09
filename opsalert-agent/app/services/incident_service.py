"""事故管理服务"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


class IncidentService:
    """事故管理服务"""

    def __init__(self):
        self._incidents: Dict[str, Dict[str, Any]] = {}
        self._ticket_store: Dict[str, Dict[str, Any]] = {}
        self._idempotency_keys: set = set()

    def create_incident(self, alert_data: Dict[str, Any], severity: str = "SEV3") -> Dict[str, Any]:
        """创建事故"""
        incident_id = f"inc-{uuid.uuid4().hex[:8]}"

        incident = {
            "id": incident_id,
            "title": f"[{severity}] {alert_data.get('alert_name')} - {alert_data.get('service')}",
            "description": alert_data.get("description", ""),
            "severity": severity,
            "status": "open",
            "alert_ids": [alert_data.get("id")],
            "affected_services": [alert_data.get("service")],
            "affected_hosts": [alert_data.get("host")],
            "root_cause": None,
            "root_cause_category": None,
            "confidence": None,
            "impact_scope": "",
            "impact_duration_minutes": None,
            "assignee": "",
            "on_call_team": self._get_oncall_team(alert_data.get("service", "")),
            "started_at": alert_data.get("starts_at", datetime.now().isoformat()),
            "detected_at": datetime.now().isoformat(),
            "acknowledged_at": None,
            "resolved_at": None,
            "closed_at": None,
            "timeline": [
                {
                    "time": datetime.now().isoformat(),
                    "event": "事故创建",
                    "description": f"由告警 {alert_data.get('id')} 触发自动创建事故",
                }
            ],
            "tags": [severity, alert_data.get("service", "")],
            "extra": {},
        }

        self._incidents[incident_id] = incident
        return incident

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return self._incidents.get(incident_id)

    def list_incidents(self, status: str = None, severity: str = None,
                       limit: int = 50) -> List[Dict[str, Any]]:
        incidents = list(self._incidents.values())
        if status:
            incidents = [i for i in incidents if i.get("status") == status]
        if severity:
            incidents = [i for i in incidents if i.get("severity") == severity]
        incidents.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return incidents[:limit]

    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if incident_id not in self._incidents:
            return None
        incident = self._incidents[incident_id]
        incident.update(updates)
        return incident

    def add_timeline_event(self, incident_id: str, event: str, description: str = "") -> Optional[Dict[str, Any]]:
        if incident_id not in self._incidents:
            return None
        incident = self._incidents[incident_id]
        incident["timeline"].append({
            "time": datetime.now().isoformat(),
            "event": event,
            "description": description,
        })
        return incident

    def set_root_cause(self, incident_id: str, root_cause: str, category: str,
                       confidence: float) -> Optional[Dict[str, Any]]:
        return self.update_incident(incident_id, {
            "root_cause": root_cause,
            "root_cause_category": category,
            "confidence": confidence,
            "status": "identified",
        })

    def resolve_incident(self, incident_id: str, resolution: str = "") -> Optional[Dict[str, Any]]:
        now = datetime.now().isoformat()
        self.add_timeline_event(incident_id, "故障恢复", resolution)
        return self.update_incident(incident_id, {
            "status": "resolved",
            "resolved_at": now,
        })

    def create_ticket(self, alert_data: Dict[str, Any], analysis_result: Dict[str, Any],
                      priority: str = "Medium", assignee: str = "") -> Dict[str, Any]:
        """创建工单（带幂等控制）"""
        from app.tools.tools_impl import create_ticket as create_ticket_tool
        import hashlib

        idempotency_key = hashlib.md5(f"ticket:{alert_data.get('id')}".encode()).hexdigest()

        # 幂等检查
        if idempotency_key in self._idempotency_keys:
            # 返回已存在的工单
            for ticket in self._ticket_store.values():
                if ticket.get("idempotency_key") == idempotency_key:
                    ticket["is_new"] = False
                    return ticket

        ticket = create_ticket_tool(alert_data, analysis_result, priority, assignee)
        self._ticket_store[ticket["id"]] = ticket
        self._idempotency_keys.add(idempotency_key)
        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        return self._ticket_store.get(ticket_id)

    def _get_oncall_team(self, service: str) -> str:
        """获取对应服务的值班团队"""
        team_map = {
            "order-service": "order-team-oncall",
            "payment-service": "payment-team-oncall",
            "user-service": "user-team-oncall",
            "product-service": "product-team-oncall",
            "gateway-service": "platform-team-oncall",
            "mysql-cluster": "dba-team-oncall",
            "redis-cluster": "cache-team-oncall",
            "rabbitmq-cluster": "middleware-team-oncall",
            "elasticsearch-cluster": "search-team-oncall",
        }
        return team_map.get(service, "sre-team-oncall")

    def notify_oncall(self, incident_id: str) -> Dict[str, Any]:
        """模拟通知On-Call"""
        incident = self._incidents.get(incident_id)
        if not incident:
            return {"success": False, "message": "Incident not found"}

        team = incident.get("on_call_team", "sre-team-oncall")
        # 模拟通知
        return {
            "success": True,
            "incident_id": incident_id,
            "notified_team": team,
            "channels": ["phone", "sms", "lark"],
            "message": f"[{incident['severity']}] {incident['title']}",
            "notified_at": datetime.now().isoformat(),
        }


_incident_service: Optional[IncidentService] = None


def get_incident_service() -> IncidentService:
    global _incident_service
    if _incident_service is None:
        _incident_service = IncidentService()
    return _incident_service
