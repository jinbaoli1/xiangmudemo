"""OpsAlert Agent - FastAPI 入口
提供告警接入、SSE流式分析接口、REST API
"""
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from app.graph import get_ops_alert_graph
from app.services.alert_service import get_alert_service
from app.services.incident_service import get_incident_service
from app.services.knowledge_service import get_knowledge_service
from app.services.cmdb_service import get_cmdb_service
from app.services.log_service import get_log_service


# ---- 请求/响应模型 ----

class AlertIn(BaseModel):
    """告警输入"""
    alert_name: str
    severity: str = "warning"  # critical, warning, info
    host: str
    service: str
    metric_name: str
    metric_value: float
    threshold: float
    unit: str = "%"
    summary: Optional[str] = None
    description: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class AlertOut(BaseModel):
    """告警输出"""
    id: str
    alert_name: str
    severity: str
    status: str
    level: Optional[str] = None
    level_score: Optional[float] = None
    host: str
    service: str
    metric_name: str
    metric_value: float
    threshold: float
    summary: str
    fingerprint: str
    created_at: str


class AnalysisResultOut(BaseModel):
    """分析结果输出"""
    trace_id: str
    alert_id: str
    level: Optional[str] = None
    level_score: Optional[float] = None
    status: str
    current_step: str
    agent_steps: List[Dict[str, Any]] = Field(default_factory=list)
    top_root_cause: Optional[Dict[str, Any]] = None
    remediation_steps: List[Dict[str, Any]] = Field(default_factory=list)
    postmortem: Optional[Dict[str, Any]] = None


# ---- 应用初始化 ----

