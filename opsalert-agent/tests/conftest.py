"""pytest 配置和公共fixture"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def init_test_data():
    """初始化测试数据 - 整个测试会话执行一次"""
    from app.data.cmdb_data import generate_cmdb_data
    from app.data.alert_rules import generate_alert_rules
    from app.data.historical_alerts import generate_historical_alerts
    from app.data.log_samples import generate_log_samples
    from app.data.knowledge_base import generate_knowledge_base
    from app.services.cmdb_service import get_cmdb_service
    from app.services.knowledge_service import get_knowledge_service
    from app.services.log_service import get_log_service

    nodes, relations, service_deps = generate_cmdb_data()
    cmdb_service = get_cmdb_service()
    cmdb_service.load_data(nodes, relations, service_deps)

    rules = generate_alert_rules()
    nodes_dict_list = [n.model_dump() for n in nodes]
    hist_alerts = generate_historical_alerts(nodes_dict_list, rules)
    log_samples = generate_log_samples(nodes_dict_list, 100)
    kb_entries = generate_knowledge_base()

    log_service = get_log_service()
    log_service.set_log_samples(log_samples)

    knowledge_service = get_knowledge_service()
    knowledge_service.load_knowledge_base(kb_entries)
    knowledge_service.load_historical_alerts(hist_alerts)

    yield


@pytest.fixture
def sample_alert():
    """示例告警数据"""
    return {
        "id": "test-alert-001",
        "alert_name": "CPU使用率过高",
        "severity": "critical",
        "status": "open",
        "host": "order-service-01.prod.local",
        "service": "order-service",
        "metric_name": "cpu_usage",
        "metric_value": 95.5,
        "threshold": 90,
        "unit": "%",
        "summary": "CPU使用率过高: order-service-01 cpu_usage=95.5%",
        "description": "订单服务CPU使用率持续超过90%阈值",
        "fingerprint": "abc123def456",
        "labels": {"env": "prod"},
        "tags": ["cpu", "critical"],
    }


@pytest.fixture
def sample_db_alert():
    """数据库告警示例"""
    return {
        "id": "test-alert-002",
        "alert_name": "数据库连接池耗尽",
        "severity": "critical",
        "status": "open",
        "host": "order-service-01.prod.local",
        "service": "order-service",
        "metric_name": "db_connections",
        "metric_value": 96.0,
        "threshold": 90,
        "unit": "%",
        "summary": "数据库连接池使用率超过90%",
        "fingerprint": "dbconn123",
        "tags": ["database"],
    }
