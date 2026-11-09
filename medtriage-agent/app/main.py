"""FastAPI 入口 - MedTriage 智能分诊导诊系统."""
from __future__ import annotations

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.database import init_db, get_db
from app.graph import get_graph, MedTriageGraph
from app.models.schemas import (
    SessionState,
    TriageRequest,
    TriageResult,
    RAGQuery,
    RAGResult,
    BaseResponse,
    Department,
    Doctor,
    Schedule,
    Medication,
    Patient,
    PatientCreate,
    Appointment,
    AppointmentCreate,
)
from app.services.department_service import DepartmentService
from app.services.doctor_service import DoctorService
from app.services.schedule_service import ScheduleService
from app.services.symptom_service import SymptomService
from app.services.medication_service import MedicationService
from app.services.patient_service import PatientService
from app.services.appointment_service import AppointmentService
from app.services.knowledge_service import get_knowledge_service

# 会话存储（简化版，生产环境用Redis）
_sessions: Dict[str, SessionState] = {}

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="基于多Agent协作的智能分诊导诊系统，支持症状分析、疾病推断、用药建议、医生推荐和预约挂号。",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化."""
    init_db()
    # 预热知识库
    try:
        get_knowledge_service()
    except Exception as e:
        print(f"Knowledge service warmup skipped: {e}")
    print(f"✅ {settings.app_name} v{settings.version} 启动成功")


# ============ 健康检查 ============

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "timestamp": datetime.now().isoformat(),
    }


# ============ SSE 问诊接口 ============

@app.post("/api/v1/triage/chat", tags=["分诊问诊"])
async def triage_chat(request: TriageRequest):
    """分诊问诊接口 - 返回完整结果（非流式）."""
    graph = get_graph()
    session_id = request.session_id

    # 获取或创建会话
    if session_id in _sessions:
        state = _sessions[session_id]
    else:
        state = graph.create_session(session_id=session_id, patient_id=request.patient_id)
        _sessions[session_id] = state

    # 设置trace_id
    if request.trace_id:
        state.trace_id = request.trace_id
    elif not state.trace_id:
        state.trace_id = str(uuid.uuid4())

    # 处理消息
    state = graph.process_message(state, request.patient_input)
    _sessions[session_id] = state

    # 返回结果
    result = graph.get_triage_result(state)
    return BaseResponse(data=result)


@app.post("/api/v1/triage/stream", tags=["分诊问诊"])
async def triage_stream(request: TriageRequest):
    """分诊问诊接口 - SSE流式输出."""
    graph = get_graph()
    session_id = request.session_id

    # 获取或创建会话
    if session_id in _sessions:
        state = _sessions[session_id]
    else:
        state = graph.create_session(session_id=session_id, patient_id=request.patient_id)
        _sessions[session_id] = state

    if request.trace_id:
        state.trace_id = request.trace_id
    elif not state.trace_id:
        state.trace_id = str(uuid.uuid4())

    async def event_generator():
        for event in graph.stream_process(state, request.patient_input):
            # 更新会话状态
            _sessions[session_id] = state
            # SSE格式
            yield f"event: {event['event']}\n"
            yield f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v1/triage/session/{session_id}", tags=["分诊问诊"])
async def get_session(session_id: str):
    """获取会话状态."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    state = _sessions[session_id]
    graph = get_graph()
    return BaseResponse(data=graph.get_triage_result(state))


# ============ RAG 接口 ============

@app.post("/api/v1/rag/query", tags=["医学RAG"])
async def rag_query(query: RAGQuery):
    """医学知识库问答."""
    ks = get_knowledge_service()
    result = ks.answer(query.query, top_k=query.top_k)
    return BaseResponse(data=RAGResult(**result))


@app.get("/api/v1/rag/search", tags=["医学RAG"])
async def rag_search(q: str, top_k: int = 10):
    """医学知识库搜索."""
    ks = get_knowledge_service()
    result = ks.search(q, top_k=top_k)
    return BaseResponse(data={
        "query": q,
        "results": result,
        "total": len(result),
    })


# ============ 科室接口 ============

@app.get("/api/v1/departments", tags=["科室管理"])
async def list_departments(category: Optional[str] = None):
    """获取科室列表."""
    departments = DepartmentService.list_all(category=category)
    return BaseResponse(data=departments)


@app.get("/api/v1/departments/{dept_id}", tags=["科室管理"])
async def get_department(dept_id: int):
    """获取科室详情."""
    dept = DepartmentService.get_by_id(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="科室不存在")
    return BaseResponse(data=dept)


# ============ 医生接口 ============

@app.get("/api/v1/doctors", tags=["医生管理"])
async def list_doctors(department_id: Optional[int] = None, limit: int = 20):
    """获取医生列表."""
    doctors = DoctorService.list_all(department_id=department_id, limit=limit)
    return BaseResponse(data=doctors)


@app.get("/api/v1/doctors/{doctor_id}", tags=["医生管理"])
async def get_doctor(doctor_id: int):
    """获取医生详情."""
    doctor = DoctorService.get_by_id(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="医生不存在")
    return BaseResponse(data=doctor)


