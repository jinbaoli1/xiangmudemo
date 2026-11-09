"""模拟数据生成模块"""
from .cmdb_data import generate_cmdb_data
from .alert_rules import generate_alert_rules
from .historical_alerts import generate_historical_alerts
from .log_samples import generate_log_samples
from .knowledge_base import generate_knowledge_base

__all__ = [
    "generate_cmdb_data",
    "generate_alert_rules",
    "generate_historical_alerts",
    "generate_log_samples",
    "generate_knowledge_base",
]
