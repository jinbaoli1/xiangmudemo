# AI Agent 项目实战集

三个不同行业的 AI Agent 项目，基于 LangGraph 状态机 + 混合检索 + 工具调用架构，全部可独立运行、可演示、可面试防守。

> 设计理念：LLM 负责理解（意图、槽位、解释），业务系统负责决定（规则、状态、金额、鉴权）。概率性能力与确定性能力严格隔离。

---

## 项目总览

| 项目 | 行业 | 技术亮点 | 复杂度 | 测试数 |
|------|------|---------|--------|--------|
| [**ecommerce-copilot**](./ecommerce-copilot) | 电商 | LangGraph 状态机 + 商品混合检索 + 售后状态机 + 订单鉴权 + 政策 RAG | ⭐⭐⭐⭐ | 80 |
| [**medtriage-agent**](./medtriage-agent) | 医疗 | 三 Agent 协作（分诊/诊断/用药）+ 症状分析 + 危急值识别 + 医学 RAG + 预约挂号 | ⭐⭐⭐⭐ | 32 |
| [**opsalert-agent**](./opsalert-agent) | IT运维 | 四 Agent 协作（检测/诊断/处置/报告）+ CMDB 拓扑 + 根因分析 + Postmortem | ⭐⭐⭐⭐ | 54 |

---

## 通用技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **后端框架** | FastAPI + Pydantic v2 | 异步 I/O、自动 OpenAPI 文档 |
| **Agent 编排** | LangGraph | 显式状态机、条件路由、失败恢复 |
| **数据存储** | SQLite | 零依赖、开箱即用，生产可换 PostgreSQL |
| **检索引擎** | BM25 + TF-IDF + RRF + Reranker | 混合检索，生产可换 Milvus/Elasticsearch |
| **流式输出** | SSE (Server-Sent Events) | 对话/分析过程分阶段推送 |
| **测试** | pytest | 单元测试 + 集成测试 |
| **LLM** | MockLLM（规则模板） | 无需 API Key 即可跑通全流程，可替换为真实模型 |

---

## 快速开始

每个项目都可以独立运行。以电商项目为例：

```bash
# 1. 进入项目目录
cd ecommerce-copilot

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化模拟数据
python seed_data.py

# 4. 启动服务
python -m uvicorn app.main:app --reload --port 8000

# 5. 运行测试
pytest tests/ -v
```

服务启动后访问 http://localhost:8000/docs 查看交互式 API 文档。

---

## 各项目详解

### 1. Commerce Copilot - 电商服务智能体

**面向场景**：中小型自营商城的智能导购 + 订单查询 + 售后预审助手

**核心能力**：
- 🛒 **智能导购**：结构化过滤 + BM25 + 向量 + RRF + Reranker 混合检索，支持自然语言找商品
- 📦 **订单查询**：服务端 user_id 注入 + 归属校验，防止越权访问
- 🔄 **售后预审**：规则引擎判断资格 → 创建草稿 → 用户确认 → 幂等提交的状态机
- 📚 **政策问答**：RAG + 引用溯源，支持退换货政策、物流政策问答
- 🤝 **人工接管**：低置信度/高风险场景自动生成接管包，避免重复沟通

**LangGraph 状态机**：
```
START → authenticate → classify_intent → extract_slots
  ├─ product_advice → clarify? → retrieve → live_enrich → rerank → explain
  ├─ order_query    → ownership_check → order_tool → summarize
  ├─ after_sales    → ownership_check → rule_engine → confirm? → create_draft
  ├─ policy_qa      → policy_rag → grounded_answer
  └─ unsafe/unknown → refuse_or_handoff
```

### 2. MedTriage Agent - 智能分诊导诊

**面向场景**：医院线上预问诊 + 智能分诊 + 医生推荐 + 预约挂号

