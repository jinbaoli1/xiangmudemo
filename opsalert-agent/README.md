# OpsAlert Agent - 告警智能分析系统

基于 LangGraph 的多 Agent 协作告警智能分析平台，实现告警分级、根因诊断、处置建议、报告生成全流程自动化。

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI 入口层                        │
│  告警接入 / SSE流式输出 / REST API / 数据看板              │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                  LangGraph 状态机                         │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ Orchestr.│→│Detection │→│ Diagnosis │→│Remediation│ │
│  │  编排器  │  │  分级Agent│  │ 根因Agent  │  │ 处置Agent  │ │
│  └─────────┘  └──────────┘  └───────────┘  └─────┬────┘ │
│                                                  ↓      │
│                                            ┌──────────┐ │
│                                            │  Report  │ │
│                                            │ 报告Agent │ │
│                                            └──────────┘ │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                       工具层                              │
│  query_metrics / query_logs / query_topology             │
│  match_history / analyze_root_cause / generate_fix_plan  │
│  create_ticket / generate_postmortem                     │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                      业务服务层                           │
│  alert_service / metric_service / log_service           │
│  cmdb_service / incident_service / knowledge_service    │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                      检索层 / 数据层                      │
│  BM25 + TF-IDF 知识库检索 / 历史告警相似度匹配            │
│  50+告警规则 / 200+历史告警 / 30+CMDB节点                │
│  100+日志样本 / 50+故障知识库条目                         │
└─────────────────────────────────────────────────────────┘
```

## 核心特性

- **四Agent协作**: 检测分级 → 诊断根因 → 处置建议 → 报告生成，LangGraph 编排 + Orchestrator 路由
- **告警分级**: P0/P1/P2/P3 四级，基于严重程度、影响范围、业务优先级综合打分
- **CMDB拓扑关联**: 根据告警主机关联上下游服务，分析影响范围
- **根因分析**: 基于知识图谱 + 规则引擎 + 历史相似告警，给出根因假设及置信度
- **处置建议**: 根据根因类型给出自动化修复步骤、风险评估、回滚方案
- **历史告警匹配**: 语义相似度匹配历史告警和解决方案
- **事故报告生成**: 自动生成 Postmortem（时间线、影响范围、根因、改进项）
- **工单创建**: 模拟 Jira 工单创建，含幂等控制
- **全链路 trace_id**: On-Call 通知模拟
- **SSE流式输出**: 分析过程实时推送

## 技术栈

- **Python 3.10+**
- **FastAPI** - Web 框架
- **LangGraph** - 状态机/Agent编排
- **Pydantic v2** - 数据验证
- **SQLite** - 数据存储（当前为内存模拟，可扩展）
- **rank_bm25 + scikit-learn TF-IDF** - 混合检索
- **SSE (Server-Sent Events)** - 流式输出
- **Mock LLM** - 基于规则模板模拟，无需外部API

## 快速开始

### 1. 安装依赖

```bash
cd opsalert-agent
pip install -r requirements.txt
```

### 2. 初始化数据

```bash
python seed_data.py
```

### 3. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问文档

打开浏览器访问: http://localhost:8000/docs

## 项目结构

```
opsalert-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI入口
│   ├── graph.py                # LangGraph状态机
│   ├── mock_llm.py             # Mock LLM（规则模板模拟）
│   ├── agents/                 # 四个Agent
│   │   ├── __init__.py
│   │   ├── detection_agent.py  # 检测分级Agent
│   │   ├── diagnosis_agent.py  # 根因诊断Agent
│   │   ├── remediation_agent.py# 处置建议Agent
│   │   └── report_agent.py     # 报告生成Agent
│   ├── tools/                  # 工具层
│   │   ├── __init__.py
│   │   ├── registry.py         # 工具注册表
│   │   └── tools_impl.py       # 8个工具实现
│   ├── services/               # 业务服务层
│   │   ├── __init__.py
│   │   ├── alert_service.py
│   │   ├── metric_service.py
│   │   ├── log_service.py
│   │   ├── cmdb_service.py
│   │   ├── incident_service.py
│   │   └── knowledge_service.py
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── alert.py
│   │   ├── metric.py
│   │   ├── log_entry.py
│   │   ├── cmdb.py
│   │   ├── incident.py
│   │   ├── ticket.py
│   │   ├── knowledge.py
│   │   └── analysis.py
│   ├── data/                   # 模拟数据
│   │   ├── __init__.py
│   │   ├── cmdb_data.py        # CMDB拓扑（30+节点）
│   │   ├── alert_rules.py      # 告警规则（50+）
│   │   ├── historical_alerts.py# 历史告警（200+）
│   │   ├── log_samples.py      # 日志样本（100+）
│   │   └── knowledge_base.py   # 知识库（50+条目）
│   └── retrieval/              # 检索层
│       ├── __init__.py
│       ├── knowledge_retriever.py  # BM25 + TF-IDF混合检索
│       └── alert_retriever.py      # 历史告警相似度匹配
├── tests/                      # 单元测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_retrieval.py
│   ├── test_agents.py
│   └── test_services.py
├── seed_data.py               # 数据初始化脚本
├── test_api.py                # API集成测试脚本
├── test_curl.ps1              # PowerShell测试脚本
├── requirements.txt           # 依赖列表
└── README.md                  # 本文件
```

## API 接口

### 告警管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/alerts | 接入告警 |
| GET | /api/v1/alerts | 告警列表 |
| GET | /api/v1/alerts/{id} | 告警详情 |
| GET | /api/v1/alerts/stats/summary | 告警统计 |

### 告警分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/analyze | 同步分析（返回完整结果） |
| POST | /api/v1/analyze/stream | SSE流式分析 |
| POST | /api/v1/analyze/{alert_id} | 分析已有告警 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/knowledge/search | 搜索知识库 |
| GET | /api/v1/knowledge/stats | 知识库统计 |

### 历史告警

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/history/similar | 相似历史告警 |
| GET | /api/v1/history/stats | 历史告警统计 |

### CMDB拓扑

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/cmdb/topology | 服务拓扑 |
| GET | /api/v1/cmdb/services | 服务列表 |
| GET | /api/v1/cmdb/impact/{service} | 影响范围评估 |

### 事故管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/incidents | 事故列表 |
| GET | /api/v1/incidents/{id} | 事故详情 |

## 演示脚本

### 方式一：Python 测试脚本

```bash
# 确保服务已启动
python test_api.py
```

### 方式二：PowerShell 测试脚本

```powershell
.\test_curl.ps1
```

### 方式三：curl 命令

**接入告警：**
```bash
curl -X POST http://localhost:8000/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "CPU使用率过高",
    "severity": "critical",
    "host": "order-service-01.prod.local",
    "service": "order-service",
    "metric_name": "cpu_usage",
    "metric_value": 95.5,
    "threshold": 90,
    "unit": "%",
    "summary": "CPU使用率过高: order-service-01 cpu_usage=95.5%"
  }'
