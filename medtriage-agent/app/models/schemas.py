"""Pydantic v2 数据模型定义."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ============ 基础响应模型 ============

class BaseResponse(BaseModel):
    """基础响应."""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


# ============ 科室模型 ============

class DepartmentBase(BaseModel):
    name: str = Field(..., description="科室名称")
    code: str = Field(..., description="科室编码")
    description: Optional[str] = None
    category: Optional[str] = None
    severity_level: int = Field(2, ge=1, le=5, description="科室严重程度等级")


class DepartmentCreate(DepartmentBase):
    pass


class Department(DepartmentBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 医生模型 ============

class DoctorBase(BaseModel):
    name: str = Field(..., description="医生姓名")
    department_id: int
    title: Optional[str] = None
    specialty: Optional[str] = None
    experience_years: int = 0
    rating: float = 5.0
    consultation_count: int = 0
    introduction: Optional[str] = None


class DoctorCreate(DoctorBase):
    pass


class Doctor(DoctorBase):
    id: int
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DoctorWithSchedule(Doctor):
    schedules: List["Schedule"] = []


# ============ 排班模型 ============

class ScheduleBase(BaseModel):
    doctor_id: int
    department_id: int
    date: str = Field(..., description="排班日期 YYYY-MM-DD")
    time_slot: str = Field(..., description="时段 上午/下午/晚间")
    total_quota: int = 20
    remaining_quota: int = 20
    fee: float = 50.0


class ScheduleCreate(ScheduleBase):
    pass


class Schedule(ScheduleBase):
    id: int
    doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 症状模型 ============

class SymptomBase(BaseModel):
    name: str
    description: Optional[str] = None
    body_part: Optional[str] = None
    severity: int = Field(2, ge=1, le=5)
    is_critical: bool = False
    related_departments: Optional[str] = None


class SymptomCreate(SymptomBase):
    pass


class Symptom(SymptomBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 疾病模型 ============

class DiseaseBase(BaseModel):
    name: str
    department_id: Optional[int] = None
    description: Optional[str] = None
    common_symptoms: Optional[str] = None
    severity_level: int = 2
    treatment_method: Optional[str] = None


class DiseaseCreate(DiseaseBase):
    pass


class Disease(DiseaseBase):
    id: int
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 药品模型 ============

class MedicationBase(BaseModel):
    name: str
    generic_name: Optional[str] = None
    category: Optional[str] = None
    indication: Optional[str] = None
    dosage: Optional[str] = None
    side_effects: Optional[str] = None
    contraindications: Optional[str] = None
    interactions: Optional[str] = None
    pregnancy_warning: bool = False
    controlled: bool = False


class MedicationCreate(MedicationBase):
    pass


class Medication(MedicationBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 患者模型 ============

class PatientBase(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    id_card: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None


class PatientCreate(PatientBase):
    phone: str = Field(..., description="手机号")


class Patient(PatientBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 预约模型 ============

class AppointmentBase(BaseModel):
    patient_id: int
    schedule_id: int
    doctor_id: int
    department_id: int
    appointment_date: str
    time_slot: str
    symptoms: Optional[str] = None
    initial_diagnosis: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    idempotency_key: Optional[str] = None


class Appointment(AppointmentBase):
    id: int
    status: str = "pending"
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ 分诊相关模型 ============

class TriageRequest(BaseModel):
    """分诊请求."""
    session_id: str = Field(..., description="会话ID")
    patient_input: str = Field(..., description="患者输入的症状描述")
    patient_id: Optional[int] = None
    trace_id: Optional[str] = None


class TriageSymptom(BaseModel):
    """识别出的症状."""
    name: str
    confidence: float
    severity: int = 2
    body_part: Optional[str] = None


class DepartmentRecommendation(BaseModel):
    """科室推荐."""
    department_id: int
    department_name: str
    confidence: float
    reason: str


class DiagnosisCandidate(BaseModel):
    """疑似疾病."""
    disease_name: str
    probability: float
    department: str
    description: str
    key_symptoms: List[str] = []


class MedicationSuggestion(BaseModel):
    """用药建议."""
    medication_name: str
    generic_name: str
    category: str
    indication: str
    dosage: str
    warnings: List[str] = []


class TriageResult(BaseModel):
    """分诊结果."""
    session_id: str
    is_critical: bool = False
    critical_warning: Optional[str] = None
    symptoms: List[TriageSymptom] = []
    department_recommendations: List[DepartmentRecommendation] = []
    diagnosis_candidates: List[DiagnosisCandidate] = []
    medication_suggestions: List[MedicationSuggestion] = []
    doctor_recommendations: List[Dict[str, Any]] = []
    follow_up_questions: List[str] = []
    conversation_stage: str = "triage"


# ============ RAG 模型 ============

class RAGQuery(BaseModel):
    query: str
    top_k: int = 5
    session_id: Optional[str] = None


class RAGResult(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    total_results: int = 0


# ============ 会话模型 ============

class ChatMessage(BaseModel):
    role: str  # user / assistant / system
    content: str
    timestamp: Optional[datetime] = None


class SessionState(BaseModel):
    """会话状态 (LangGraph state)."""
    session_id: str
    patient_id: Optional[int] = None
    patient_input: str = ""
    trace_id: str = ""
    messages: List[ChatMessage] = []
    symptoms: List[TriageSymptom] = []
    is_critical: bool = False
    critical_warning: str = ""
    department_recommendations: List[DepartmentRecommendation] = []
    diagnosis_candidates: List[DiagnosisCandidate] = []
    medication_suggestions: List[MedicationSuggestion] = []
    doctor_recommendations: List[Dict[str, Any]] = []
    current_stage: str = "init"  # init / triage / diagnosis / medication / booking / done
    follow_up_questions: List[str] = []
    extra: Dict[str, Any] = Field(default_factory=dict)


# ============ SSE 事件模型 ============

class SSEEvent(BaseModel):
    event: str
    data: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None


# 提前声明的前向引用更新
DoctorWithSchedule.model_rebuild()
