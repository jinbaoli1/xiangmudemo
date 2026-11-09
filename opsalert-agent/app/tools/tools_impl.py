"""核心工具函数实现 - 8个Agent工具"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


def query_metrics(host: str, metric_names: List[str], service: str = None,
                  time_range_minutes: int = 30) -> Dict[str, Any]:
    """
    查询监控指标数据
    :param host: 主机名
    :param metric_names: 指标名列表
    :param service: 服务名
    :param time_range_minutes: 时间范围（分钟）
    :return: 指标数据
    """
    random.seed(hash(f"{host}:{','.join(metric_names)}:{service}") % 2**32)
    now = datetime.now()

    results = {}
    for metric in metric_names:
        # 根据指标名生成模拟数据
        base_values = {
            "cpu_usage": (70, 95, "%"),
            "memory_usage": (60, 90, "%"),
            "disk_usage": (50, 85, "%"),
            "disk_io_usage": (30, 80, "%"),
            "network_in_bytes": (100, 500, "Mbps"),
            "network_out_bytes": (100, 500, "Mbps"),
            "load_average": (2, 10, ""),
            "http_error_rate": (1, 15, "%"),
            "http_response_time_p99": (100, 800, "ms"),
            "http_qps": (500, 3000, "qps"),
            "jvm_heap_usage": (50, 90, "%"),
            "jvm_gc_duration": (50, 300, "ms"),
            "db_connections": (40, 90, "%"),
            "db_slow_queries": (0, 20, "count"),
            "db_cpu_usage": (30, 95, "%"),
            "db_replication_lag": (1, 60, "s"),
            "redis_memory_usage": (40, 90, "%"),
            "redis_latency": (1, 30, "ms"),
            "mq_queue_size": (100, 50000, "count"),
            "mq_consume_latency": (5, 300, "s"),
            "cache_hit_rate": (60, 99, "%"),
            "tcp_connections": (1000, 8000, "count"),
            "nginx_connections": (500, 8000, "count"),
            "nginx_error_rate": (0.5, 10, "%"),
        }

        low, high, unit = base_values.get(metric, (10, 100, ""))
        current = round(random.uniform(low, high), 2)

        # 生成时间序列数据点
        data_points = []
        for i in range(time_range_minutes):
            ts = now - timedelta(minutes=time_range_minutes - i)
            variance = random.uniform(-5, 5)
            val = round(max(0, current + variance + random.uniform(-high * 0.1, high * 0.1)), 2)
            data_points.append({
                "timestamp": ts.isoformat(),
                "value": val,
            })

        results[metric] = {
            "current_value": current,
            "unit": unit,
            "host": host,
            "service": service,
            "time_range_minutes": time_range_minutes,
            "avg_value": round(sum(d["value"] for d in data_points) / len(data_points), 2),
            "max_value": round(max(d["value"] for d in data_points), 2),
            "min_value": round(min(d["value"] for d in data_points), 2),
            "trend": "rising" if data_points[-1]["value"] > data_points[0]["value"] else "falling",
            "data_points": data_points,
        }

    return {
        "host": host,
        "service": service,
        "metrics": results,
        "queried_at": now.isoformat(),
    }


def query_logs(host: str, service: str, keywords: List[str] = None,
               level: str = "ERROR", limit: int = 20,
               time_range_minutes: int = 30) -> Dict[str, Any]:
    """
    查询日志
    :param host: 主机名
    :param service: 服务名
    :param keywords: 关键词列表
    :param level: 日志级别
    :param limit: 返回数量
    :param time_range_minutes: 时间范围
    :return: 日志结果
    """
    random.seed(hash(f"{host}:{service}:{level}:{','.join(keywords or [])}") % 2**32)
    now = datetime.now()

    error_patterns = [
        "java.lang.OutOfMemoryError: Java heap space",
        "java.sql.SQLException: Connection refused, too many connections",
        "java.net.SocketTimeoutException: Read timed out",
        "org.springframework.data.redis.RedisConnectionFailureException: Unable to connect to Redis",
        "java.lang.NullPointerException: Cannot invoke method on null object",
        "io.github.resilience4j.circuitbreaker.CallNotPermittedException: CircuitBreaker is OPEN",
        "Slow query detected: SELECT * FROM orders WHERE ... took 5230ms",
        "Deadlock detected between threads: pool-1-thread-23 and pool-1-thread-45",
        "com.mysql.cj.jdbc.exceptions.MySQLTransactionRollbackException: Deadlock found",
        "Rate limit exceeded for client: 192.168.1.100",
        "Connection pool exhausted: active=200, pending=150",
        "GC pause detected: 2345ms, cause: Full GC (Ergonomics)",
        "org.springframework.web.client.HttpServerErrorException: 503 Service Unavailable",
        "FileNotFoundException: /data/config/app.properties",
        "ClassNotFoundException: com.example.plugin.CustomPlugin",
    ]

    warn_patterns = [
        "Request timeout after 30000ms for endpoint /api/v1/orders",
        "High memory usage detected: 85% of heap used",
        "Connection pool near capacity: 85% active",
        "Cache miss rate increasing: current hit rate 72%",
        "Slow consumer detected on queue order.events",
    ]

    patterns = error_patterns if level == "ERROR" else (warn_patterns if level == "WARN" else error_patterns + warn_patterns)

    logs = []
    count = min(limit, random.randint(5, limit))
    for i in range(count):
        minutes_ago = random.randint(0, time_range_minutes)
        seconds_ago = random.randint(0, 59)
        ts = now - timedelta(minutes=minutes_ago, seconds=seconds_ago)

        message = random.choice(patterns)
        if keywords:
            # 确保至少包含一个关键词
            for kw in keywords:
                if kw.lower() in message.lower():
                    break
            else:
                message = f"{message} [keyword: {random.choice(keywords)}]"

        log_entry = {
            "id": f"log-query-{i:04d}",
            "timestamp": ts.isoformat(),
            "host": host,
            "service": service,
            "level": level,
            "message": message,
            "trace_id": f"trace-{random.randint(100000000000, 999999999999)}",
            "source": f"/var/log/{service}/app.log",
            "thread": f"http-nio-8080-exec-{random.randint(1, 200)}",
        }
        logs.append(log_entry)

    logs.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "host": host,
        "service": service,
        "level": level,
        "total_found": len(logs),
        "logs": logs,
        "queried_at": now.isoformat(),
    }


def query_topology(service: str, host: str = None, depth: int = 2) -> Dict[str, Any]:
    """
    查询CMDB拓扑关系
    :param service: 服务名
    :param host: 主机名
    :param depth: 依赖深度
    :return: 拓扑信息
    """
    # 依赖关系映射
    dependency_map = {
        "gateway-service": {
            "upstream": [],
            "downstream": ["user-service", "order-service", "payment-service", "product-service",
                          "inventory-service", "search-service", "recommend-service",
                          "message-service", "auth-service"],
        },
        "order-service": {
            "upstream": ["gateway-service"],
            "downstream": ["user-service", "product-service", "inventory-service", "payment-service",
                          "mysql-cluster", "redis-cluster", "rabbitmq-cluster"],
        },
        "payment-service": {
            "upstream": ["gateway-service", "order-service"],
            "downstream": ["user-service", "mysql-cluster", "redis-cluster"],
        },
        "user-service": {
            "upstream": ["gateway-service", "order-service", "payment-service", "auth-service", "recommend-service"],
            "downstream": ["mysql-cluster", "redis-cluster"],
        },
        "product-service": {
            "upstream": ["gateway-service", "order-service", "search-service", "recommend-service"],
            "downstream": ["inventory-service", "mysql-cluster", "redis-cluster", "elasticsearch-cluster"],
        },
        "inventory-service": {
            "upstream": ["order-service", "product-service"],
            "downstream": ["mysql-cluster", "redis-cluster"],
        },
        "search-service": {
            "upstream": ["gateway-service"],
            "downstream": ["product-service", "elasticsearch-cluster", "redis-cluster"],
        },
        "recommend-service": {
            "upstream": ["gateway-service"],
            "downstream": ["product-service", "user-service", "redis-cluster"],
        },
        "message-service": {
            "upstream": ["gateway-service"],
            "downstream": ["user-service", "rabbitmq-cluster", "mysql-cluster", "redis-cluster"],
        },
        "auth-service": {
            "upstream": ["gateway-service"],
            "downstream": ["user-service", "mysql-cluster", "redis-cluster"],
        },
        "mysql-cluster": {
            "upstream": ["order-service", "payment-service", "user-service", "product-service",
                        "inventory-service", "message-service", "auth-service"],
            "downstream": [],
        },
        "redis-cluster": {
            "upstream": ["order-service", "payment-service", "user-service", "product-service",
                        "inventory-service", "search-service", "recommend-service",
                        "message-service", "auth-service"],
            "downstream": [],
        },
        "rabbitmq-cluster": {
            "upstream": ["order-service", "message-service"],
            "downstream": [],
        },
        "elasticsearch-cluster": {
            "upstream": ["product-service", "search-service"],
            "downstream": [],
        },
    }

    svc_info = dependency_map.get(service, {"upstream": [], "downstream": []})

    # 计算影响范围
    impact_services = set()
    if depth >= 1:
        impact_services.update(svc_info["upstream"])
        impact_services.update(svc_info["downstream"])
    if depth >= 2:
        for dep_svc in list(svc_info["downstream"]):
            dep_info = dependency_map.get(dep_svc, {})
            impact_services.update(dep_info.get("downstream", []))

    # 业务优先级映射
    priority_map = {
        "gateway-service": 5, "user-service": 5, "order-service": 5,
        "payment-service": 5, "product-service": 4, "inventory-service": 4,
        "search-service": 3, "recommend-service": 3, "message-service": 3,
        "auth-service": 4, "mysql-cluster": 5, "redis-cluster": 4,
        "rabbitmq-cluster": 4, "elasticsearch-cluster": 3,
    }

    return {
        "service": service,
        "host": host,
        "depth": depth,
        "upstream_services": svc_info["upstream"],
        "downstream_services": svc_info["downstream"],
        "impact_scope": {
            "direct_upstream_count": len(svc_info["upstream"]),
            "direct_downstream_count": len(svc_info["downstream"]),
            "total_affected_services": len(impact_services),
            "affected_services": sorted(list(impact_services)),
            "business_priority": priority_map.get(service, 3),
            "core_service": priority_map.get(service, 3) >= 4,
        },
        "dependency_map": dependency_map,
    }


def match_history(alert_summary: str, service: str, metric_name: str = None,
                  top_k: int = 5) -> Dict[str, Any]:
    """
    匹配历史相似告警
    :param alert_summary: 告警摘要
    :param service: 服务名
    :param metric_name: 指标名
    :param top_k: 返回数量
    :return: 相似告警列表
    """
    # 注意：实际调用会使用AlertRetriever，这里是工具函数包装
    from app.services.knowledge_service import get_knowledge_service
    try:
        ks = get_knowledge_service()
        alert_dict = {
            "alert_name": alert_summary[:50],
            "summary": alert_summary,
            "service": service,
            "metric_name": metric_name or "",
            "host": "",
            "tags": [],
        }
        similar = ks.find_similar_alerts(alert_dict, top_k=top_k, service=service)
        return {
            "query": alert_summary,
            "service": service,
            "total_found": len(similar),
            "similar_alerts": similar,
        }
    except Exception as e:
        return {
            "query": alert_summary,
            "service": service,
            "total_found": 0,
            "similar_alerts": [],
            "error": str(e),
        }


def analyze_root_cause(alert_data: Dict[str, Any], metrics_data: Dict[str, Any],
                       logs_data: Dict[str, Any], topology_data: Dict[str, Any],
                       similar_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    根因分析工具
    :param alert_data: 告警数据
    :param metrics_data: 指标数据
    :param logs_data: 日志数据
    :param topology_data: 拓扑数据
    :param similar_alerts: 相似告警
    :return: 根因分析结果
    """
    metric_name = alert_data.get("metric_name", "")
    service = alert_data.get("service", "")
    severity = alert_data.get("severity", "warning")

    # 基于规则的根因分析
    hypotheses = []
    hypo_id = 0

    # 规则1: 根据指标名推断根因类别
    category_rules = {
        "cpu_usage": {
            "category": "infrastructure",
            "causes": [
                ("业务流量突增导致CPU使用率升高", 0.4),
                ("应用存在死循环或计算密集型异常", 0.3),
                ("GC频繁导致CPU消耗过高", 0.2),
                ("系统进程或定时任务异常", 0.1),
            ]
        },
        "memory_usage": {
            "category": "infrastructure",
            "causes": [
                ("内存泄漏导致内存持续增长", 0.4),
                ("缓存数据量过大未及时清理", 0.3),
                ("并发量过高导致内存占用增加", 0.2),
                ("JVM堆内存配置不合理", 0.1),
            ]
        },
        "http_error_rate": {
            "category": "application",
            "causes": [
                ("依赖服务故障或不可用", 0.4),
                ("应用内部异常（NPE等）", 0.3),
                ("数据库连接池耗尽或慢查询", 0.2),
                ("配置错误或版本发布问题", 0.1),
            ]
        },
        "http_response_time_p99": {
            "category": "performance",
            "causes": [
                ("数据库慢查询导致响应延迟", 0.4),
                ("依赖服务响应慢", 0.3),
                ("应用代码性能问题", 0.2),
                ("缓存命中率下降", 0.1),
            ]
        },
        "db_connections": {
            "category": "database",
            "causes": [
                ("慢查询占用连接时间过长", 0.4),
                ("连接泄漏（连接未正常释放）", 0.3),
                ("并发量过高，连接池不足", 0.2),
                ("连接池配置过小", 0.1),
            ]
        },
        "db_slow_queries": {
            "category": "database",
            "causes": [
                ("缺少索引导致全表扫描", 0.4),
                ("SQL语句写法不佳", 0.3),
                ("数据量过大未分库分表", 0.2),
                ("执行计划异常", 0.1),
            ]
        },
        "jvm_heap_usage": {
            "category": "application",
            "causes": [
                ("内存泄漏", 0.4),
                ("缓存对象过多", 0.3),
                ("业务高峰期内存占用升高", 0.2),
                ("堆内存配置过小", 0.1),
            ]
        },
        "mq_queue_size": {
            "category": "middleware",
            "causes": [
                ("消费者处理速度慢", 0.4),
                ("生产者发送量突增", 0.3),
                ("消费者实例异常或宕机", 0.2),
                ("消息处理逻辑变更", 0.1),
            ]
        },
        "redis_memory_usage": {
            "category": "database",
            "causes": [
                ("缓存数据持续增长未过期", 0.4),
                ("存在大key占用大量内存", 0.3),
                ("内存碎片率过高", 0.2),
                ("内存配置不足", 0.1),
            ]
        },
        "service_up": {
            "category": "infrastructure",
            "causes": [
                ("服务进程崩溃（OOM等）", 0.4),
                ("部署发布失败", 0.3),
                ("宿主机故障或网络分区", 0.2),
                ("配置错误导致启动失败", 0.1),
            ]
        },
    }

    rule = category_rules.get(metric_name, {
        "category": "unknown",
        "causes": [("需要进一步分析根因", 0.5), ("可能是系统异常", 0.3), ("需要更多日志和指标", 0.2)],
    })

    for cause_desc, base_confidence in rule["causes"]:
        confidence = base_confidence

        # 如果有错误日志，提升置信度
        if logs_data and logs_data.get("total_found", 0) > 0:
            confidence = min(0.95, confidence + 0.1)

        # 如果有相似历史告警，提升置信度
        if similar_alerts:
            for sim in similar_alerts[:2]:
                if sim.get("metric_name") == metric_name:
                    confidence = min(0.95, confidence + 0.05)
                    break

        # 收集证据
        evidence = []
        if severity == "critical":
            evidence.append(f"告警严重程度为critical")
        evidence.append(f"指标{metric_name}异常: {alert_data.get('metric_value')} (阈值: {alert_data.get('threshold')})")
        if logs_data and logs_data.get("logs"):
            evidence.append(f"发现{logs_data['total_found']}条相关错误日志")
        if similar_alerts:
            evidence.append(f"匹配到{len(similar_alerts)}条历史相似告警")

        hypotheses.append({
            "id": f"hypo-{hypo_id:02d}",
            "description": cause_desc,
            "category": rule["category"],
            "confidence": round(confidence, 3),
            "evidence": evidence,
            "supporting_metrics": [metric_name],
            "supporting_logs": [l["message"][:80] for l in logs_data.get("logs", [])[:2]] if logs_data else [],
        })
        hypo_id += 1

    # 按置信度排序
    hypotheses.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "alert_id": alert_data.get("id"),
        "service": service,
        "metric_name": metric_name,
        "hypotheses": hypotheses,
        "top_hypothesis": hypotheses[0] if hypotheses else None,
        "analysis_method": "rule_based + log_correlation + history_matching",
    }


