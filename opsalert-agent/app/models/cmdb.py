from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CMDBNodeType(str):
    SERVER = "server"
    DATABASE = "database"
    MIDDLEWARE = "middleware"
    SERVICE = "service"
    LOAD_BALANCER = "load_balancer"
    CACHE = "cache"
    QUEUE = "queue"
    NETWORK = "network"


class CMDBNode(BaseModel):
    id: str
    name: str
    node_type: str = "server"
    ip: Optional[str] = None
    hostname: Optional[str] = None
    environment: str = "prod"  # prod, staging, dev
    region: str = "cn-east-1"
    status: str = "running"  # running, stopped, maintenance
    service: Optional[str] = None
    business_priority: int = 3  # 1-5, 5最高
    owner: str = ""
    tags: List[str] = Field(default_factory=list)
    specs: Dict[str, Any] = Field(default_factory=dict)  # cpu, memory, disk等
    extra: Dict[str, Any] = Field(default_factory=dict)


class CMDBRelation(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str = "depends_on"  # depends_on, contains, connects_to
    description: str = ""


class ServiceDependency(BaseModel):
    service: str
    upstream: List[str] = Field(default_factory=list)
    downstream: List[str] = Field(default_factory=list)