**核心能力**：
- 🏥 **智能分诊**：症状关键词匹配 + 权重打分 + 科室推荐（置信度排序）
- 🩺 **三 Agent 协作**：分诊 Agent → 诊断 Agent → 用药 Agent 串联协作
- ⚠️ **危急值识别**：自动识别胸痛、呼吸困难等高危症状，紧急提示
- 💊 **用药安全检查**：药物相互作用 + 过敏提示 + 特殊人群禁忌
- 📅 **预约挂号**：排班查询 → 号源扣减 → 幂等预约 → 取消退号
- 📖 **医学 RAG**：基于知识库的疾病常识、用药指南问答

**数据规模**：25 科室、98 医生、100 症状、70 疾病、535 药品、542 知识条目

### 3. OpsAlert Agent - 告警智能分析

**面向场景**：运维告警自动分析、根因定位、处置建议、事故报告生成

**核心能力**：
- 🔔 **告警分级**：P0/P1/P2/P3 四级，四维加权打分（严重度+影响范围+业务优先级+历史频率）
- 🕸️ **CMDB 拓扑关联**：自动分析上下游影响范围和业务优先级
- 🔍 **四 Agent 协作**：检测 → 诊断 → 处置 → 报告，Orchestrator 统一编排
- 🧠 **根因分析**：多假设输出，带置信度和证据链
- 🔧 **处置建议**：修复步骤 + 风险等级 + 回滚方案
- 📋 **Postmortem**：自动生成事故报告（时间线、影响范围、根因、改进项）
- 🎫 **工单创建**：P0/P1 自动创建工单，幂等控制

**数据规模**：46 CMDB 节点、56 告警规则、261 历史告警、120 日志样本、53 知识库条目

---

## 项目亮点（面试话术）

1. **确定性与概率性隔离**：意图识别允许误差，但订单鉴权、金额计算、状态流转全部由确定性代码控制
2. **写操作安全契约**：所有写操作都经过「准备 → 用户确认 → 幂等执行 → 审计留痕」四步
3. **混合检索分层设计**：硬约束走 SQL、专有名词走 BM25、语义需求走向量、实时信息走 API，各司其职
4. **全链路可观测**：trace_id 贯穿始终，工具调用有审计，支持问题定位和回放
5. **可评测可复现**：每个项目都有离线评测脚本，指标有公式、数据有样本、结果可复现

---

## 目录结构

```
xiangmudemo/
├── ecommerce-copilot/      # 电商服务智能体
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── graph.py        # LangGraph 状态机
│   │   ├── tools/          # 工具层（8个工具）
│   │   ├── services/       # 业务服务层
│   │   ├── retrieval/      # 混合检索层
│   │   ├── models/         # 数据模型
│   │   ├── data/           # 模拟数据
│   │   └── eval/           # 评测脚本
│   ├── tests/              # 80个单元测试
│   ├── seed_data.py        # 数据初始化
│   ├── requirements.txt
│   └── README.md
├── medtriage-agent/        # 医疗分诊导诊
│   ├── app/
│   │   ├── main.py
│   │   ├── graph.py
│   │   ├── agents/         # 3个Agent（分诊/诊断/用药）
│   │   ├── tools/          # 6个工具
│   │   ├── services/       # 8个业务服务
│   │   ├── retrieval/      # 混合检索
│   │   └── data/           # 模拟数据生成器
│   ├── tests/              # 32个单元测试
│   └── README.md
├── opsalert-agent/         # 运维告警分析
│   ├── app/
│   │   ├── main.py
│   │   ├── graph.py
│   │   ├── agents/         # 4个Agent（检测/诊断/处置/报告）
│   │   ├── tools/          # 8个工具
│   │   ├── services/       # 6个业务服务
│   │   ├── retrieval/      # 知识库+历史告警检索
│   │   └── data/           # 模拟数据
│   ├── tests/              # 54个单元测试
│   └── README.md
└── README.md               # 本文件
```

---

## 许可证

MIT License
