"""日志样本模拟数据 - 100+日志样本"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


def generate_log_samples(nodes_info: list, count: int = 120) -> List[Dict[str, Any]]:
    """生成日志样本"""
    random.seed(123)
    logs = []

    services = [n["service"] for n in nodes_info if n.get("service") and n.get("node_type") == "service"]
    hosts_by_service = {}
    for n in nodes_info:
        if n.get("service"):
            svc = n["service"]
            if svc not in hosts_by_service:
                hosts_by_service[svc] = []
            hosts_by_service[svc].append(n["hostname"] or n["name"])

    # 错误模板
    error_templates = [
        # Java异常
        {"level": "ERROR", "pattern": "java.lang.OutOfMemoryError: Java heap space", "category": "jvm_oom",
         "stack": "at com.example.service.OrderService.process(OrderService.java:128)\n  at com.example.controller.OrderController.create(OrderController.java:45)"},
        {"level": "ERROR", "pattern": "java.sql.SQLException: Connection refused, too many connections", "category": "db_connection",
         "stack": "at com.zaxxer.hikari.HikariDataSource.getConnection(HikariDataSource.java:120)\n  at com.example.dao.OrderDAO.insert(OrderDAO.java:88)"},
        {"level": "ERROR", "pattern": "java.net.SocketTimeoutException: Read timed out", "category": "network_timeout",
         "stack": "at java.net.SocketInputStream.socketRead0(Native Method)\n  at org.apache.http.impl.io.SessionInputBufferImpl.streamRead(SessionInputBufferImpl.java:137)"},
        {"level": "ERROR", "pattern": "org.springframework.data.redis.RedisConnectionFailureException: Unable to connect to Redis", "category": "redis_connection",
         "stack": "at org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory$ExceptionTranslatingConnectionProvider.translateException(LettuceConnectionFactory.java:22)"},
        {"level": "ERROR", "pattern": "com.rabbitmq.client.ShutdownSignalException: channel error; protocol method: #method<channel.close>", "category": "mq_channel",
         "stack": "at com.rabbitmq.client.impl.ChannelN.close(ChannelN.java:620)\n  at org.springframework.amqp.rabbit.core.RabbitTemplate.doSend(RabbitTemplate.java:1234)"},
        {"level": "WARN", "pattern": "Slow query detected: SELECT * FROM orders WHERE user_id=? AND status=? took 5230ms", "category": "slow_query",
         "stack": ""},
        {"level": "ERROR", "pattern": "java.lang.NullPointerException: Cannot invoke \"String.length()\" because \"name\" is null", "category": "npe",
         "stack": "at com.example.service.UserService.validateUser(UserService.java:256)\n  at com.example.controller.UserController.getProfile(UserController.java:78)"},
        {"level": "ERROR", "pattern": "io.github.resilience4j.circuitbreaker.CallNotPermittedException: CircuitBreaker 'paymentService' is OPEN", "category": "circuit_breaker",
         "stack": "at io.github.resilience4j.circuitbreaker.CircuitBreakerStateMachine$OpenState.acquirePermission(CircuitBreakerStateMachine.java:345)"},
        {"level": "WARN", "pattern": "ThreadPoolExecutor is saturated: pool size = 200, active threads = 200, queue size = 5000", "category": "thread_pool",
         "stack": ""},
        {"level": "ERROR", "pattern": "java.lang.StackOverflowError", "category": "stack_overflow",
         "stack": "at com.example.service.RecursiveService.calculate(RecursiveService.java:42)\n  at com.example.service.RecursiveService.calculate(RecursiveService.java:45)"},
        {"level": "ERROR", "pattern": "org.springframework.web.client.HttpServerErrorException: 503 Service Unavailable", "category": "upstream_503",
         "stack": "at org.springframework.web.client.DefaultResponseErrorHandler.handleError(DefaultResponseErrorHandler.java:146)"},
        {"level": "WARN", "pattern": "GC pause detected: 2345ms, cause: Full GC (Ergonomics)", "category": "gc_long",
         "stack": ""},
        {"level": "ERROR", "pattern": "Deadlock detected between threads: pool-1-thread-23 and pool-1-thread-45", "category": "deadlock",
         "stack": "at com.example.service.InventoryService.lockProduct(InventoryService.java:120)\n  at com.example.service.InventoryService.deductStock(InventoryService.java:67)"},
        {"level": "ERROR", "pattern": "com.mysql.cj.jdbc.exceptions.MySQLTransactionRollbackException: Deadlock found when trying to get lock; try restarting transaction", "category": "db_deadlock",
         "stack": "at com.mysql.cj.jdbc.exceptions.SQLError.createSQLException(SQLError.java:121)"},
        {"level": "WARN", "pattern": "Rate limit exceeded for client: 192.168.1.100, limit: 1000/s", "category": "rate_limit",
         "stack": ""},
    ]

    # 正常日志模板
    info_templates = [
        {"level": "INFO", "pattern": "Request processed: GET /api/v1/users/{id} in 45ms, status: 200", "category": "request"},
        {"level": "INFO", "pattern": "Order created successfully: order_id={order_id}, user_id={user_id}", "category": "business"},
        {"level": "INFO", "pattern": "Cache hit for key: user:profile:{user_id}", "category": "cache"},
        {"level": "INFO", "pattern": "Message sent to queue: order.events, routingKey: order.created", "category": "mq"},
        {"level": "INFO", "pattern": "Health check passed: status UP, db: UP, redis: UP, mq: UP", "category": "health"},
        {"level": "INFO", "pattern": "Scheduled task completed: data_sync, duration: 1250ms, records: 5000", "category": "scheduler"},
        {"level": "DEBUG", "pattern": "SQL executed: SELECT * FROM products WHERE id IN (?, ?, ?), params: [1,2,3]", "category": "sql"},
        {"level": "INFO", "pattern": "Connection pool stats: active=45, idle=155, pending=0, max=200", "category": "pool"},
        {"level": "INFO", "pattern": "User login successful: user_id={user_id}, ip=192.168.1.{ip_suffix}", "category": "auth"},
        {"level": "INFO", "pattern": "Payment callback received: order_id={order_id}, status: success", "category": "payment"},
    ]

    now = datetime.now()
    log_id = 0

    for i in range(count):
        # 70%正常日志，30%错误日志
        is_error = random.random() < 0.3

        if is_error:
            tmpl = random.choice(error_templates)
        else:
            tmpl = random.choice(info_templates)

        svc = random.choice(services) if services else "user-service"
        hosts = hosts_by_service.get(svc, [f"{svc}-01.prod.local"])
        host = random.choice(hosts)

        # 时间分布：最近24小时内
        minutes_ago = random.randint(0, 24 * 60)
        timestamp = now - timedelta(minutes=minutes_ago)

        # 填充模板变量
        message = tmpl["pattern"]
        message = message.replace("{id}", str(random.randint(1000, 9999)))
        message = message.replace("{order_id}", f"ORD{random.randint(100000, 999999)}")
        message = message.replace("{user_id}", str(random.randint(10000, 99999)))
        message = message.replace("{ip_suffix}", str(random.randint(1, 254)))

        trace_id = f"trace-{random.randint(100000000000, 999999999999)}"

        log = {
            "id": f"log-{log_id:05d}",
            "timestamp": timestamp.isoformat(),
            "host": host,
            "service": svc,
            "source": f"/var/log/{svc}/app.log",
            "level": tmpl["level"],
            "message": message,
            "trace_id": trace_id,
            "stack_trace": tmpl.get("stack"),
            "metadata": {
                "category": tmpl["category"],
                "thread": f"http-nio-8080-exec-{random.randint(1, 200)}",
                "logger": random.choice([
                    "com.example.controller.OrderController",
                    "com.example.service.OrderService",
                    "com.example.dao.OrderDAO",
                    "org.springframework.web.servlet.DispatcherServlet",
                    "com.zaxxer.hikari.HikariPool",
                ]),
            },
        }
        logs.append(log)
        log_id += 1

    # 按时间倒序排列
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return logs
