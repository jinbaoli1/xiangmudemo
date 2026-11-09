"""服务层和状态机测试"""
import pytest
from app.services.alert_service import AlertService
from app.services.cmdb_service import CMDBService
from app.services.incident_service import IncidentService
from app.graph import OpsAlertGraph


class TestAlertService:
    """告警服务测试"""

    def test_create_alert(self):
        service = AlertService()
        alert = service.create_alert({
            "alert_name": "测试告警",
            "severity": "warning",
            "host": "host1",
            "service": "svc1",
            "metric_name": "cpu_usage",
            "metric_value": 85,
            "threshold": 80,
        })
        assert "id" in alert
        assert alert["status"] == "open"
        assert "fingerprint" in alert

    def test_alert_deduplication(self):
        """测试相同指纹告警去重"""
        service = AlertService()
        a1 = service.create_alert({
            "alert_name": "测试告警",
            "severity": "warning",
            "host": "host1",
            "service": "svc1",
            "metric_name": "cpu_usage",
            "metric_value": 85,
            "threshold": 80,
        })
        a2 = service.create_alert({
            "alert_name": "测试告警2",
            "severity": "warning",
            "host": "host1",
            "service": "svc1",
            "metric_name": "cpu_usage",
            "metric_value": 88,
            "threshold": 80,
        })
        # 相同指纹应该返回同一个告警（更新）
        assert a1["id"] == a2["id"]

    def test_update_alert(self):
        service = AlertService()
        alert = service.create_alert({
            "alert_name": "测试",
            "severity": "warning",
            "host": "h1",
            "service": "s1",
            "metric_name": "m1",
            "metric_value": 10,
            "threshold": 5,
        })
        updated = service.update_alert(alert["id"], {"level": "P2", "level_score": 65})
        assert updated["level"] == "P2"
        assert updated["level_score"] == 65

    def test_count_by_level(self, init_test_data):
        from app.services.alert_service import get_alert_service
        service = get_alert_service()
        counts = service.count_by_level()
        assert "P0" in counts
        assert "P1" in counts
        assert "P2" in counts
        assert "P3" in counts


class TestCMDBService:
    """CMDB服务测试"""

    def test_get_topology(self, init_test_data):
        from app.services.cmdb_service import get_cmdb_service
        service = get_cmdb_service()
        topology = service.get_topology("order-service")
        assert "upstream_services" in topology
        assert "downstream_services" in topology

    def test_calculate_impact(self, init_test_data):
        from app.services.cmdb_service import get_cmdb_service
        service = get_cmdb_service()
        impact = service.calculate_impact_scope("order-service")
        assert "impact_score" in impact
        assert "impact_level" in impact
        assert impact["impact_level"] in ("critical", "high", "medium")

    def test_business_priority(self, init_test_data):
        from app.services.cmdb_service import get_cmdb_service
        service = get_cmdb_service()
        p = service.get_business_priority("payment-service")
        assert p >= 4  # 支付服务应该是高优先级


class TestIncidentService:
    """事故服务测试"""

    def test_create_incident(self):
        service = IncidentService()
        alert = {
            "id": "a1",
            "alert_name": "测试告警",
            "service": "order-service",
            "host": "h1",
            "starts_at": "2024-01-01T00:00:00",
        }
        incident = service.create_incident(alert, severity="SEV2")
        assert incident["id"].startswith("inc-")
        assert incident["severity"] == "SEV2"
        assert incident["status"] == "open"

    def test_ticket_idempotency(self):
        """测试工单幂等性"""
        service = IncidentService()
        alert = {
            "id": "a1",
            "alert_name": "测试",
            "service": "s1",
            "host": "h1",
            "starts_at": "2024-01-01T00:00:00",
        }
        analysis = {}
        t1 = service.create_ticket(alert, analysis)
        t2 = service.create_ticket(alert, analysis)
        assert t1["id"] == t2["id"]
        assert t2["is_new"] == False

    def test_notify_oncall(self):
        service = IncidentService()
        alert = {
            "id": "a1", "alert_name": "test", "service": "order-service",
            "host": "h1", "starts_at": "2024-01-01T00:00:00",
        }
        incident = service.create_incident(alert, "SEV2")
        result = service.notify_oncall(incident["id"])
        assert result["success"] == True
        assert "notified_team" in result


class TestOpsAlertGraph:
    """状态机测试"""

    def test_initial_state(self, sample_alert):
        graph = OpsAlertGraph()
        state = graph.create_initial_state(sample_alert)
        assert state["trace_id"].startswith("trace-")
        assert state["status"] == "pending"
        assert state["current_step"] == "init"
        assert len(state["agent_steps"]) == 0

    def test_full_run(self, init_test_data, sample_alert):
        """完整运行测试"""
        graph = OpsAlertGraph()
        result = graph.run(sample_alert)

        assert result["status"] == "completed"
        assert result["level"] in ("P0", "P1", "P2", "P3")
        assert result["top_root_cause"] is not None
        assert len(result["remediation_steps"]) > 0
        assert result["postmortem"] is not None
        assert len(result["agent_steps"]) >= 5  # 至少5步

    def test_stream_events(self, init_test_data, sample_alert):
        """测试流式事件回调"""
        events = []

        def callback(event, data):
            events.append((event, data))

        graph = OpsAlertGraph()
        graph.run(sample_alert, stream_callback=callback)

        assert len(events) > 0
        event_types = [e[0] for e in events]
        assert "start" in event_types
        assert "step" in event_types
        assert "complete" in event_types

    def test_result_structure(self, init_test_data, sample_alert):
        """测试结果结构完整性"""
        graph = OpsAlertGraph()
        result = graph.run(sample_alert)

        required_fields = [
            "trace_id", "alert_id", "level", "level_score",
            "top_root_cause", "remediation_steps", "postmortem",
            "agent_steps", "status", "timeline",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
