"""工具层和Agent层单元测试."""
import sys
import os
from pathlib import Path

# 添加项目根目录到path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest
from app.database import init_db, get_connection
from app.tools.symptom_analyzer import SymptomAnalyzerTool
from app.tools.department_matcher import DepartmentMatcherTool
from app.tools.medication_check import MedicationCheckTool
from app.tools.medical_rag import MedicalRAGTool
from app.agents.triage_agent import TriageAgent
from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.medication_agent import MedicationAgent
from app.models.schemas import SessionState, ChatMessage


@pytest.fixture(scope="module")
def setup_db():
    """设置测试数据库."""
    import app.database as db_module
    import tempfile

    tmp_db = tempfile.mktemp(suffix=".db")
    db_module._db_path = Path(tmp_db)
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    # 插入基础测试数据
    # 科室
    depts = [
        ("心内科", "CARD", "心血管内科", "内科", 4),
        ("呼吸内科", "RESP", "呼吸内科", "内科", 3),
        ("急诊科", "EMER", "急诊科", "急诊", 5),
        ("消化内科", "GAST", "消化内科", "内科", 3),
        ("神经内科", "NEUR", "神经内科", "内科", 4),
    ]
    for d in depts:
        cursor.execute(
            "INSERT INTO departments (name, code, description, category, severity_level) VALUES (?, ?, ?, ?, ?)", d
        )

    # 症状
    symptoms = [
        ("胸痛", "胸部", 5, 1, "心内科,急诊科"),
        ("胸闷", "胸部", 4, 1, "心内科,呼吸内科,急诊科"),
        ("呼吸困难", "胸部", 5, 1, "呼吸内科,急诊科,心内科"),
        ("咳嗽", "胸部", 2, 0, "呼吸内科,耳鼻喉科"),
        ("发热", "全身", 2, 0, "感染科,呼吸内科"),
        ("头痛", "头部", 2, 0, "神经内科,耳鼻喉科"),
        ("腹痛", "腹部", 3, 0, "消化内科,普外科"),
        ("心悸", "胸部", 2, 0, "心内科"),
    ]
    for s in symptoms:
        cursor.execute(
            "INSERT INTO symptoms (name, body_part, severity, is_critical, related_departments) VALUES (?, ?, ?, ?, ?)", s
        )

    # 疾病
    diseases = [
        ("冠心病", 1, "冠状动脉粥样硬化性心脏病", "胸痛,胸闷,心悸", 4),
        ("高血压病", 1, "血压升高", "头痛,头晕,心悸", 3),
        ("肺炎", 2, "肺部感染", "发热,咳嗽,咳痰", 3),
    ]
    for d in diseases:
        cursor.execute(
            "INSERT INTO diseases (name, department_id, description, common_symptoms, severity_level) VALUES (?, ?, ?, ?, ?)", d
        )

    # 症状-疾病映射
    mappings = [
        (1, 1, 2.0),  # 胸痛 -> 冠心病
        (2, 1, 1.5),  # 胸闷 -> 冠心病
        (8, 1, 1.2),  # 心悸 -> 冠心病
        (5, 3, 1.5),  # 发热 -> 肺炎
        (4, 3, 2.0),  # 咳嗽 -> 肺炎
    ]
    for m in mappings:
        cursor.execute(
            "INSERT INTO symptom_disease_map (symptom_id, disease_id, weight) VALUES (?, ?, ?)", m
        )

    # 药品
    meds = [
        ("阿司匹林肠溶片", "阿司匹林", "抗血小板药", "用于心脑血管疾病", "100mg qd", "过敏者禁用", 0, 0),
        ("硝苯地平缓释片", "硝苯地平", "钙通道阻滞剂", "高血压、心绞痛", "20mg bid", "过敏者禁用", 0, 0),
        ("阿莫西林胶囊", "阿莫西林", "青霉素类抗生素", "细菌感染", "0.5g tid", "青霉素过敏者禁用", 1, 0),
    ]
    for m in meds:
        cursor.execute(
            """INSERT INTO medications (name, generic_name, category, indication, dosage, contraindications, pregnancy_warning, controlled)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", m
        )

    # 知识库
    kb_items = [
        ("高血压病常识", "高血压是指血压升高的疾病...", "疾病常识", "高血压,血压", "医学科普"),
        ("冠心病常识", "冠心病是冠状动脉粥样硬化性心脏病...", "疾病常识", "冠心病,心血管", "医学科普"),
        ("感冒与流感常识", "感冒是上呼吸道感染...", "疾病常识", "感冒,流感", "医学科普"),
        ("抗生素合理使用指南", "抗生素用于细菌感染...", "用药指南", "抗生素,合理用药", "合理用药手册"),
    ]
    for k in kb_items:
        cursor.execute(
            "INSERT INTO knowledge_base (title, content, category, tags, source) VALUES (?, ?, ?, ?, ?)", k
        )

    # 医生
    cursor.execute(
        "INSERT INTO doctors (name, department_id, title, specialty, experience_years, rating, consultation_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("张主任", 1, "主任医师", "冠心病介入", 20, 4.8, 2000)
    )

    # 排班
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO schedules (doctor_id, department_id, date, time_slot, total_quota, remaining_quota, fee) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 1, today, "上午", 20, 15, 100.0)
    )

    conn.commit()
    yield conn
    conn.close()
    if os.path.exists(tmp_db):
        os.unlink(tmp_db)


class TestSymptomAnalyzerTool:
    """症状分析工具测试."""

    def test_analyze_normal_symptoms(self, setup_db):
        """测试分析普通症状."""
        tool = SymptomAnalyzerTool()
        result = tool.analyze("我最近有点咳嗽和发热")

        assert "symptoms" in result
        assert len(result["symptoms"]) >= 2
        assert not result["is_critical"]

    def test_analyze_critical_symptoms(self, setup_db):
        """测试分析危急症状."""
        tool = SymptomAnalyzerTool()
        result = tool.analyze("我突然胸痛得厉害，还有呼吸困难")

        assert result["is_critical"] is True
        assert "胸痛" in result["critical_symptoms"]
        assert result["critical_warning"] != ""

    def test_analyze_no_symptoms(self, setup_db):
        """测试分析无明确症状."""
        tool = SymptomAnalyzerTool()
        result = tool.analyze("我不太舒服")

        assert len(result["symptoms"]) == 0
        assert len(result["follow_up_questions"]) > 0


class TestDepartmentMatcherTool:
    """科室匹配工具测试."""

    def test_match_department(self, setup_db):
        """测试科室匹配."""
        tool = DepartmentMatcherTool()
        result = tool.match(["胸痛", "心悸"], symptom_ids=[1, 8])

        assert "recommendations" in result
        assert len(result["recommendations"]) >= 1
        # 心内科应该是推荐的第一个或靠前
        assert any(d.department_name == "心内科" for d in result["recommendations"])

    def test_match_confidence(self, setup_db):
        """匹配置信度."""
        tool = DepartmentMatcherTool()
        result = tool.match(["胸痛"], symptom_ids=[1])

        assert len(result["recommendations"]) > 0
        # 置信度应该在0-1之间
        for rec in result["recommendations"]:
            assert 0 <= rec.confidence <= 1


class TestMedicationCheckTool:
    """用药安全检查工具测试."""

    def test_recommend_medications(self, setup_db):
        """测试药物推荐."""
        tool = MedicationCheckTool()
        result = tool.recommend_medications("高血压")

        assert "medications" in result
        assert isinstance(result["medications"], list)

    def test_check_allergies(self, setup_db):
        """测试过敏检查."""
        tool = MedicationCheckTool()
        result = tool.check_allergies(["阿莫西林胶囊"], "青霉素")

        assert result["has_allergy_risk"] is True
        assert len(result["allergy_alerts"]) >= 1

    def test_comprehensive_check(self, setup_db):
        """测试综合用药检查."""
        tool = MedicationCheckTool()
        result = tool.comprehensive_check(
            medication_names=["阿司匹林肠溶片", "硝苯地平缓释片"],
            allergies="青霉素",
            elderly=True,
        )

        assert "risk_level" in result
        assert "interactions" in result
        assert "allergies" in result
        assert "special_population" in result


class TestMedicalRAGTool:
    """医学RAG工具测试."""

    def test_search(self, setup_db):
        """测试知识搜索."""
        tool = MedicalRAGTool()
        result = tool.search("高血压", top_k=5)

        assert "results" in result
        assert isinstance(result["results"], list)

    def test_query(self, setup_db):
        """测试知识问答."""
        tool = MedicalRAGTool()
        result = tool.query("高血压有什么症状", top_k=3)

        assert "answer" in result
        assert "sources" in result
        assert isinstance(result["answer"], str)


class TestTriageAgent:
    """分诊Agent测试."""

    def test_triage_normal(self, setup_db):
        """测试普通分诊."""
        agent = TriageAgent()
        state = SessionState(
            session_id="test-session-1",
            patient_input="我咳嗽还有点发热",
            trace_id="test-trace-1",
        )

        result = agent.run(state)

        assert result.current_stage == "triage_completed"
        assert len(result.symptoms) > 0
        assert len(result.department_recommendations) > 0
        assert len(result.messages) > 0

    def test_triage_critical(self, setup_db):
        """测试危急症状分诊."""
        agent = TriageAgent()
        state = SessionState(
            session_id="test-session-2",
            patient_input="我胸痛呼吸困难",
            trace_id="test-trace-2",
        )

        result = agent.run(state)

        assert result.is_critical is True
        assert result.critical_warning != ""


class TestDiagnosisAgent:
    """诊断Agent测试."""

    def test_diagnosis_analysis(self, setup_db):
        """测试疾病分析."""
        from app.models.schemas import TriageSymptom

        agent = DiagnosisAgent()
        state = SessionState(
            session_id="test-session-3",
            trace_id="test-trace-3",
            symptoms=[
                TriageSymptom(name="胸痛", confidence=0.9, severity=5, body_part="胸部"),
                TriageSymptom(name="心悸", confidence=0.8, severity=2, body_part="胸部"),
            ],
        )

        result = agent.run(state)

        assert result.current_stage == "diagnosis_completed"
        assert len(result.diagnosis_candidates) > 0
        # 冠心病应该是候选之一
        assert any("冠心病" in c.disease_name for c in result.diagnosis_candidates)
