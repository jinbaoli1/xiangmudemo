"""历史告警模拟数据 - 200+历史告警"""
import hashlib
import random
from datetime import datetime, timedelta
from typing import List
from app.models.alert import Alert, AlertSeverity, AlertStatus


def generate_historical_alerts(nodes_info: list, rules: list) -> List[dict]:
    """生成200+历史告警记录"""
    alerts = []
    random.seed(42)

    services = [
        "gateway-service", "user-service", "order-service", "payment-service",
        "product-service", "inventory-service", "search-service",
        "recommend-service", "message-service", "auth-service",
    ]
    hosts_by_service = {}
    for n in nodes_info:
        if n.get("service") and n.get("node_type") == "service":
            svc = n["service"]
            if svc not in hosts_by_service:
                hosts_by_service[svc] = []
            hosts_by_service[svc].append(n["hostname"] or n["name"])

    # 基础设施主机
    infra_hosts = []
    for n in nodes_info:
        if n.get("node_type") in ("database", "cache", "queue", "middleware", "load_balancer"):
            infra_hosts.append((n["hostname"] or n["name"], n.get("service", "infra")))

    alert_id = 0
    now = datetime.now()

    # 生成过去30天的告警
    for day in range(30):
        day_offset = timedelta(days=day)
        base_time = now - day_offset

        # 每天生成5-12条告警
        daily_count = random.randint(5, 12)
        for _ in range(daily_count):
            rule = random.choice(rules)
            severity = AlertSeverity.CRITICAL if rule["severity"] == "critical" else (
                AlertSeverity.WARNING if rule["severity"] == "warning" else AlertSeverity.INFO
            )

            # 选择主机
            if rule["category"] in ("application", "business"):
                svc = random.choice(services)
                hosts = hosts_by_service.get(svc, [f"{svc}-01.prod.local"])
                host = random.choice(hosts)
                service = svc
            elif rule["category"] == "database":
                db_hosts = [(h, s) for h, s in infra_hosts if "mysql" in h.lower() or "redis" in h.lower()]
                if db_hosts:
                    host, service = random.choice(db_hosts)
                else:
                    host, service = "mysql-master-01.prod.local", "mysql-cluster"
            elif rule["category"] == "middleware":
                mw_hosts = [(h, s) for h, s in infra_hosts if any(x in h.lower() for x in ["nginx", "rabbit", "kafka", "elastic"])]
                if mw_hosts:
                    host, service = random.choice(mw_hosts)
                else:
                    host, service = "rabbitmq-01.prod.local", "rabbitmq-cluster"
            else:  # system, network
                sys_hosts = [(h, s) for h, s in infra_hosts if s in hosts_by_service]
                if sys_hosts:
                    host, service = random.choice(sys_hosts)
                else:
                    svc = random.choice(services)
                    hosts = hosts_by_service.get(svc, [f"{svc}-01.prod.local"])
                    host = random.choice(hosts)
                    service = svc

            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            starts_at = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 告警持续时间
            duration_minutes = random.choice([5, 10, 15, 30, 60, 120, 180])
            ends_at = starts_at + timedelta(minutes=duration_minutes)

            # 告警状态分布：大部分已解决
            status_weights = [0.7, 0.1, 0.15, 0.05]
            statuses = [AlertStatus.RESOLVED, AlertStatus.ACKNOWLEDGED, AlertStatus.OPEN, AlertStatus.SUPPRESSED]
            status = random.choices(statuses, weights=status_weights, k=1)[0]

            metric_value = rule["critical_threshold"] * random.uniform(1.0, 1.5)
            threshold = rule["critical_threshold"]
            if severity == AlertSeverity.WARNING:
                metric_value = rule["warning_threshold"] * random.uniform(1.0, 1.3)
                threshold = rule["warning_threshold"]

            fingerprint_src = f"{rule['metric_name']}|{host}|{service}"
            fingerprint = hashlib.md5(fingerprint_src.encode()).hexdigest()[:16]

            alert = {
                "id": f"hist-alert-{alert_id:05d}",
                "alert_name": rule["name"],
                "severity": severity.value,
                "status": status.value,
                "level": _random_level(severity),
                "level_score": round(random.uniform(30, 95), 1),
                "host": host,
                "service": service,
                "metric_name": rule["metric_name"],
                "metric_value": round(metric_value, 2),
                "threshold": threshold,
                "unit": _get_unit(rule["metric_name"]),
                "summary": f"{rule['name']}: {host} {rule['metric_name']}={round(metric_value,2)} (阈值={threshold})",
                "description": rule["description"],
                "labels": {
                    "category": rule["category"],
                    "environment": "prod",
                    "region": "cn-east-1",
                },
                "annotations": {
                    "runbook": f"https://wiki.example.com/runbook/{rule['id']}",
                    "dashboard": f"https://grafana.example.com/d/{service}",
                },
                "fingerprint": fingerprint,
                "generator_url": f"https://prometheus.example.com",
                "starts_at": starts_at.isoformat(),
                "ends_at": ends_at.isoformat() if status == AlertStatus.RESOLVED else None,
                "created_at": starts_at.isoformat(),
                "updated_at": (ends_at if status == AlertStatus.RESOLVED else starts_at).isoformat(),
                "incident_id": f"inc-{random.randint(1000, 9999)}" if random.random() < 0.3 else None,
                "ticket_id": f"OPS-{random.randint(10000, 99999)}" if random.random() < 0.4 else None,
                "tags": [rule["category"], severity.value],
                "extra": {
                    "rule_id": rule["id"],
                    "duration_minutes": duration_minutes,
                    "resolved_by": random.choice(["oncall-a", "oncall-b", "auto-recovery", "dba-team"]) if status == AlertStatus.RESOLVED else None,
                },
            }
            alerts.append(alert)
            alert_id += 1

    # 确保至少200条
    while len(alerts) < 210:
        day = random.randint(0, 30)
        rule = random.choice(rules)
        severity = AlertSeverity.CRITICAL if rule["severity"] == "critical" else AlertSeverity.WARNING
        svc = random.choice(services)
        hosts = hosts_by_service.get(svc, [f"{svc}-01.prod.local"])
        host = random.choice(hosts)
        starts_at = now - timedelta(days=day, hours=random.randint(0, 23))

        fingerprint_src = f"{rule['metric_name']}|{host}|{svc}-{alert_id}"
        fingerprint = hashlib.md5(fingerprint_src.encode()).hexdigest()[:16]

        alert = {
            "id": f"hist-alert-{alert_id:05d}",
            "alert_name": rule["name"],
            "severity": severity.value,
            "status": "resolved",
            "level": _random_level(severity),
            "level_score": round(random.uniform(30, 95), 1),
            "host": host,
            "service": svc,
            "metric_name": rule["metric_name"],
            "metric_value": round(rule["critical_threshold"] * random.uniform(1.0, 1.5), 2),
            "threshold": rule["critical_threshold"],
            "unit": _get_unit(rule["metric_name"]),
            "summary": f"{rule['name']}: {host}",
            "description": rule["description"],
            "labels": {"category": rule["category"], "environment": "prod"},
            "annotations": {},
            "fingerprint": fingerprint,
            "generator_url": "https://prometheus.example.com",
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(minutes=random.randint(10, 120))).isoformat(),
            "created_at": starts_at.isoformat(),
            "updated_at": starts_at.isoformat(),
            "incident_id": None,
            "ticket_id": None,
            "tags": [rule["category"]],
            "extra": {"rule_id": rule["id"]},
        }
        alerts.append(alert)
        alert_id += 1

    return alerts


def _random_level(severity: AlertSeverity) -> str:
    if severity == AlertSeverity.CRITICAL:
        return random.choices(["P0", "P1", "P2"], weights=[0.3, 0.5, 0.2], k=1)[0]
    elif severity == AlertSeverity.WARNING:
        return random.choices(["P1", "P2", "P3"], weights=[0.1, 0.5, 0.4], k=1)[0]
    else:
        return "P3"


def _get_unit(metric_name: str) -> str:
    if any(k in metric_name for k in ["usage", "rate", "hit_rate"]):
        return "%"
    elif any(k in metric_name for k in ["time", "latency", "duration", "wait"]):
        return "ms"
    elif any(k in metric_name for k in ["bytes", "memory", "disk"]):
        return "bytes"
    elif any(k in metric_name for k in ["count", "number", "connections"]):
        return "count"
    elif "qps" in metric_name:
        return "qps"
    elif "lag" in metric_name:
        return "s"
    return ""
