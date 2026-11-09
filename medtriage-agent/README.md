# MedTriage 智能分诊导诊 Agent

基于多Agent协作的智能分诊导诊系统，使用 FastAPI + LangGraph + SQLite 构建，支持症状分析、疾病推断、用药建议、医生推荐和预约挂号。

## 项目特点

- **多Agent协作**：TriageAgent（症状采集分诊）→ DiagnosisAgent（疾病分析鉴别）→ MedicationAgent（用药建议+禁忌），通过状态机编排
- **智能分诊**：症状关键词匹配 + 权重打分 + 科室推荐 + 置信度评估
- **医生推荐**：根据科室、专长、排班、评分综合排序
- **挂号预约**：查询排班余量 → 选择时段 → 创建预约 → 幂等控制
- **医学RAG**：基于医学知识库的问答，支持 BM25 + TF-IDF + Reranker 检索 + 引用溯源
- **用药安全检查**：药物相互作用、过敏提示、特殊人群禁忌
- **危急值识别**：识别高危症状（胸痛、呼吸困难等）并紧急提示
- **SSE流式输出**：实时推送分诊过程
- **全链路trace_id、会话历史、Pydantic校验**

## 技术栈

- **Python 3.10+**
- **FastAPI** - Web框架
- **LangGraph** - 状态机/Agent编排
- **SQLite** - 数据库
- **Pydantic v2** - 数据校验
- **SSE (Server-Sent Events)** - 流式输出
- **rank_bm25** - BM25检索
- **scikit-learn (TF-IDF)** - 向量检索
- **jieba** - 中文分词
- **MockLLM** - 基于规则模板模拟LLM（无需外部API）

## 项目结构

```
medtriage-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口，SSE问诊接口、REST API
│   ├── graph.py             # LangGraph状态机：分诊主流程
│   ├── config.py            # 配置管理
│   ├── database.py          # SQLite数据库连接
│   ├── agents/              # Agent层
│   │   ├── __init__.py
│   │   ├── mock_llm.py      # 模拟LLM（基于规则模板）
│   │   ├── triage_agent.py  # 分诊Agent：症状采集分诊
│   │   ├── diagnosis_agent.py # 诊断Agent：疾病分析鉴别
│   │   └── medication_agent.py # 用药Agent：用药建议+禁忌
│   ├── tools/               # 工具层
│   │   ├── __init__.py
│   │   ├── symptom_analyzer.py   # 症状分析工具
│   │   ├── department_matcher.py # 科室匹配工具
│   │   ├── doctor_scheduler.py   # 医生排班查询工具
│   │   ├── appointment_booking.py # 预约挂号工具
│   │   ├── medical_rag.py        # 医学RAG工具
│   │   └── medication_check.py   # 用药安全检查工具
│   ├── services/            # 业务服务层
│   │   ├── __init__.py
│   │   ├── department_service.py
│   │   ├── doctor_service.py
│   │   ├── schedule_service.py
│   │   ├── symptom_service.py
│   │   ├── medication_service.py
│   │   ├── patient_service.py
│   │   ├── appointment_service.py
│   │   └── knowledge_service.py
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic v2 模型
│   ├── data/                # 模拟数据
│   │   ├── __init__.py
│   │   ├── departments.py   # 25个科室
│   │   ├── doctors.py       # 80+医生生成器
│   │   ├── symptoms.py      # 100+症状、80+疾病、300+映射
│   │   ├── medications.py   # 550+药品生成器
│   │   ├── schedules.py     # 排班生成器
│   │   └── knowledge_data.py # 200+医学知识条目
│   ├── knowledge/           # 医学知识库
│   │   └── __init__.py
│   └── retrieval/           # 检索层
│       ├── __init__.py
│       ├── bm25_retriever.py    # BM25检索器
│       ├── tfidf_retriever.py   # TF-IDF检索器
│       ├── reranker.py          # 重排序器
│       └── ensemble.py          # 融合检索器
├── tests/                    # 单元测试（20+个用例）
│   ├── __init__.py
│   ├── test_services.py
│   └── test_tools_agents.py
├── seed_data.py             # 数据初始化脚本
├── requirements.txt         # 依赖清单
└── README.md                # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
cd medtriage-agent
pip install -r requirements.txt
```

### 2. 初始化数据

```bash
python seed_data.py
```

将创建SQLite数据库并导入：
- 25个科室
- 80+位医生
- 100+个症状
- 80+种疾病
- 300+条症状-疾病映射
- 550+种药品
- 200+条医学知识
- 未来14天排班

### 3. 启动服务

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API 接口

### 分诊问诊

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/triage/chat` | 分诊问诊（完整结果） |
| POST | `/api/v1/triage/stream` | 分诊问诊（SSE流式） |
| GET | `/api/v1/triage/session/{id}` | 获取会话状态 |

### 医学RAG

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/rag/query` | 医学知识问答 |
| GET | `/api/v1/rag/search` | 医学知识搜索 |

