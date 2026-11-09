"""Agent测试"""
import pytest
from app.agents.detection_agent import DetectionAgent
from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.remediation_agent import RemediationAgent
from app.agents.report_agent import ReportAgent


class TestDetectionAgent:
    """检测分级Agent测试"""

    def test_analyze_returns_level(self, init_test_data, sample_alert):
        agent = DetectionAgent()
        result = agent.analyze(sample_alert)
        assert result["agent"] == "DetectionAgent"
        assert result["level"] in ("P0", "P1", "P2", "P3")
        assert 0 <= result["level_score"] <= 100
        assert result["status"] == "completed"

    def test_critical_alert_high_score(self, init_test_data, sample_alert):
        agent = DetectionAgent()
        result = agent.analyze(sample_alert)
        # critical告警分数应该较高
        assert result["level_score"] >= 40

    def test_impact_scope_included(self, init_test_data, sample_alert):
        agent = DetectionAgent()
        result = agent.analyze(sample_alert)
        assert "impact_scope" in result
        assert "business_priority" in result["impact_scope"]

    def test_level_reason_provided(self, init_test_data, sample_alert):
        agent = DetectionAgent()
        result = agent.analyze(sample_alert)
        assert len(result["level_reason"]) > 0


class TestDiagnosisAgent:
    """根因诊断Agent测试"""

    def test_analyze_returns_hypotheses(self, init_test_data, sample_db_alert):
        detection = {"level": "P1", "level_score": 80, "impact_scope": {}}
        agent = DiagnosisAgent()
        result = agent.analyze(sample_db_alert, detection)
        assert result["agent"] == "DiagnosisAgent"
        assert len(result["hypotheses"]) > 0
        assert result["top_root_cause"] is not None
        assert "confidence" in result["top_root_cause"]

    def test_hypothesis_confidence(self, init_test_data, sample_db_alert):
        detection = {"level": "P1", "level_score": 80, "impact_scope": {}}
        agent = DiagnosisAgent()
        result = agent.analyze(sample_db_alert, detection)
        top = result["top_root_cause"]
        assert 0 < top["confidence"] <= 1

    def test_similar_alerts_found(self, init_test_data, sample_alert):
        detection = {"level": "P2", "level_score": 60, "impact_scope": {}}
        agent = DiagnosisAgent()
        result = agent.analyze(sample_alert, detection)
        assert "similar_alerts_count" in result

    def test_related_knowledge(self, init_test_data, sample_db_alert):
        detection = {"level": "P1", "level_score": 80, "impact_scope": {}}
        agent = DiagnosisAgent()
        result = agent.analyze(sample_db_alert, detection)
        assert "related_knowledge" in result


class TestRemediationAgent:
    """处置建议Agent测试"""

    def test_generate_steps(self, init_test_data, sample_db_alert):
        detection = {"level": "P1", "level_score": 80}
        diagnosis = {
            "top_root_cause": {
                "id": "h1",
                "description": "慢查询导致连接池耗尽",
                "category": "database",
                "confidence": 0.85,
            },
            "hypotheses": [],
        }
        agent = RemediationAgent()
        result = agent.analyze(sample_db_alert, diagnosis, detection)
        assert result["agent"] == "RemediationAgent"
        assert len(result["remediation_steps"]) > 0
        assert result["estimated_total_time_minutes"] > 0

    def test_risk_level(self, init_test_data, sample_db_alert):
        detection = {"level": "P1", "level_score": 80}
        diagnosis = {
            "top_root_cause": {
                "description": "测试",
                "category": "database",
                "confidence": 0.8,
            },
            "hypotheses": [],
        }
        agent = RemediationAgent()
        result = agent.analyze(sample_db_alert, diagnosis, detection)
        assert result["overall_risk_level"] in ("low", "medium", "high")

    def test_rollback_plan(self, init_test_data, sample_db_alert):
        detection = {"level": "P1", "level_score": 80}
        diagnosis = {
            "top_root_cause": {
                "description": "测试",
                "category": "infrastructure",
                "confidence": 0.8,
            },
            "hypotheses": [],
        }
        agent = RemediationAgent()
        result = agent.analyze(sample_db_alert, diagnosis, detection)
        assert "rollback_plan" in result

    def test_step_order(self, init_test_data, sample_db_alert):
        detection = {"level": "P2", "level_score": 60}
        diagnosis = {
            "top_root_cause": {
                "description": "测试",
                "category": "application",
                "confidence": 0.7,
            },
            "hypotheses": [],
        }
        agent = RemediationAgent()
        result = agent.analyze(sample_db_alert, diagnosis, detection)
        steps = result["remediation_steps"]
        # 检查步骤顺序正确
        orders = [s["order"] for s in steps]
        assert orders == sorted(orders)


class TestReportAgent:
    """报告生成Agent测试"""

    def test_generate_postmortem(self, init_test_data, sample_alert):
        detection = {"level": "P1", "level_score": 80, "impact_scope": {"impact_level": "high"}}
        diagnosis = {
            "top_root_cause": {
                "description": "CPU资源耗尽",
                "category": "infrastructure",
                "confidence": 0.85,
            },
            "hypotheses": [],
        }
        remediation = {
            "remediation_steps": [{"action": "step1", "order": 1}],
            "estimated_total_time_minutes": 30,
        }
        agent = ReportAgent()
        result = agent.generate_report(sample_alert, detection, diagnosis, remediation)
        assert result["agent"] == "ReportAgent"
        assert "postmortem" in result
        assert "timeline" in result
        assert len(result["timeline"]) > 0

    def test_timeline_includes_all_steps(self, init_test_data, sample_alert):
        detection = {"level": "P2", "level_score": 60, "impact_scope": {}}
        diagnosis = {"top_root_cause": {"description": "test", "category": "app", "confidence": 0.7}, "hypotheses": []}
        remediation = {"remediation_steps": [], "estimated_total_time_minutes": 10}
        agent = ReportAgent()
        result = agent.generate_report(sample_alert, detection, diagnosis, remediation)
        events = [t["event"] for t in result["timeline"]]
        assert "告警触发" in events
        assert "检测分级完成" in events
        assert "根因诊断完成" in events

    def test_action_items(self, init_test_data, sample_alert):
        detection = {"level": "P0", "level_score": 95, "impact_scope": {}}
        diagnosis = {"top_root_cause": {"description": "test", "category": "infra", "confidence": 0.9}, "hypotheses": []}
        remediation = {"remediation_steps": [], "estimated_total_time_minutes": 30}
        agent = ReportAgent()
        result = agent.generate_report(sample_alert, detection, diagnosis, remediation)
        assert len(result["postmortem"]["action_items"]) > 0
