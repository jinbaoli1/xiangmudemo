"""告警规则模拟数据 - 50+告警规则"""
from typing import List, Dict, Any


def generate_alert_rules() -> List[Dict[str, Any]]:
    rules = []
    rule_id = 0

    # 系统指标类告警 (15条)
    system_alerts = [
        ("CPU使用率过高", "cpu_usage", 90, 95, "critical", "系统CPU使用率持续超过阈值", "system"),
        ("内存使用率过高", "memory_usage", 85, 95, "critical", "系统内存使用率持续超过阈值", "system"),
        ("磁盘使用率过高", "disk_usage", 80, 90, "warning", "磁盘空间使用率超过阈值", "system"),
        ("磁盘IO过高", "disk_io_usage", 80, 95, "warning", "磁盘IO使用率超过阈值", "system"),
        ("网络入流量过高", "network_in_bytes", 80, 95, "warning", "网络入站带宽使用率超过阈值", "network"),
        ("网络出流量过高", "network_out_bytes", 80, 95, "warning", "网络出站带宽使用率超过阈值", "network"),
        ("TCP连接数过高", "tcp_connections", 5000, 10000, "warning", "TCP连接数超过阈值", "network"),
        ("系统负载过高", "load_average", 4, 8, "critical", "系统1分钟负载超过CPU核数阈值", "system"),
        ("进程异常退出", "process_exit", 1, 1, "critical", "关键进程异常退出", "system"),
        ("文件句柄数过高", "file_descriptors", 80, 95, "warning", "文件描述符使用率超过阈值", "system"),
        ("swap使用率过高", "swap_usage", 30, 60, "warning", "Swap分区使用率过高，内存可能不足", "system"),
        ("时钟偏移过大", "clock_offset", 100, 500, "warning", "系统时钟偏移超过阈值(ms)", "system"),
        ("内核错误", "kernel_panic", 1, 1, "critical", "内核发生严重错误", "system"),
        ("OOM事件", "oom_kill", 1, 1, "critical", "发生OOM内存溢出杀死进程事件", "system"),
        ("CPU等待IO过高", "iowait", 20, 40, "warning", "CPU等待IO时间占比过高", "system"),
    ]

    for name, metric, warn_thresh, crit_thresh, severity, desc, category in system_alerts:
        rules.append({
            "id": f"rule-{rule_id:03d}",
            "name": name,
            "metric_name": metric,
            "category": category,
            "severity": severity,
            "warning_threshold": warn_thresh,
            "critical_threshold": crit_thresh,
            "description": desc,
            "duration": "5m",
            "labels": {"category": category, "type": "system"},
        })
        rule_id += 1

    # 应用服务类告警 (15条)
    app_alerts = [
        ("服务不可用", "service_up", 1, 0, "critical", "服务实例宕机或不可达", "application"),
        ("接口错误率过高", "http_error_rate", 5, 10, "critical", "HTTP请求错误率超过阈值(%)", "application"),
        ("接口响应时间过长", "http_response_time_p99", 500, 1000, "warning", "P99响应时间超过阈值(ms)", "application"),
        ("接口QPS过高", "http_qps", 5000, 10000, "warning", "服务请求量超过阈值", "application"),
        ("JVM堆内存使用率过高", "jvm_heap_usage", 80, 95, "warning", "JVM堆内存使用率超过阈值", "application"),
        ("GC时间过长", "jvm_gc_duration", 200, 500, "warning", "GC单次停顿时间过长(ms)", "application"),
        ("线程数过高", "jvm_thread_count", 500, 1000, "warning", "JVM线程数超过阈值", "application"),
        ("死锁检测", "jvm_deadlock", 1, 1, "critical", "检测到JVM线程死锁", "application"),
        ("连接池耗尽", "connection_pool_usage", 80, 95, "critical", "数据库连接池使用率超过阈值", "application"),
        ("消息队列积压", "mq_queue_size", 10000, 50000, "warning", "消息队列消息堆积量过大", "application"),
        ("消息消费延迟", "mq_consume_latency", 60, 300, "warning", "消息消费延迟超过阈值(秒)", "application"),
        ("缓存命中率低", "cache_hit_rate", 70, 50, "warning", "缓存命中率低于阈值(%)", "application"),
        ("熔断触发", "circuit_breaker_open", 1, 1, "warning", "熔断器被触发打开", "application"),
        ("限流触发", "rate_limit_triggered", 100, 1000, "warning", "限流被触发的次数过多", "application"),
        ("重试次数过高", "retry_count", 50, 200, "warning", "接口重试次数过多", "application"),
    ]

    for name, metric, warn_thresh, crit_thresh, severity, desc, category in app_alerts:
        rules.append({
            "id": f"rule-{rule_id:03d}",
            "name": name,
            "metric_name": metric,
            "category": category,
            "severity": severity,
            "warning_threshold": warn_thresh,
            "critical_threshold": crit_thresh,
            "description": desc,
            "duration": "5m",
            "labels": {"category": category, "type": "application"},
        })
        rule_id += 1

    # 数据库类告警 (10条)
    db_alerts = [
        ("数据库连接数过高", "db_connections", 80, 95, "warning", "数据库连接数使用率超过阈值", "database"),
        ("数据库CPU使用率过高", "db_cpu_usage", 70, 90, "critical", "数据库CPU使用率超过阈值", "database"),
        ("慢查询数量", "db_slow_queries", 10, 50, "warning", "慢查询数量超过阈值", "database"),
        ("主从延迟过大", "db_replication_lag", 10, 60, "warning", "MySQL主从同步延迟过大(秒)", "database"),
        ("锁等待时间过长", "db_lock_wait_time", 5, 30, "warning", "数据库锁等待时间过长(秒)", "database"),
        ("事务死锁", "db_deadlock", 1, 5, "critical", "数据库死锁次数超过阈值", "database"),
        ("Buffer Pool命中率低", "db_buffer_hit_rate", 95, 90, "warning", "InnoDB Buffer Pool命中率低于阈值", "database"),
        ("表空间不足", "db_tablespace_usage", 80, 95, "warning", "表空间使用率超过阈值", "database"),
        ("Redis内存使用率过高", "redis_memory_usage", 80, 95, "warning", "Redis内存使用率超过阈值", "database"),
        ("Redis命令响应慢", "redis_latency", 10, 50, "warning", "Redis命令延迟过高(ms)", "database"),
    ]

    for name, metric, warn_thresh, crit_thresh, severity, desc, category in db_alerts:
        rules.append({
            "id": f"rule-{rule_id:03d}",
            "name": name,
            "metric_name": metric,
            "category": category,
            "severity": severity,
            "warning_threshold": warn_thresh,
            "critical_threshold": crit_thresh,
            "description": desc,
            "duration": "5m",
            "labels": {"category": category, "type": "database"},
        })
        rule_id += 1

    # 中间件和基础设施告警 (10条)
    mw_alerts = [
        ("Nginx连接数过高", "nginx_connections", 10000, 50000, "warning", "Nginx活跃连接数过高", "middleware"),
        ("Nginx错误率高", "nginx_error_rate", 5, 10, "warning", "Nginx请求错误率超过阈值", "middleware"),
        ("Kafka消息积压", "kafka_lag", 10000, 100000, "warning", "Kafka消费者组消息积压", "middleware"),
        ("Kafka Broker不可用", "kafka_broker_down", 1, 1, "critical", "Kafka Broker节点宕机", "middleware"),
        ("Elasticsearch集群状态异常", "es_cluster_status", 1, 1, "critical", "ES集群状态为yellow或red", "middleware"),
        ("Elasticsearch JVM内存高", "es_jvm_usage", 80, 90, "warning", "ES节点JVM内存使用率过高", "middleware"),
        ("RabbitMQ队列积压", "rabbitmq_queue_messages", 10000, 100000, "warning", "RabbitMQ队列消息积压过多", "middleware"),
        ("RabbitMQ连接数高", "rabbitmq_connections", 500, 2000, "warning", "RabbitMQ连接数过高", "middleware"),
        ("SSL证书即将过期", "ssl_cert_expiry", 30, 7, "warning", "SSL证书将在N天内过期", "network"),
        ("DNS解析失败", "dns_failure_rate", 1, 5, "critical", "DNS解析失败率过高", "network"),
    ]

    for name, metric, warn_thresh, crit_thresh, severity, desc, category in mw_alerts:
        rules.append({
            "id": f"rule-{rule_id:03d}",
            "name": name,
            "metric_name": metric,
            "category": category,
            "severity": severity,
            "warning_threshold": warn_thresh,
            "critical_threshold": crit_thresh,
            "description": desc,
            "duration": "5m",
            "labels": {"category": category, "type": "middleware"},
        })
        rule_id += 1

    # 业务指标告警 (5+条)
    biz_alerts = [
        ("订单创建量突降", "biz_order_create_rate", -30, -50, "critical", "订单创建量同比下降超过阈值(%)", "business"),
        ("支付成功率下降", "biz_payment_success_rate", 98, 95, "critical", "支付成功率低于阈值(%)", "business"),
        ("用户注册量突增", "biz_user_register_rate", 50, 100, "warning", "用户注册量同比增长超过阈值(%)", "business"),
        ("接口调用量异常", "biz_api_call_volume", -20, -40, "warning", "核心接口调用量异常波动", "business"),
        ("库存预警", "biz_inventory_low", 100, 10, "warning", "商品库存低于安全阈值", "business"),
        ("登录失败率过高", "biz_login_failure_rate", 5, 15, "warning", "用户登录失败率过高(%)", "business"),
    ]

    for name, metric, warn_thresh, crit_thresh, severity, desc, category in biz_alerts:
        rules.append({
            "id": f"rule-{rule_id:03d}",
            "name": name,
            "metric_name": metric,
            "category": category,
            "severity": severity,
            "warning_threshold": warn_thresh,
            "critical_threshold": crit_thresh,
            "description": desc,
            "duration": "5m",
            "labels": {"category": category, "type": "business"},
        })
        rule_id += 1

    return rules