def initialize_data():
    """初始化模拟数据"""
    from app.data.cmdb_data import generate_cmdb_data
    from app.data.alert_rules import generate_alert_rules
    from app.data.historical_alerts import generate_historical_alerts
    from app.data.log_samples import generate_log_samples
    from app.data.knowledge_base import generate_knowledge_base

    # 生成CMDB数据
    nodes, relations, service_deps = generate_cmdb_data()
    cmdb_service = get_cmdb_service()
    cmdb_service.load_data(nodes, relations, service_deps)

    # 生成告警规则
    rules = generate_alert_rules()

    # 生成历史告警
    nodes_dict_list = [n.model_dump() for n in nodes]
    hist_alerts = generate_historical_alerts(nodes_dict_list, rules)

    # 生成日志样本
    log_samples = generate_log_samples(nodes_dict_list)
    log_service = get_log_service()
    log_service.set_log_samples(log_samples)

    # 生成知识库
    kb_entries = generate_knowledge_base()

    # 构建检索索引
    knowledge_service = get_knowledge_service()
    knowledge_service.load_knowledge_base(kb_entries)
    knowledge_service.load_historical_alerts(hist_alerts)

    return {
        "cmdb_nodes": len(nodes),
        "cmdb_relations": len(relations),
        "alert_rules": len(rules),
        "historical_alerts": len(hist_alerts),
        "log_samples": len(log_samples),
        "knowledge_entries": len(kb_entries),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时初始化数据
    stats = initialize_data()
    print(f"[OpsAlert] 数据初始化完成: {stats}")
    yield
    # 关闭时清理
    print("[OpsAlert] 服务关闭")


app = FastAPI(
    title="OpsAlert Agent API",
    description="告警智能分析Agent系统 - 基于LangGraph的多Agent协作告警分析平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 工具函数 ----

def _format_sse_event(event: str, data: Dict[str, Any]) -> str:
    """格式化SSE事件"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ---- 告警接口 ----

@app.post("/api/v1/alerts", response_model=AlertOut, summary="接入告警")
async def receive_alert(alert_in: AlertIn):
    """
    接入一条告警，自动生成ID和指纹
    """
    alert_service = get_alert_service()

    summary = alert_in.summary or f"{alert_in.alert_name}: {alert_in.host} {alert_in.metric_name}={alert_in.metric_value}"

    alert_data = {
        "alert_name": alert_in.alert_name,
        "severity": alert_in.severity,
        "host": alert_in.host,
        "service": alert_in.service,
        "metric_name": alert_in.metric_name,
        "metric_value": alert_in.metric_value,
        "threshold": alert_in.threshold,
        "unit": alert_in.unit,
        "summary": summary,
        "description": alert_in.description,
        "labels": alert_in.labels,
        "annotations": alert_in.annotations,
        "tags": alert_in.tags,
    }

    alert = alert_service.create_alert(alert_data)
    return alert


@app.get("/api/v1/alerts", summary="告警列表")
async def list_alerts(
    status: Optional[str] = None,
    service: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
):
    """查询告警列表"""
    alert_service = get_alert_service()
    alerts = alert_service.list_alerts(status=status, service=service, level=level, limit=limit)
    return {"total": len(alerts), "alerts": alerts}


@app.get("/api/v1/alerts/{alert_id}", summary="告警详情")
async def get_alert(alert_id: str):
    """获取单条告警详情"""
    alert_service = get_alert_service()
    alert = alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.get("/api/v1/alerts/stats/summary", summary="告警统计概览")
async def alert_stats():
    """告警级别分布统计"""
    alert_service = get_alert_service()
    counts = alert_service.count_by_level()
    return {
        "by_level": counts,
        "total_open": sum(counts.values()),
    }


# ---- 分析接口 ----

@app.post("/api/v1/analyze", summary="同步分析告警")
async def analyze_alert(alert_in: AlertIn):
    """
    同步执行完整告警分析，返回最终结果
    """
    # 先创建告警
    alert_service = get_alert_service()
    summary = alert_in.summary or f"{alert_in.alert_name}: {alert_in.host} {alert_in.metric_name}={alert_in.metric_value}"
    alert_data = {
        "alert_name": alert_in.alert_name,
        "severity": alert_in.severity,
        "host": alert_in.host,
        "service": alert_in.service,
        "metric_name": alert_in.metric_name,
        "metric_value": alert_in.metric_value,
        "threshold": alert_in.threshold,
        "unit": alert_in.unit,
        "summary": summary,
        "description": alert_in.description,
        "labels": alert_in.labels,
        "annotations": alert_in.annotations,
        "tags": alert_in.tags,
    }
    alert = alert_service.create_alert(alert_data)

    # 执行分析
    graph = get_ops_alert_graph()
    result = graph.run(alert)

    return result


@app.post("/api/v1/analyze/stream", summary="SSE流式分析告警")
async def analyze_alert_stream(alert_in: AlertIn):
    """
    SSE流式输出告警分析过程，每个Agent完成后推送一次结果
    """
    # 先创建告警
    alert_service = get_alert_service()
    summary = alert_in.summary or f"{alert_in.alert_name}: {alert_in.host} {alert_in.metric_name}={alert_in.metric_value}"
    alert_data = {
        "alert_name": alert_in.alert_name,
        "severity": alert_in.severity,
        "host": alert_in.host,
        "service": alert_in.service,
        "metric_name": alert_in.metric_name,
        "metric_value": alert_in.metric_value,
        "threshold": alert_in.threshold,
        "unit": alert_in.unit,
        "summary": summary,
        "description": alert_in.description,
        "labels": alert_in.labels,
        "annotations": alert_in.annotations,
        "tags": alert_in.tags,
    }
    alert = alert_service.create_alert(alert_data)

    graph = get_ops_alert_graph()

    async def event_generator():
        # 开始事件
        yield _format_sse_event("connected", {
            "message": "Analysis started",
            "alert_id": alert["id"],
        })

        async for result in graph.arun(alert):
            event_type = "progress" if result["status"] != "completed" else "complete"
            yield _format_sse_event(event_type, result)
            await asyncio.sleep(0.1)  # 模拟处理延迟，便于观察流式效果

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/analyze/{alert_id}", summary="分析已有告警")
async def analyze_existing_alert(alert_id: str):
    """对已存在的告警执行分析"""
    alert_service = get_alert_service()
    alert = alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    graph = get_ops_alert_graph()
    result = graph.run(alert)
    return result


# ---- 知识库接口 ----

@app.get("/api/v1/knowledge/search", summary="搜索知识库")
async def search_knowledge(
    q: str = Query(..., description="搜索关键词"),
    top_k: int = Query(5, ge=1, le=20),
    category: Optional[str] = None,
    service: Optional[str] = None,
):
    """搜索故障知识库"""
    knowledge_service = get_knowledge_service()
    results = knowledge_service.search_knowledge(q, top_k=top_k, category=category, service=service)
    return {
        "query": q,
        "total": len(results),
        "results": results,
    }


@app.get("/api/v1/knowledge/stats", summary="知识库统计")
async def knowledge_stats():
    """知识库统计信息"""
    knowledge_service = get_knowledge_service()
    return knowledge_service.get_knowledge_stats()


# ---- 历史告警接口 ----

@app.get("/api/v1/history/similar", summary="相似历史告警")
async def similar_history_alerts(
    alert_name: str = Query(..., description="告警名称"),
    service: str = Query(..., description="服务名"),
    metric_name: Optional[str] = None,
    top_k: int = Query(5, ge=1, le=20),
):
    """查找相似的历史告警"""
    knowledge_service = get_knowledge_service()
    alert_dict = {
        "alert_name": alert_name,
        "summary": alert_name,
        "service": service,
        "metric_name": metric_name or "",
        "host": "",
        "tags": [],
    }
    results = knowledge_service.find_similar_alerts(alert_dict, top_k=top_k, service=service)
    return {
        "alert_name": alert_name,
        "service": service,
        "total": len(results),
        "similar_alerts": results,
    }


@app.get("/api/v1/history/stats", summary="历史告警统计")
async def history_stats():
    """历史告警统计信息"""
    knowledge_service = get_knowledge_service()
    return knowledge_service.get_historical_alert_stats()


# ---- 事故接口 ----

@app.get("/api/v1/incidents", summary="事故列表")
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    """查询事故列表"""
    incident_service = get_incident_service()
    incidents = incident_service.list_incidents(status=status, severity=severity, limit=limit)
    return {"total": len(incidents), "incidents": incidents}


@app.get("/api/v1/incidents/{incident_id}", summary="事故详情")
async def get_incident(incident_id: str):
    """获取事故详情"""
    incident_service = get_incident_service()
    incident = incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


# ---- CMDB接口 ----

@app.get("/api/v1/cmdb/topology", summary="查询服务拓扑")
async def get_topology(service: str = Query(..., description="服务名"), depth: int = 2):
    """查询服务的拓扑依赖关系"""
    cmdb_service = get_cmdb_service()
    topology = cmdb_service.get_topology(service, depth=depth)
    return topology


@app.get("/api/v1/cmdb/services", summary="服务列表")
async def list_services():
    """获取所有服务列表"""
    cmdb_service = get_cmdb_service()
    services = cmdb_service.get_all_services()
    return {"total": len(services), "services": services}


@app.get("/api/v1/cmdb/impact/{service}", summary="影响范围评估")
async def get_impact_scope(service: str):
    """评估服务故障的影响范围"""
    cmdb_service = get_cmdb_service()
    impact = cmdb_service.calculate_impact_scope(service)
    return impact


# ---- 健康检查 ----

@app.get("/health", summary="健康检查")
async def health_check():
    """服务健康检查"""
    return {
        "status": "healthy",
        "service": "opsalert-agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/", summary="根路径")
async def root():
    return {
        "name": "OpsAlert Agent",
        "description": "告警智能分析Agent系统",
        "version": "1.0.0",
        "docs": "/docs",
        "api_version": "v1",
    }