### 科室/医生/排班

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/departments` | 科室列表 |
| GET | `/api/v1/departments/{id}` | 科室详情 |
| GET | `/api/v1/doctors` | 医生列表 |
| GET | `/api/v1/doctors/{id}` | 医生详情 |
| GET | `/api/v1/doctors/{id}/schedules` | 医生排班 |
| GET | `/api/v1/schedules` | 科室排班列表 |
| GET | `/api/v1/schedules/{id}` | 排班详情 |

### 症状/药品

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/symptoms` | 症状列表 |
| GET | `/api/v1/symptoms/search` | 搜索症状 |
| GET | `/api/v1/symptoms/critical` | 危急症状列表 |
| GET | `/api/v1/medications` | 药品列表 |
| GET | `/api/v1/medications/search` | 搜索药品 |
| GET | `/api/v1/medications/categories` | 药品分类 |

### 患者/预约

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/patients` | 创建患者档案 |
| GET | `/api/v1/patients/{id}` | 患者详情 |
| POST | `/api/v1/appointments` | 创建预约 |
| GET | `/api/v1/appointments/{id}` | 预约详情 |
| DELETE | `/api/v1/appointments/{id}` | 取消预约 |
| GET | `/api/v1/patients/{id}/appointments` | 患者预约列表 |

## 演示示例

### 示例1：普通分诊

```bash
curl -X POST http://localhost:8000/api/v1/triage/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "patient_input": "我最近头痛、头晕，还有点心悸",
    "trace_id": "trace-001"
  }'
```

### 示例2：危急症状识别

```bash
curl -X POST http://localhost:8000/api/v1/triage/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-002",
    "patient_input": "我胸痛得厉害，还有呼吸困难"
  }'
```

### 示例3：SSE流式输出

```bash
curl -N -X POST http://localhost:8000/api/v1/triage/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-stream-001",
    "patient_input": "我咳嗽、发热三天了"
  }'
```

### 示例4：医学RAG问答

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "高血压有什么症状和治疗方法",
    "top_k": 5
  }'
```

### 示例5：预约挂号

```bash
# 1. 查询排班
curl "http://localhost:8000/api/v1/schedules?department_id=1"

# 2. 创建预约
curl -X POST http://localhost:8000/api/v1/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "schedule_id": 1,
    "doctor_id": 1,
    "department_id": 1,
    "appointment_date": "2026-01-01",
    "time_slot": "上午",
    "symptoms": "头痛头晕",
    "idempotency_key": "appt-test-001"
  }'
```

## 核心流程

### 分诊主流程（LangGraph状态机）

```
用户输入
   ↓
症状分析 (SymptomAnalyzer)
   ↓
┌─ 危急？ ──是──→ 紧急提示 → 结束
│   │
│   否
│   ↓
科室匹配 (DepartmentMatcher)
   ↓
疾病诊断 (DiagnosisAgent)
   ↓
用药建议 (MedicationAgent)
   ↓
医生推荐 (DoctorScheduler)
   ↓
完成（可继续追问或预约）
```

### 检索架构

```
用户查询
   ↓
┌───────────┐  ┌───────────┐
│  BM25检索 │  │ TF-IDF检索 │
└─────┬─────┘  └─────┬─────┘
      └───────┬───────┘
              ↓
        结果融合（加权+RRF）
              ↓
        Reranker重排序
              ↓
        生成回答+引用溯源
```

## 运行测试

```bash
python -m pytest tests/ -v
```

测试覆盖：
- 服务层：科室、医生、症状、药品、患者、预约等
- 工具层：症状分析、科室匹配、用药安全检查、医学RAG
- Agent层：分诊Agent、诊断Agent

## 数据说明

本项目使用模拟数据，所有数据均为程序生成，仅供演示和测试使用。

- **科室**：25个，涵盖内科、外科、妇儿、五官、急诊、重症等
- **医生**：80+位，涵盖各科室各级职称
- **症状**：100+个常见症状，含危急症状标记
- **疾病**：80+种常见疾病
- **症状-疾病映射**：300+条，带权重
- **药品**：550+种，涵盖抗生素、心血管、消化、呼吸等类别
- **医学知识**：200+条，含科室介绍、疾病常识、用药指南
- **排班**：未来14天排班，自动生成

## 注意事项

1. **MockLLM**：本项目使用基于规则模板的MockLLM，无需外部API即可跑通全流程。如需接入真实LLM，可替换 `app/agents/mock_llm.py` 中的实现。

2. **数据安全**：本项目为演示项目，密码、token等敏感信息未加密存储，生产环境请加强安全措施。

3. **会话存储**：当前会话存储在内存中，重启后丢失。生产环境建议使用Redis等持久化存储。

4. **医疗免责**：本系统仅供分诊参考，不能替代专业医生诊断。所有医疗建议仅供参考，具体诊疗请遵医嘱。

## License

MIT
