"""CMDB模拟数据 - 30+节点的服务拓扑"""
from typing import List, Tuple
from app.models.cmdb import CMDBNode, CMDBRelation, ServiceDependency


def generate_cmdb_data() -> Tuple[List[CMDBNode], List[CMDBRelation], List[ServiceDependency]]:
    nodes: List[CMDBNode] = []
    relations: List[CMDBRelation] = []

    # 定义服务列表和业务优先级
    services = [
        ("user-service", 5, "用户服务", "核心业务"),
        ("order-service", 5, "订单服务", "核心业务"),
        ("payment-service", 5, "支付服务", "核心业务"),
        ("product-service", 4, "商品服务", "重要业务"),
        ("inventory-service", 4, "库存服务", "重要业务"),
        ("search-service", 3, "搜索服务", "一般业务"),
        ("recommend-service", 3, "推荐服务", "一般业务"),
        ("message-service", 3, "消息服务", "一般业务"),
        ("gateway-service", 5, "网关服务", "入口服务"),
        ("auth-service", 4, "认证服务", "基础服务"),
    ]

    node_id = 0
    relation_id = 0

    # 负载均衡层
    lb = CMDBNode(
        id=f"node-{node_id}",
        name="nginx-lb-01",
        node_type="load_balancer",
        ip="10.0.0.1",
        hostname="nginx-lb-01",
        environment="prod",
        region="cn-east-1",
        status="running",
        service="gateway-service",
        business_priority=5,
        owner="infra-team",
        tags=["nginx", "load-balancer", "edge"],
        specs={"cpu": 8, "memory": "16GB", "version": "1.24.0"},
    )
    nodes.append(lb)
    node_id += 1

    # 网关服务 - 3个实例
    for i in range(3):
        node = CMDBNode(
            id=f"node-{node_id}",
            name=f"gateway-{i+1:02d}",
            node_type="service",
            ip=f"10.0.1.{10+i}",
            hostname=f"gateway-{i+1:02d}.prod.local",
            environment="prod",
            region="cn-east-1",
            status="running",
            service="gateway-service",
            business_priority=5,
            owner="platform-team",
            tags=["spring-cloud", "gateway", "java"],
            specs={"cpu": 4, "memory": "8GB", "jdk": "17", "version": "3.2.0"},
        )
        nodes.append(node)
        node_id += 1

    # 各业务服务 - 每个2-4个实例
    service_nodes = {}
    for svc_name, priority, _, _ in services[1:]:  # 跳过gateway
        instance_count = 4 if priority >= 5 else (3 if priority >= 4 else 2)
        svc_nodes = []
        for i in range(instance_count):
            node = CMDBNode(
                id=f"node-{node_id}",
                name=f"{svc_name}-{i+1:02d}",
                node_type="service",
                ip=f"10.0.{2+len(service_nodes)}.{10+i}",
                hostname=f"{svc_name}-{i+1:02d}.prod.local",
                environment="prod",
                region="cn-east-1",
                status="running",
                service=svc_name,
                business_priority=priority,
                owner=f"{svc_name.split('-')[0]}-team",
                tags=["spring-boot", "java", svc_name],
                specs={"cpu": 4 if priority >= 4 else 2, "memory": "8GB" if priority >= 4 else "4GB",
                       "jdk": "17", "version": "2.7.0"},
            )
            nodes.append(node)
            svc_nodes.append(node)
            node_id += 1
        service_nodes[svc_name] = svc_nodes

    # MySQL集群 - 主从
    mysql_master = CMDBNode(
        id=f"node-{node_id}",
        name="mysql-master-01",
        node_type="database",
        ip="10.0.10.10",
        hostname="mysql-master-01.prod.local",
        environment="prod",
        region="cn-east-1",
        status="running",
        service="mysql-cluster",
        business_priority=5,
        owner="dba-team",
        tags=["mysql", "database", "master"],
        specs={"cpu": 16, "memory": "64GB", "disk": "2TB SSD", "version": "8.0.32", "role": "master"},
    )
    nodes.append(mysql_master)
    node_id += 1

    for i in range(2):
        slave = CMDBNode(
            id=f"node-{node_id}",
            name=f"mysql-slave-0{i+1}",
            node_type="database",
            ip=f"10.0.10.{20+i}",
            hostname=f"mysql-slave-0{i+1}.prod.local",
            environment="prod",
            region="cn-east-1",
            status="running",
            service="mysql-cluster",
            business_priority=5,
            owner="dba-team",
            tags=["mysql", "database", "slave"],
            specs={"cpu": 16, "memory": "64GB", "disk": "2TB SSD", "version": "8.0.32", "role": "slave"},
        )
        nodes.append(slave)
        node_id += 1

    # Redis集群
    for i in range(6):
        redis = CMDBNode(
            id=f"node-{node_id}",
            name=f"redis-cluster-{i+1:02d}",
            node_type="cache",
            ip=f"10.0.11.{10+i}",
            hostname=f"redis-cluster-{i+1:02d}.prod.local",
            environment="prod",
            region="cn-east-1",
            status="running",
            service="redis-cluster",
            business_priority=4,
            owner="cache-team",
            tags=["redis", "cache", "cluster"],
            specs={"cpu": 4, "memory": "32GB", "version": "7.0.0", "role": "master" if i < 3 else "slave"},
        )
        nodes.append(redis)
        node_id += 1

    # RabbitMQ集群
    for i in range(3):
        mq = CMDBNode(
            id=f"node-{node_id}",
            name=f"rabbitmq-{i+1:02d}",
            node_type="queue",
            ip=f"10.0.12.{10+i}",
            hostname=f"rabbitmq-{i+1:02d}.prod.local",
            environment="prod",
            region="cn-east-1",
            status="running",
            service="rabbitmq-cluster",
            business_priority=4,
            owner="middleware-team",
            tags=["rabbitmq", "message-queue"],
            specs={"cpu": 8, "memory": "16GB", "version": "3.11.0"},
        )
        nodes.append(mq)
        node_id += 1

    # Elasticsearch集群
    for i in range(3):
        es = CMDBNode(
            id=f"node-{node_id}",
            name=f"elasticsearch-{i+1:02d}",
            node_type="middleware",
            ip=f"10.0.13.{10+i}",
            hostname=f"elasticsearch-{i+1:02d}.prod.local",
            environment="prod",
            region="cn-east-1",
            status="running",
            service="elasticsearch-cluster",
            business_priority=3,
            owner="search-team",
            tags=["elasticsearch", "search"],
            specs={"cpu": 16, "memory": "64GB", "disk": "4TB SSD", "version": "8.5.0"},
        )
        nodes.append(es)
        node_id += 1

    # 构建依赖关系
    # LB -> 所有gateway
    for i in range(3):
        relations.append(CMDBRelation(
            id=f"rel-{relation_id}",
            source_id=lb.id,
            target_id=nodes[1 + i].id,  # gateway nodes
            relation_type="connects_to",
            description=f"LB routes to gateway-{i+1:02d}",
        ))
        relation_id += 1

    # gateway -> 所有业务服务
    gateway_nodes = nodes[1:4]
    svc_start_idx = 4
    idx = svc_start_idx
    for svc_name, priority, _, _ in services[1:]:
        count = 4 if priority >= 5 else (3 if priority >= 4 else 2)
        for gw in gateway_nodes:
            for i in range(count):
                if i == 0:  # 只连第一个实例表示服务依赖
                    relations.append(CMDBRelation(
                        id=f"rel-{relation_id}",
                        source_id=gw.id,
                        target_id=nodes[idx + i].id,
                        relation_type="depends_on",
                        description=f"gateway calls {svc_name}",
                    ))
                    relation_id += 1
        idx += count

    # 服务间依赖
    # order-service 依赖 user-service, product-service, inventory-service, payment-service
    def get_service_first_node(svc_name):
        for n in nodes:
            if n.service == svc_name:
                return n
        return None

    dependencies = [
        ("order-service", ["user-service", "product-service", "inventory-service", "payment-service"]),
        ("payment-service", ["user-service", "order-service"]),
        ("product-service", ["inventory-service"]),
        ("search-service", ["product-service"]),
        ("recommend-service", ["product-service", "user-service"]),
        ("message-service", ["user-service"]),
        ("auth-service", ["user-service"]),
    ]

    for src_svc, dep_svcs in dependencies:
        src_node = get_service_first_node(src_svc)
        if src_node:
            for dep_svc in dep_svcs:
                dep_node = get_service_first_node(dep_svc)
                if dep_node:
                    relations.append(CMDBRelation(
                        id=f"rel-{relation_id}",
                        source_id=src_node.id,
                        target_id=dep_node.id,
                        relation_type="depends_on",
                        description=f"{src_svc} depends on {dep_svc}",
                    ))
                    relation_id += 1

    # 所有业务服务依赖 MySQL
    for svc_name, _, _, _ in services[1:]:
        svc_node = get_service_first_node(svc_name)
        if svc_node:
            relations.append(CMDBRelation(
                id=f"rel-{relation_id}",
                source_id=svc_node.id,
                target_id=mysql_master.id,
                relation_type="depends_on",
                description=f"{svc_name} uses MySQL",
            ))
            relation_id += 1

    # 所有业务服务依赖 Redis
    redis_first = nodes[svc_start_idx + sum(4 if p >= 5 else (3 if p >= 4 else 2) for _, p, _, _ in services[1:])]
    for svc_name, _, _, _ in services[1:]:
        svc_node = get_service_first_node(svc_name)
        if svc_node:
            relations.append(CMDBRelation(
                id=f"rel-{relation_id}",
                source_id=svc_node.id,
                target_id=redis_first.id,
                relation_type="depends_on",
                description=f"{svc_name} uses Redis cache",
            ))
            relation_id += 1

    # message-service 依赖 RabbitMQ
    msg_node = get_service_first_node("message-service")
    rabbitmq_first = get_service_first_node("rabbitmq-cluster")
    if msg_node and rabbitmq_first:
        relations.append(CMDBRelation(
            id=f"rel-{relation_id}",
            source_id=msg_node.id,
            target_id=rabbitmq_first.id,
            relation_type="depends_on",
            description="message-service uses RabbitMQ",
        ))
        relation_id += 1

    # search-service 依赖 Elasticsearch
    search_node = get_service_first_node("search-service")
    es_first = get_service_first_node("elasticsearch-cluster")
    if search_node and es_first:
        relations.append(CMDBRelation(
            id=f"rel-{relation_id}",
            source_id=search_node.id,
            target_id=es_first.id,
            relation_type="depends_on",
            description="search-service uses Elasticsearch",
        ))
        relation_id += 1

    # 构建服务依赖关系列表
    service_deps = []
    for svc_name, _, _, _ in services:
        upstream = []
        downstream = []
        for src_svc, dep_svcs in dependencies:
            if src_svc == svc_name:
                upstream.extend(dep_svcs)
            if svc_name in dep_svcs:
                downstream.append(src_svc)
        # gateway是所有服务的下游调用方
        if svc_name != "gateway-service":
            downstream.append("gateway-service")
        service_deps.append(ServiceDependency(
            service=svc_name,
            upstream=list(set(upstream)),
            downstream=list(set(downstream)),
        ))

    return nodes, relations, service_deps
