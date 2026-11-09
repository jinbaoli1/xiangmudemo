"""数据模型测试"""
import pytest
from datetime import datetime
from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertLevel
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.knowledge import KnowledgeEntry
from app.models.analysis import AnalysisResult, RootCauseHypothesis, RemediationStep


class TestAlertModel:
    """告警模型测试"""

    def test_create_alert(self):
        """测试创建告警"""
        alert = Alert(
            id="alert-001",
            alert_name="CPU过高",
            severity=AlertSeverity.CRITICAL,
            host="server-01",
            service="order-service",
            metric_name="cpu_usage",
            metric_value=95.5,
            threshold=90,
            summary="CPU使用率过高",
            fingerprint="fp001",
        )
        assert alert.id == "alert-001"
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == AlertStatus.OPEN
        assert alert.metric_value == 95.5
        assert alert.level is None

    def test_alert_levels(self):
        """测试告警级别枚举"""
        assert AlertLevel.P0 == "P0"
        assert AlertLevel.P1 == "P1"
        assert AlertLevel.P2 == "P2"
        assert AlertLevel.P3 == "P3"

    def test_alert_defaults(self):
        """测试告警默认值"""
        alert = Alert(
            id="a1",
            alert_name="test",
            severity=AlertSeverity.WARNING,
            host="h1",
            service="s1",
            metric_name="m1",
            metric_value=10,
            threshold=5,
            summary="test",
            fingerprint="fp1",
        )
        assert alert.status == AlertStatus.OPEN
        assert alert.unit == "%"
        assert isinstance(alert.labels, dict)
        assert isinstance(alert.tags, list)
        assert alert.level is None


class TestTicketModel:
    """工单模型测试"""

    def test_create_ticket(self):
        ticket = Ticket(
            id="OPS-12345",
            title="测试工单",
            priority=TicketPriority.HIGH,
        )
        assert ticket.id == "OPS-12345"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.priority == TicketPriority.HIGH


class TestIncidentModel:
    """事故模型测试"""

    def test_create_incident(self):
        incident = Incident(
            id="inc-001",
            title="测试事故",
            severity=IncidentSeverity.SEV2,
        )
        assert incident.id == "inc-001"
        assert incident.status == IncidentStatus.OPEN
        assert incident.severity == IncidentSeverity.SEV2
        assert isinstance(incident.alert_ids, list)


class TestKnowledgeModel:
    """知识库模型测试"""

    def test_create_entry(self):
        entry = KnowledgeEntry(
            id="kb-001",
            title="测试知识库条目",
            category="troubleshooting",
            steps=["步骤1", "步骤2"],
        )
        assert entry.id == "kb-001"
        assert entry.category == "troubleshooting"
        assert len(entry.steps) == 2


class TestAnalysisModel:
    """分析结果模型测试"""

    def test_create_analysis_result(self):
        result = AnalysisResult(
            trace_id="trace-001",
            alert_id="alert-001",
            status="pending",
        )
        assert result.trace_id == "trace-001"
        assert result.status == "pending"
        assert isinstance(result.root_cause_hypotheses, list)
        assert isinstance(result.remediation_steps, list)

    def test_root_cause_hypothesis(self):
        hypo = RootCauseHypothesis(
            id="hypo-01",
            description="CPU资源耗尽",
            confidence=0.85,
            category="infrastructure",
        )
        assert hypo.confidence == 0.85
        assert hypo.category == "infrastructure"

    def test_remediation_step(self):
        step = RemediationStep(
            order=1,
            action="检查CPU使用",
            risk_level="low",
            estimated_time_minutes=5,
        )
        assert step.order == 1
        assert step.risk_level == "low"