@app.get("/api/v1/doctors/{doctor_id}/schedules", tags=["医生管理"])
async def get_doctor_schedules(doctor_id: int):
    """获取医生排班."""
    schedules = ScheduleService.list_by_doctor(doctor_id)
    return BaseResponse(data=schedules)


# ============ 排班接口 ============

@app.get("/api/v1/schedules", tags=["排班管理"])
async def list_schedules(department_id: int, date: Optional[str] = None):
    """获取科室排班."""
    schedules = ScheduleService.list_by_department(department_id, date=date)
    return BaseResponse(data=schedules)


@app.get("/api/v1/schedules/{schedule_id}", tags=["排班管理"])
async def get_schedule(schedule_id: int):
    """获取排班详情."""
    schedule = ScheduleService.get_by_id(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="排班不存在")
    return BaseResponse(data=schedule)


# ============ 症状接口 ============

@app.get("/api/v1/symptoms", tags=["症状管理"])
async def list_symptoms():
    """获取症状列表."""
    symptoms = SymptomService.list_all()
    return BaseResponse(data=symptoms)


@app.get("/api/v1/symptoms/search", tags=["症状管理"])
async def search_symptoms(q: str):
    """搜索症状."""
    symptoms = SymptomService.search(q)
    return BaseResponse(data=symptoms)


@app.get("/api/v1/symptoms/critical", tags=["症状管理"])
async def get_critical_symptoms():
    """获取危急症状列表."""
    symptoms = SymptomService.get_critical_symptoms()
    return BaseResponse(data=symptoms)


# ============ 药品接口 ============

@app.get("/api/v1/medications", tags=["药品管理"])
async def list_medications(category: Optional[str] = None, limit: int = 50):
    """获取药品列表."""
    medications = MedicationService.list_all(category=category, limit=limit)
    return BaseResponse(data=medications)


@app.get("/api/v1/medications/search", tags=["药品管理"])
async def search_medications(q: str, limit: int = 20):
    """搜索药品."""
    medications = MedicationService.search(q, limit=limit)
    return BaseResponse(data=medications)


@app.get("/api/v1/medications/categories", tags=["药品管理"])
async def get_medication_categories():
    """获取药品分类."""
    categories = MedicationService.get_categories()
    return BaseResponse(data=categories)


# ============ 患者接口 ============

@app.post("/api/v1/patients", tags=["患者管理"])
async def create_patient(patient: PatientCreate):
    """创建患者档案."""
    existing = PatientService.get_by_phone(patient.phone)
    if existing:
        return BaseResponse(data=existing, message="患者已存在")
    new_patient = PatientService.create(patient.model_dump())
    return BaseResponse(data=new_patient, message="创建成功")


@app.get("/api/v1/patients/{patient_id}", tags=["患者管理"])
async def get_patient(patient_id: int):
    """获取患者信息."""
    patient = PatientService.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    return BaseResponse(data=patient)


# ============ 预约接口 ============

@app.post("/api/v1/appointments", tags=["预约挂号"])
async def create_appointment(appointment: AppointmentCreate):
    """创建预约."""
    from app.tools.appointment_booking import AppointmentBookingTool
    tool = AppointmentBookingTool()

    result = tool.book_appointment(
        schedule_id=appointment.schedule_id,
        patient_id=appointment.patient_id,
        symptoms=appointment.symptoms,
        initial_diagnosis=appointment.initial_diagnosis,
        idempotency_key=appointment.idempotency_key,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return BaseResponse(data=result["appointment"], message="预约成功")


@app.get("/api/v1/appointments/{appointment_id}", tags=["预约挂号"])
async def get_appointment(appointment_id: int):
    """获取预约详情."""
    appointment = AppointmentService.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return BaseResponse(data=appointment)


@app.delete("/api/v1/appointments/{appointment_id}", tags=["预约挂号"])
async def cancel_appointment(appointment_id: int):
    """取消预约."""
    from app.tools.appointment_booking import AppointmentBookingTool
    tool = AppointmentBookingTool()
    result = tool.cancel_appointment(appointment_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return BaseResponse(message="取消成功")


@app.get("/api/v1/patients/{patient_id}/appointments", tags=["预约挂号"])
async def list_patient_appointments(patient_id: int, limit: int = 10):
    """获取患者预约列表."""
    appointments = AppointmentService.list_by_patient(patient_id, limit=limit)
    return BaseResponse(data=appointments)


# ============ 统计接口 ============

@app.get("/api/v1/stats/summary", tags=["统计"])
async def get_stats_summary():
    """获取数据统计摘要."""
    with get_db() as conn:
        cursor = conn.cursor()

        stats = {}
        tables = [
            ("departments", "科室"),
            ("doctors", "医生"),
            ("symptoms", "症状"),
            ("diseases", "疾病"),
            ("medications", "药品"),
            ("knowledge_base", "知识条目"),
            ("schedules", "排班记录"),
        ]

        for table, label in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                stats[label] = cursor.fetchone()["cnt"]
            except Exception:
                stats[label] = 0

    return BaseResponse(data=stats)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
