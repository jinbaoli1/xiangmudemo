"""服务层单元测试."""
import sys
import os
from pathlib import Path

# 添加项目根目录到path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest
from app.database import init_db, get_connection
from app.services.department_service import DepartmentService
from app.services.doctor_service import DoctorService
from app.services.symptom_service import SymptomService
from app.services.medication_service import MedicationService
from app.services.patient_service import PatientService
from app.services.appointment_service import AppointmentService


@pytest.fixture(scope="module")
def setup_db():
    """设置测试数据库."""
    # 使用内存数据库测试
    import app.database as db_module
    from pathlib import Path
    import tempfile

    tmp_db = tempfile.mktemp(suffix=".db")
    db_module._db_path = Path(tmp_db)

    init_db()

    # 插入测试数据
    conn = get_connection()
    cursor = conn.cursor()

    # 测试科室
    cursor.execute(
        "INSERT INTO departments (name, code, description, category, severity_level) VALUES (?, ?, ?, ?, ?)",
        ("心内科", "CARD_TEST", "测试心内科", "内科", 4)
    )
    cursor.execute(
        "INSERT INTO departments (name, code, description, category, severity_level) VALUES (?, ?, ?, ?, ?)",
        ("呼吸内科", "RESP_TEST", "测试呼吸内科", "内科", 3)
    )
    cursor.execute(
        "INSERT INTO departments (name, code, description, category, severity_level) VALUES (?, ?, ?, ?, ?)",
        ("急诊科", "EMER_TEST", "测试急诊科", "急诊", 5)
    )

    # 测试医生
    cursor.execute(
        """INSERT INTO doctors (name, department_id, title, specialty, experience_years, rating, consultation_count)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("张医生", 1, "主任医师", "冠心病介入", 20, 4.8, 1000)
    )
    cursor.execute(
        """INSERT INTO doctors (name, department_id, title, specialty, experience_years, rating, consultation_count)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("李医生", 1, "副主任医师", "心律失常", 12, 4.5, 500)
    )

    # 测试症状
    cursor.execute(
        "INSERT INTO symptoms (name, body_part, severity, is_critical, related_departments) VALUES (?, ?, ?, ?, ?)",
        ("胸痛", "胸部", 5, 1, "心内科,急诊科")
    )
    cursor.execute(
        "INSERT INTO symptoms (name, body_part, severity, is_critical, related_departments) VALUES (?, ?, ?, ?, ?)",
        ("咳嗽", "胸部", 2, 0, "呼吸内科,耳鼻喉科")
    )
    cursor.execute(
        "INSERT INTO symptoms (name, body_part, severity, is_critical, related_departments) VALUES (?, ?, ?, ?, ?)",
        ("发热", "全身", 2, 0, "感染科,呼吸内科")
    )

    # 测试疾病
    cursor.execute(
        "INSERT INTO diseases (name, department_id, description, common_symptoms, severity_level) VALUES (?, ?, ?, ?, ?)",
        ("冠心病", 1, "冠状动脉粥样硬化性心脏病", "胸痛,胸闷,心悸", 4)
    )
    cursor.execute(
        "INSERT INTO diseases (name, department_id, description, common_symptoms, severity_level) VALUES (?, ?, ?, ?, ?)",
        ("高血压病", 1, "血压升高", "头痛,头晕,心悸", 3)
    )

    # 症状-疾病映射
    cursor.execute("INSERT INTO symptom_disease_map (symptom_id, disease_id, weight) VALUES (?, ?, ?)", (1, 1, 2.0))
    cursor.execute("INSERT INTO symptom_disease_map (symptom_id, disease_id, weight) VALUES (?, ?, ?)", (2, 1, 1.0))

    # 测试药品
    cursor.execute(
        """INSERT INTO medications (name, generic_name, category, indication, dosage, contraindications, pregnancy_warning)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("阿司匹林肠溶片", "阿司匹林", "抗血小板药", "用于心脑血管疾病预防", "每次100mg，每日1次", "对阿司匹林过敏者禁用", 0)
    )
    cursor.execute(
        """INSERT INTO medications (name, generic_name, category, indication, dosage, contraindications, pregnancy_warning)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("硝苯地平缓释片", "硝苯地平", "钙通道阻滞剂", "用于高血压、心绞痛", "每次20mg，每日2次", "对本品过敏者禁用", 0)
    )

    # 测试排班
    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """INSERT INTO schedules (doctor_id, department_id, date, time_slot, total_quota, remaining_quota, fee)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (1, 1, today, "上午", 20, 15, 100.0)
    )

    # 测试患者
    cursor.execute(
        "INSERT INTO patients (name, gender, age, phone, allergies, medical_history) VALUES (?, ?, ?, ?, ?, ?)",
        ("测试患者", "男", 30, "13900000000", "青霉素", "无")
    )

    conn.commit()

    yield conn
    conn.close()
    if os.path.exists(tmp_db):
        os.unlink(tmp_db)


class TestDepartmentService:
    """科室服务测试."""

    def test_list_all(self, setup_db):
        """测试获取所有科室."""
        depts = DepartmentService.list_all()
        assert len(depts) >= 3
        assert any(d.name == "心内科" for d in depts)

    def test_get_by_id(self, setup_db):
        """测试根据ID获取科室."""
        dept = DepartmentService.get_by_id(1)
        assert dept is not None
        assert dept.name == "心内科"

    def test_get_by_name(self, setup_db):
        """测试根据名称获取科室."""
        dept = DepartmentService.get_by_name("心内科")
        assert dept is not None
        assert dept.code == "CARD_TEST"

    def test_search(self, setup_db):
        """测试搜索科室."""
        results = DepartmentService.search("心")
        assert len(results) >= 1
        assert any("心" in d.name for d in results)

    def test_get_by_id_not_found(self, setup_db):
        """测试获取不存在的科室."""
        dept = DepartmentService.get_by_id(99999)
        assert dept is None


class TestDoctorService:
    """医生服务测试."""

    def test_list_all(self, setup_db):
        """测试获取医生列表."""
        doctors = DoctorService.list_all()
        assert len(doctors) >= 2

    def test_get_by_id(self, setup_db):
        """测试根据ID获取医生."""
        doctor = DoctorService.get_by_id(1)
        assert doctor is not None
        assert doctor.name == "张医生"
        assert doctor.department_name == "心内科"

    def test_recommend_doctors(self, setup_db):
        """测试推荐医生."""
        doctors = DoctorService.recommend_doctors(department_id=1, limit=5)
        assert len(doctors) >= 1
        assert all(d.department_id == 1 for d in doctors)


class TestSymptomService:
    """症状服务测试."""

    def test_list_all(self, setup_db):
        """测试获取所有症状."""
        symptoms = SymptomService.list_all()
        assert len(symptoms) >= 3

    def test_get_critical_symptoms(self, setup_db):
        """测试获取危急症状."""
        critical = SymptomService.get_critical_symptoms()
        assert len(critical) >= 1
        assert any(s.name == "胸痛" for s in critical)

    def test_detect_critical_symptoms(self, setup_db):
        """检测危急症状."""
        detected = SymptomService.detect_critical_symptoms("我最近胸痛得厉害")
        assert len(detected) >= 1
        assert detected[0].name == "胸痛"

    def test_match_symptoms_from_text(self, setup_db):
        """测试从文本匹配症状."""
        matched = SymptomService.match_symptoms_from_text("我咳嗽还有点发热")
        assert len(matched) >= 2
        symptom_names = [s[0].name for s in matched]
        assert "咳嗽" in symptom_names
        assert "发热" in symptom_names

    def test_get_diseases_by_symptoms(self, setup_db):
        """测试根据症状推断疾病."""
        diseases = SymptomService.get_diseases_by_symptoms([1], limit=5)
        assert len(diseases) >= 1
        assert any("冠心病" in d.disease_name for d in diseases)


class TestMedicationService:
    """药品服务测试."""

    def test_search(self, setup_db):
        """测试搜索药品."""
        results = MedicationService.search("阿司匹林")
        assert len(results) >= 1
        assert results[0].name == "阿司匹林肠溶片"

    def test_check_drug_interactions(self, setup_db):
        """测试药物相互作用检查."""
        result = MedicationService.check_drug_interactions(["阿司匹林肠溶片", "硝苯地平缓释片"])
        # 这两种药没有严重相互作用
        assert isinstance(result, list)

    def test_check_allergies(self, setup_db):
        """测试过敏检查."""
        result = MedicationService.check_allergies(["阿司匹林肠溶片"], "青霉素,阿司匹林")
        assert len(result) >= 1


class TestPatientService:
    """患者服务测试."""

    def test_get_by_id(self, setup_db):
        """测试根据ID获取患者."""
        patient = PatientService.get_by_id(1)
        assert patient is not None
        assert patient.name == "测试患者"

    def test_get_by_phone(self, setup_db):
        """测试根据手机号获取患者."""
        patient = PatientService.get_by_phone("13900000000")
        assert patient is not None
        assert patient.name == "测试患者"


class TestAppointmentService:
    """预约服务测试."""

    def test_create_and_cancel(self, setup_db):
        """测试创建和取消预约."""
        # 创建预约
        appointment = AppointmentService.create({
            "schedule_id": 1,
            "patient_id": 1,
            "doctor_id": 1,
            "department_id": 1,
            "appointment_date": "2026-01-01",
            "time_slot": "上午",
            "symptoms": "胸痛",
            "initial_diagnosis": "疑似冠心病",
            "idempotency_key": "test-key-001",
        })
        assert appointment is not None
        assert appointment.status == "confirmed"

        # 幂等测试
        appointment2 = AppointmentService.create({
            "schedule_id": 1,
            "patient_id": 1,
            "doctor_id": 1,
            "department_id": 1,
            "appointment_date": "2026-01-01",
            "time_slot": "上午",
            "idempotency_key": "test-key-001",
        })
        assert appointment2 is not None
        assert appointment2.id == appointment.id  # 同一个预约

        # 取消预约
        result = AppointmentService.cancel(appointment.id)
        assert result is True

        # 获取预约
        cancelled = AppointmentService.get_by_id(appointment.id)
        assert cancelled.status == "cancelled"