```

**同步分析：**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "数据库连接池耗尽",
    "severity": "critical",
    "host": "order-service-01.prod.local",
    "service": "order-service",
    "metric_name": "db_connections",
    "metric_value": 96,
    "threshold": 90,
    "unit": "%"
  }'
```

**SSE流式分析：**
```bash
curl -N -X POST http://localhost:8000/api/v1/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{
    "alert_name": "接口错误率过高",
    "severity": "critical",
    "host": "payment-service-01.prod.local",
    "service": "payment-service",
    "metric_name": "http_error_rate",
    "metric_value": 12.5,
    "threshold": 10,
    "unit": "%"
  }'
```

**搜索知识库：**
```bash
curl "http://localhost:8000/api/v1/knowledge/search?q=CPU%E4%BD%BF%E7%94%A8%E7%8E%87%E8%BF%87%E9%AB%98"
```

## 单元测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_agents.py -v

# 查看覆盖率
pytest tests/ --cov=app --cov-report=term-missing
```

## 告警分级规则

分级得分（0-100分）由四个维度加权计算：

| 维度 | 权重 | 说明 |
|------|------|------|
| 严重程度 | 30% | critical/warning/info + 超出阈值幅度 |
| 影响范围 | 30% | 上下游依赖服务数量、受影响实例数 |
| 业务优先级 | 25% | 服务业务重要性等级（1-5） |
| 历史频率 | 15% | 30天内发生频率（首次发生权重更高） |

级别判定：

| 得分 | 级别 | 说明 |
|------|------|------|
| >= 85 | P0 | 重大故障，立即响应 |
| >= 70 | P1 | 严重故障，紧急处理 |
| >= 50 | P2 | 一般故障，尽快处理 |
| < 50 | P3 | 轻微告警，常规处理 |

## 设计说明

### 为什么用 Mock LLM？

本项目为了实现**零外部依赖即可跑通全流程**，使用 `mock_llm.py` 基于规则模板模拟 LLM 输出。
在实际生产环境中，可以无缝替换为真实的 LLM API（如 GPT-4、文心一言等），只需修改 `get_mock_llm()` 返回真实 LLM 客户端即可。

### 检索方案

采用 **BM25 + TF-IDF 混合检索**：
- BM25: 基于词频的经典检索算法，对关键词匹配效果好
- TF-IDF: 余弦相似度计算，对语义相近的词有一定泛化能力
- 混合权重: BM25 60% + TF-IDF 40%，兼顾精确匹配和语义匹配

### 状态机设计

使用 LangGraph StateGraph 编排四 Agent 协作：
1. **Orchestrator**: 接收告警，初始化上下文
2. **DetectionAgent**: 告警分级 + 影响范围评估
3. **DiagnosisAgent**: 根因分析（查询指标/日志/历史/知识库）
4. **RemediationAgent**: 生成处置方案 + 自动创建工单（P0/P1）
5. **ReportAgent**: 生成 Postmortem 报告

P0/P1 级告警自动创建事故和工单，并通知 On-Call 团队。

## 数据规模

| 数据类型 | 数量 | 说明 |
|----------|------|------|
| CMDB节点 | 30+ | 10个服务 + MySQL/Redis/RabbitMQ/ES/Nginx |
| 告警规则 | 56条 | 系统/应用/数据库/中间件/业务 五大类 |
| 历史告警 | 210+ | 过去30天的模拟告警数据 |
| 日志样本 | 120+ | 覆盖常见错误类型 |
| 知识库条目 | 50+ | 覆盖基础设施、应用、数据库、中间件、业务 |

## 扩展方向

- [ ] 接入真实 LLM API
- [ ] SQLite 持久化存储
- [ ] Prometheus/Grafana 真实监控对接
- [ ] ELK 真实日志对接
- [ ] Jira 真实工单集成
- [ ] 飞书/钉钉/企业微信通知
- [ ] 告警聚合和风暴抑制
- [ ] 多租户支持
- [ ] 可视化 Dashboard

## License

MIT