def generate_fix_plan(root_cause: Dict[str, Any], alert_data: Dict[str, Any],
                      knowledge_entries: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    生成处置建议
    :param root_cause: 根因分析结果
    :param alert_data: 告警数据
    :param knowledge_entries: 相关知识库条目
    :return: 处置方案
    """
    top_hypo = root_cause.get("top_hypothesis", {})
    category = top_hypo.get("category", "unknown")
    description = top_hypo.get("description", "")

    # 基于根因类型生成修复步骤
    fix_steps_map = {
        "infrastructure": [
            {
                "order": 1,
                "action": "立即检查系统资源使用情况",
                "description": "使用top/htop查看CPU、内存使用，定位高资源占用进程",
                "estimated_time_minutes": 5,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": True,
                "command": "top -b -n 1 | head -20",
            },
            {
                "order": 2,
                "action": "确认是否为业务流量增长导致",
                "description": "查看监控QPS和流量趋势，对比历史同期数据",
                "estimated_time_minutes": 5,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": True,
                "command": "查看监控仪表盘",
            },
            {
                "order": 3,
                "action": "如为资源不足，考虑扩容或限流",
                "description": "根据业务情况选择扩容服务实例或启用限流降级",
                "estimated_time_minutes": 15,
                "risk_level": "medium",
                "rollback_step": "缩容或关闭限流",
                "automation_available": False,
                "command": "手动扩容操作",
            },
            {
                "order": 4,
                "action": "排查并修复具体根因",
                "description": "根据根因分析结果执行针对性修复操作",
                "estimated_time_minutes": 30,
                "risk_level": "medium",
                "rollback_step": "恢复原配置",
                "automation_available": False,
                "command": "根据根因执行",
            },
        ],
        "application": [
            {
                "order": 1,
                "action": "查看应用错误日志定位异常",
                "description": "检查应用日志中的ERROR和异常堆栈信息",
                "estimated_time_minutes": 5,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": True,
                "command": "tail -f error.log",
            },
            {
                "order": 2,
                "action": "检查依赖服务健康状态",
                "description": "确认下游依赖服务是否正常运行",
                "estimated_time_minutes": 5,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": True,
                "command": "检查健康检查端点",
            },
            {
                "order": 3,
                "action": "如为代码问题，考虑回滚版本",
                "description": "如果是最近发布导致的问题，回滚到上一稳定版本",
                "estimated_time_minutes": 10,
                "risk_level": "medium",
                "rollback_step": "重新发布新版本",
                "automation_available": True,
                "command": "执行回滚脚本",
            },
            {
                "order": 4,
                "action": "内存问题：生成并分析堆转储",
                "description": "OOM或内存泄漏时生成heap dump进行分析",
                "estimated_time_minutes": 20,
                "risk_level": "medium",
                "rollback_step": "无",
                "automation_available": False,
                "command": "jmap -dump:live,format=b,file=heap.hprof <pid>",
            },
        ],
        "database": [
            {
                "order": 1,
                "action": "查看数据库当前活跃连接和慢查询",
                "description": "执行show processlist查看当前运行的SQL",
                "estimated_time_minutes": 5,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": True,
                "command": "show processlist; show full processlist;",
            },
            {
                "order": 2,
                "action": "分析慢查询并优化索引",
                "description": "对慢查询使用EXPLAIN分析执行计划，添加合适索引",
                "estimated_time_minutes": 20,
                "risk_level": "low",
                "rollback_step": "删除新增索引",
                "automation_available": False,
                "command": "EXPLAIN <sql>",
            },
            {
                "order": 3,
                "action": "连接池问题：调整连接池大小",
                "description": "根据实际需要适当调大连接池max_size配置",
                "estimated_time_minutes": 10,
                "risk_level": "medium",
                "rollback_step": "恢复原配置",
                "automation_available": False,
                "command": "修改application.yml",
            },
            {
                "order": 4,
                "action": "紧急情况：kill慢查询",
                "description": "如有长时运行的慢查询阻塞其他操作，可kill对应连接",
                "estimated_time_minutes": 5,
                "risk_level": "high",
                "rollback_step": "重新执行被中断的查询",
                "automation_available": True,
                "command": "kill <connection_id>",
            },
        ],
        "middleware": [
            {
                "order": 1,
                "action": "检查中间件服务状态",
                "description": "确认MQ/缓存/搜索等中间件服务是否正常运行",
                "estimated_time_minutes": 5,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": True,
                "command": "检查服务状态",
            },
            {
                "order": 2,
                "action": "消息积压：增加消费者",
                "description": "如果消费能力不足，增加消费者实例数量",
                "estimated_time_minutes": 10,
                "risk_level": "low",
                "rollback_step": "减少消费者实例",
                "automation_available": True,
                "command": "扩容消费者服务",
            },
            {
                "order": 3,
                "action": "分析消费慢的原因",
                "description": "查看消费者日志，定位慢操作并优化",
                "estimated_time_minutes": 20,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": False,
                "command": "分析消费逻辑",
            },
        ],
        "performance": [
            {
                "order": 1,
                "action": "分析调用链定位慢节点",
                "description": "使用APM工具查看请求调用链，找出耗时最长的环节",
                "estimated_time_minutes": 10,
                "risk_level": "low",
                "rollback_step": "无",
                "automation_available": True,
                "command": "查看APM调用链",
            },
            {
                "order": 2,
                "action": "数据库慢：优化SQL和索引",
                "description": "如果慢在数据库，优化查询和索引",
                "estimated_time_minutes": 20,
                "risk_level": "low",
                "rollback_step": "撤销索引变更",
                "automation_available": False,
                "command": "SQL优化",
            },
            {
                "order": 3,
                "action": "增加缓存层减少后端压力",
                "description": "对热点数据增加缓存，降低数据库和下游服务压力",
                "estimated_time_minutes": 30,
                "risk_level": "medium",
                "rollback_step": "关闭缓存",
                "automation_available": False,
                "command": "添加缓存逻辑",
            },
        ],
    }

    steps = fix_steps_map.get(category, fix_steps_map["infrastructure"])

    # 如果有知识库条目，追加知识库中的步骤
    knowledge_steps = []
    if knowledge_entries:
        for kb in knowledge_entries[:2]:
            if kb.get("steps"):
                knowledge_steps.append({
                    "source": kb["title"],
                    "kb_id": kb.get("id"),
                    "steps": kb["steps"][:3],
                })

    total_time = sum(s["estimated_time_minutes"] for s in steps)

    # 风险评估
    risk_levels = [s["risk_level"] for s in steps]
    overall_risk = "high" if "high" in risk_levels else ("medium" if "medium" in risk_levels else "low")

    return {
        "root_cause_category": category,
        "root_cause_description": description,
        "remediation_steps": steps,
        "estimated_total_time_minutes": total_time,
        "overall_risk_level": overall_risk,
        "rollback_plan": [s["rollback_step"] for s in steps if s["rollback_step"] and s["rollback_step"] != "无"],
        "knowledge_references": knowledge_steps,
        "alert_id": alert_data.get("id"),
    }


def create_ticket(alert_data: Dict[str, Any], analysis_result: Dict[str, Any],
                  priority: str = "Medium", assignee: str = "") -> Dict[str, Any]:
    """
    创建工单（模拟Jira）
    :param alert_data: 告警数据
    :param analysis_result: 分析结果
    :param priority: 优先级
    :param assignee: 处理人
    :return: 工单信息
    """
    import uuid
    import hashlib

    # 幂等控制：基于告警ID生成唯一key
    idempotency_key = hashlib.md5(f"ticket:{alert_data.get('id')}".encode()).hexdigest()

    ticket_id = f"OPS-{random.randint(10000, 99999)}"

    top_root_cause = analysis_result.get("top_root_cause", {}) if analysis_result else {}
    level = alert_data.get("level", "P3")

    # 优先级映射
    priority_map = {
        "P0": "Highest",
        "P1": "High",
        "P2": "Medium",
        "P3": "Low",
    }
    final_priority = priority_map.get(level, priority)

    # 组件映射
    components_map = {
        "infrastructure": ["Infrastructure", "SRE"],
        "application": ["Application", "Development"],
        "database": ["Database", "DBA"],
        "middleware": ["Middleware", "Platform"],
        "network": ["Network", "SRE"],
        "performance": ["Performance", "SRE"],
    }
    category = top_root_cause.get("category", "application")
    components = components_map.get(category, ["SRE"])

    description_parts = [
        f"h2. 告警信息",
        f"* 告警名称: {alert_data.get('alert_name')}",
        f"* 告警级别: {level}",
        f"* 严重程度: {alert_data.get('severity')}",
        f"* 主机: {alert_data.get('host')}",
        f"* 服务: {alert_data.get('service')}",
        f"* 指标: {alert_data.get('metric_name')} = {alert_data.get('metric_value')} (阈值: {alert_data.get('threshold')})",
        f"* 告警摘要: {alert_data.get('summary')}",
        "",
        f"h2. 根因分析",
        f"* 最可能根因: {top_root_cause.get('description', '待分析')}",
        f"* 置信度: {top_root_cause.get('confidence', 0):.1%}",
        f"* 根因类别: {category}",
        "",
        f"h2. 处置建议",
        f"请参考分析结果中的处置步骤进行处理。",
    ]

    ticket = {
        "id": ticket_id,
        "title": f"[{level}] {alert_data.get('alert_name')} - {alert_data.get('service')}",
        "description": "\n".join(description_parts),
        "status": "open",
        "priority": final_priority,
        "incident_id": alert_data.get("incident_id"),
        "alert_id": alert_data.get("id"),
        "assignee": assignee,
        "reporter": "OpsAlert Agent",
        "components": components,
        "labels": [alert_data.get("severity", ""), level, alert_data.get("service", ""), category],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "idempotency_key": idempotency_key,
        "is_new": True,
    }

    return ticket


def generate_postmortem(incident_data: Dict[str, Any], alert_data: Dict[str, Any],
                        root_cause: Dict[str, Any], remediation: Dict[str, Any],
                        timeline: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    生成事故报告Postmortem
    :param incident_data: 事故数据
    :param alert_data: 告警数据
    :param root_cause: 根因分析
    :param remediation: 处置方案
    :param timeline: 时间线
    :return: Postmortem报告
    """
    top_hypo = root_cause.get("top_hypothesis", {}) if root_cause else {}
    started_at = incident_data.get("started_at", alert_data.get("starts_at", datetime.now().isoformat()))
    resolved_at = incident_data.get("resolved_at")

    # 计算影响时长
    try:
        start_dt = datetime.fromisoformat(started_at) if isinstance(started_at, str) else started_at
        if resolved_at:
            end_dt = datetime.fromisoformat(resolved_at) if isinstance(resolved_at, str) else resolved_at
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        else:
            duration_minutes = None
    except (ValueError, TypeError):
        duration_minutes = None

    # 构建时间线
    default_timeline = [
        {"time": started_at, "event": "告警触发", "description": alert_data.get("summary", "")},
        {"time": started_at, "event": "自动检测", "description": "OpsAlert Agent检测到告警并启动分析"},
        {"time": "T+2min", "event": "根因分析完成", "description": f"初步根因: {top_hypo.get('description', '待确认')}"},
        {"time": "T+5min", "event": "处置方案生成", "description": "自动生成处置建议和操作步骤"},
    ]
    if timeline:
        default_timeline.extend(timeline)
    if resolved_at:
        default_timeline.append({"time": resolved_at, "event": "故障恢复", "description": "服务恢复正常"})

    # 影响范围
    impact_scope = incident_data.get("impact_scope", "")
    if not impact_scope:
        impact_scope = f"服务 {alert_data.get('service')} 受影响"

    # 改进项
    action_items = [
        {
            "id": "ACTION-001",
            "action": "优化监控告警阈值，减少误报",
            "owner": "sre-team",
            "priority": "medium",
            "due_date": "7天内",
        },
        {
            "id": "ACTION-002",
            "action": "完善故障自动化处理能力",
            "owner": "sre-team",
            "priority": "high",
            "due_date": "14天内",
        },
        {
            "id": "ACTION-003",
            "action": f"针对{top_hypo.get('category', '同类')}问题进行代码优化",
            "owner": f"{alert_data.get('service', 'dev')}-team",
            "priority": "medium",
            "due_date": "7天内",
        },
        {
            "id": "ACTION-004",
            "action": "补充相关应急预案和Runbook",
            "owner": "sre-team",
            "priority": "low",
            "due_date": "30天内",
        },
    ]

    # 经验教训
    lessons = [
        "需要加强对关键指标的监控和预警",
        "故障自动化处置可以显著缩短响应时间",
        "定期进行故障演练提升应急响应能力",
        "完善的日志和监控是快速定位问题的基础",
    ]

    # 做得好的
    went_well = [
        "告警及时触发，检测时间短",
        "自动化分析快速给出根因假设",
        "处置建议有参考价值",
    ]

    # 做得不好的
    went_wrong = [
        "故障发现仍依赖监控告警，缺少主动预测",
        "部分自动化修复能力不足，需要人工介入",
        "根因分析准确性还有提升空间",
    ]

    return {
        "incident_id": incident_data.get("id", ""),
        "title": f"{incident_data.get('severity', 'SEV3')}事故报告 - {alert_data.get('alert_name', '')}",
        "summary": f"{alert_data.get('service')} 服务发生 {alert_data.get('alert_name')} 告警，"
                   f"初步判定根因为{top_hypo.get('description', '待确认')}，"
                   f"影响时长约 {duration_minutes if duration_minutes else '待确认'} 分钟。",
        "timeline": default_timeline,
        "impact_scope": impact_scope,
        "affected_services": incident_data.get("affected_services", [alert_data.get("service", "")]),
        "affected_users": incident_data.get("extra", {}).get("affected_users", "待统计"),
        "root_cause": top_hypo.get("description", "待确认"),
        "root_cause_category": top_hypo.get("category", "unknown"),
        "contributing_factors": [
            "监控告警阈值设置可能不够精准",
            "自动化处置能力有待加强",
            "故障预警机制不够完善",
        ],
        "detection": f"通过{alert_data.get('metric_name')}指标监控告警发现",
        "response_actions": [
            step["action"] for step in remediation.get("remediation_steps", [])
        ] if remediation else [],
        "resolution": remediation.get("root_cause_description", "待确认") if remediation else "待处理",
        "what_went_well": went_well,
        "what_went_wrong": went_wrong,
        "action_items": action_items,
        "lessons_learned": lessons,
        "impact_duration_minutes": duration_minutes,
        "generated_at": datetime.now().isoformat(),
        "generated_by": "OpsAlert Agent",
    }
