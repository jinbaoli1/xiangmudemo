"""CMDB服务"""
from typing import List, Dict, Any, Optional
from app.tools.tools_impl import query_topology


class CMDBService:
    """CMDB配置管理服务"""

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._relations: List[Dict[str, Any]] = []
        self._service_deps: Dict[str, Dict[str, Any]] = {}

    def load_data(self, nodes: List[Dict[str, Any]], relations: List[Dict[str, Any]],
                  service_deps: List[Dict[str, Any]]):
        for node in nodes:
            if hasattr(node, 'model_dump'):
                node = node.model_dump()
            self._nodes[node["id"]] = node
        self._relations = relations
        for dep in service_deps:
            if hasattr(dep, 'model_dump'):
                dep = dep.model_dump()
            self._service_deps[dep["service"]] = dep

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self._nodes.get(node_id)

    def get_node_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        for node in self._nodes.values():
            if node.get("name") == name or node.get("hostname") == name:
                return node
        return None

    def get_service_nodes(self, service: str) -> List[Dict[str, Any]]:
        return [n for n in self._nodes.values() if n.get("service") == service]

    def get_topology(self, service: str, host: str = None, depth: int = 2) -> Dict[str, Any]:
        return query_topology(service, host, depth)

    def get_service_dependency(self, service: str) -> Optional[Dict[str, Any]]:
        return self._service_deps.get(service)

    def get_all_services(self) -> List[str]:
        return list(self._service_deps.keys())

    def get_business_priority(self, service: str) -> int:
        # 优先级映射表
        priority_map = {
            "gateway-service": 5, "user-service": 5, "order-service": 5,
            "payment-service": 5, "product-service": 4, "inventory-service": 4,
            "auth-service": 4, "search-service": 3, "recommend-service": 3,
            "message-service": 3,
            "mysql-cluster": 5, "redis-cluster": 4,
            "rabbitmq-cluster": 4, "elasticsearch-cluster": 3,
        }
        if service in priority_map:
            return priority_map[service]
        # 从CMDB节点中查找
        for node in self._nodes.values():
            if node.get("service") == service:
                return node.get("business_priority", 3)
        return 3

    def calculate_impact_scope(self, service: str) -> Dict[str, Any]:
        """计算服务故障的影响范围"""
        topology = query_topology(service, depth=2)
        impact = topology.get("impact_scope", {})

        # 计算影响评分
        upstream_count = len(topology.get("upstream_services", []))
        downstream_count = len(topology.get("downstream_services", []))
        priority = self.get_business_priority(service)

        impact_score = (
            priority * 10
            + upstream_count * 2
            + downstream_count * 3
        )

        return {
            "service": service,
            "business_priority": priority,
            "upstream_services": topology.get("upstream_services", []),
            "downstream_services": topology.get("downstream_services", []),
            "total_affected_services": impact.get("total_affected_services", 0),
            "impact_score": impact_score,
            "impact_level": "critical" if impact_score >= 60 else ("high" if impact_score >= 40 else "medium"),
        }


_cmdb_service: Optional[CMDBService] = None


def get_cmdb_service() -> CMDBService:
    global _cmdb_service
    if _cmdb_service is None:
        _cmdb_service = CMDBService()
    return _cmdb_service
