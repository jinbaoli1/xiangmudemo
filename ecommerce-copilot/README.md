# Commerce Copilot - 电商服务智能体

## 项目简介

基于 FastAPI + LangGraph + SQLite 的电商服务智能体，支持商品导购、订单查询、售后预审、政策QA、人工接管等全链路服务。

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI 层                       │
│  (SSE流式输出 / REST API / 参数校验 / 鉴权)        │
├─────────────────────────────────────────────────────┤
│                  LangGraph 状态机                   │
│  authenticate → classify_intent → extract_slots     │
│     ┌──────────┬──────────┬──────────┬──────────┐  │
│  商品导购   订单查询   售后预审   政策QA   人工接管  │
├─────────────────────────────────────────────────────┤
│                    Tools 工具层                     │
│  search_products / get_order / get_logistics /      │
│  evaluate_after_sale / create_after_sale_draft /    │
│  confirm_after_sale / policy_rag                    │
├─────────────────────────────────────────────────────┤
│                 Services 业务服务层                 │
│  product_service / order_service / inventory /      │
│  after_sale_rule_service                            │
├─────────────────────────────────────────────────────┤
│                 Retrieval 检索层                    │
│  BM25 + TF-IDF + RRF融合 + Reranker                 │
├─────────────────────────────────────────────────────┤
│                   Data 数据层                       │
│  SQLite + 模拟数据 (200+ SKU / 50+ 订单 / 政策)     │
└─────────────────────────────────────────────────────┘
```

## 核心特性

1. **LangGraph状态机**：authenticate → classify_intent → extract_slots → 路由到6条业务链路
2. **商品混合检索**：SQL结构化过滤 + BM25关键词 + TF-IDF语义 + RRF融合 + Reranker
3. **订单鉴权**：服务端user_id注入，ownership校验
4. **售后状态机**：规则引擎判断资格 → 创建草稿 → 用户确认 → 幂等提交 → 转人工
5. **政策RAG**：基于TF-IDF的简单向量检索 + 引用溯源
6. **人工接管**：生成接管包（用户身份、意图、工具结果、风险标签）
7. **全链路追踪**：trace_id + 幂等键 + Pydantic参数校验
8. **SSE流式输出**：实时对话体验

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据

```bash
python seed_data.py
```

### 3. 启动服务

```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 测试接口

```bash
# 商品导购测试
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_001" \
  -d '{"message": "推荐一款性价比高的无线耳机", "conversation_id": "conv_001"}'

# 订单查询测试
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_001" \
  -d '{"message": "查一下我的订单", "conversation_id": "conv_002"}'

# 售后测试
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_001" \
  -d '{"message": "我要退货，订单号ORD202401001", "conversation_id": "conv_003"}'

# 政策QA测试
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_001" \
  -d '{"message": "七天无理由退货政策是什么？", "conversation_id": "conv_004"}'
```

## 项目结构

```
ecommerce-copilot/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI入口，SSE + REST API
│   ├── graph.py                # LangGraph状态机
│   ├── mock_llm.py             # 模拟LLM（规则+模板）
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── product.py          # 商品模型
│   │   ├── order.py            # 订单模型
│   │   ├── after_sale.py       # 售后模型
│   │   ├── conversation.py     # 对话模型
│   │   └── policy.py           # 政策模型
│   ├── data/                   # 模拟数据
│   │   ├── __init__.py
│   │   ├── products.py         # 200+商品SKU
│   │   ├── orders.py           # 50+订单
│   │   ├── after_sale_rules.py # 售后规则
│   │   └── policies.py         # 政策文档
│   ├── retrieval/              # 检索层
│   │   ├── __init__.py
│   │   ├── bm25_retriever.py   # BM25检索
│   │   ├── tfidf_retriever.py  # TF-IDF向量检索
│   │   ├── hybrid_search.py    # RRF融合 + Reranker
│   │   └── base.py             # 基类
│   ├── services/               # 业务服务层
│   │   ├── __init__.py
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   ├── inventory_service.py
│   │   └── after_sale_rule_service.py
│   ├── tools/                  # 工具层
│   │   ├── __init__.py
│   │   ├── search_products.py
│   │   ├── get_order.py
│   │   ├── get_logistics.py
│   │   ├── evaluate_after_sale.py
│   │   ├── create_after_sale_draft.py
│   │   ├── confirm_after_sale.py
│   │   └── policy_rag.py
│   └── eval/                   # 评测脚本
│       ├── __init__.py
│       ├── intent_eval.py
│       ├── retrieval_eval.py
│       └── tool_call_eval.py
├── tests/                      # 单元测试 (20+)
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_retrieval.py
│   ├── test_services.py
│   ├── test_tools.py
│   └── test_graph.py
├── seed_data.py                # 数据初始化脚本
├── test_curls.sh               # curl测试脚本
├── requirements.txt
└── README.md
```

## 状态机节点说明

### 主流程节点
- `authenticate`: 身份验证（从header注入user_id）
- `classify_intent`: 意图分类（6类：商品导购/订单查询/售后/政策QA/闲聊/转人工）
- `extract_slots`: 槽位提取（订单号、商品名、价格区间等）

### 业务链路
1. **商品导购链路**：`search_products` → `rerank` → `generate_response`
2. **订单查询链路**：`verify_ownership` → `get_order_detail` → `generate_response`
3. **售后预审链路**：`evaluate_eligibility` → `create_draft` → `confirm` → `submit`
4. **政策QA链路**：`retrieve_policy` → `cite_sources` → `generate_answer`
5. **闲聊链路**：`chit_chat_response`
6. **人工接管链路**：`generate_handoff_package` → `route_to_agent`

## 运行测试

```bash
# 运行所有单元测试
pytest tests/ -v

# 运行评测脚本
python -m app.eval.intent_eval
python -m app.eval.retrieval_eval
python -m app.eval.tool_call_eval
```
