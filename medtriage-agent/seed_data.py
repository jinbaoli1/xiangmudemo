"""MedTriage 数据初始化脚本.

使用方法：
    python seed_data.py

会创建SQLite数据库并导入所有模拟数据。
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from app.database import init_db, get_connection
from app.data.departments import DEPARTMENTS
from app.data.doctors import generate_doctors
from app.data.symptoms import SYMPTOMS, DISEASES, generate_symptom_disease_map
from app.data.medications import generate_medications
from app.data.schedules import generate_schedules
from app.data.knowledge_data import generate_knowledge_base


def seed_departments(conn):
    """导入科室数据."""
    cursor = conn.cursor()
    for dept in DEPARTMENTS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO departments (name, code, description, category, severity_level)
            VALUES (?, ?, ?, ?, ?)
            """,
            (dept["name"], dept["code"], dept["description"], dept["category"], dept["severity_level"])
        )
    conn.commit()
    cursor.execute("SELECT COUNT(*) as cnt FROM departments")
    return cursor.fetchone()["cnt"]


def seed_doctors(conn):
    """导入医生数据."""
    cursor = conn.cursor()
    doctors = generate_doctors(DEPARTMENTS)
    for doc in doctors:
        cursor.execute(
            """
            INSERT OR IGNORE INTO doctors
                (name, department_id, title, specialty, experience_years,
                 rating, consultation_count, introduction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc["name"], doc["department_id"], doc["title"], doc["specialty"],
                doc["experience_years"], doc["rating"], doc["consultation_count"],
                doc["introduction"]
            )
        )
    conn.commit()
    cursor.execute("SELECT COUNT(*) as cnt FROM doctors")
    return cursor.fetchone()["cnt"]


def seed_symptoms_and_diseases(conn):
    """导入症状、疾病和映射数据."""
    cursor = conn.cursor()

    # 症状
    for sym in SYMPTOMS:
        cursor.execute(
            """
            INSERT OR IGNORE INTO symptoms
                (name, description, body_part, severity, is_critical, related_departments)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sym["name"], sym.get("description", ""), sym.get("body_part", ""),
                sym["severity"], 1 if sym["is_critical"] else 0,
                sym.get("related_departments", "")
            )
        )

    # 疾病
    for disease in DISEASES:
        # 获取科室ID
        cursor.execute("SELECT id FROM departments WHERE name = ?", (disease["department_name"],))
        row = cursor.fetchone()
        dept_id = row["id"] if row else None

        cursor.execute(
            """
            INSERT OR IGNORE INTO diseases
                (name, department_id, description, common_symptoms, severity_level, treatment_method)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                disease["name"], dept_id, disease["description"],
                disease["common_symptoms"], disease["severity_level"],
                disease["treatment_method"]
            )
        )

    conn.commit()

    # 症状-疾病映射
    mappings = generate_symptom_disease_map(SYMPTOMS, DISEASES)
    for mapping in mappings:
        cursor.execute(
            """
            INSERT OR IGNORE INTO symptom_disease_map (symptom_id, disease_id, weight)
            VALUES (?, ?, ?)
            """,
            (mapping["symptom_id"], mapping["disease_id"], mapping["weight"])
        )

    conn.commit()

    cursor.execute("SELECT COUNT(*) as cnt FROM symptoms")
    symptom_count = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM diseases")
    disease_count = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM symptom_disease_map")
    map_count = cursor.fetchone()["cnt"]

    return symptom_count, disease_count, map_count


def seed_medications(conn):
    """导入药品数据."""
    cursor = conn.cursor()
    medications = generate_medications()
    for med in medications:
        cursor.execute(
            """
            INSERT OR IGNORE INTO medications
                (name, generic_name, category, indication, dosage, side_effects,
                 contraindications, interactions, pregnancy_warning, controlled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                med["name"], med["generic_name"], med["category"],
                med["indication"], med["dosage"], med["side_effects"],
                med["contraindications"], med["interactions"],
                1 if med["pregnancy_warning"] else 0,
                1 if med["controlled"] else 0,
            )
        )
    conn.commit()
    cursor.execute("SELECT COUNT(*) as cnt FROM medications")
    return cursor.fetchone()["cnt"]


def seed_schedules(conn):
    """导入排班数据."""
    cursor = conn.cursor()

    # 读取医生和科室
    cursor.execute("SELECT * FROM doctors")
    doctors = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM departments")
    departments = [dict(row) for row in cursor.fetchall()]

    schedules = generate_schedules(doctors, departments, num_days=14)

    for sched in schedules:
        cursor.execute(
            """
            INSERT OR IGNORE INTO schedules
                (doctor_id, department_id, date, time_slot, total_quota, remaining_quota, fee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sched["doctor_id"], sched["department_id"], sched["date"],
                sched["time_slot"], sched["total_quota"], sched["remaining_quota"],
                sched["fee"]
            )
        )
    conn.commit()
    cursor.execute("SELECT COUNT(*) as cnt FROM schedules")
    return cursor.fetchone()["cnt"]


def seed_knowledge(conn):
    """导入医学知识库."""
    cursor = conn.cursor()
    knowledge = generate_knowledge_base()
    for item in knowledge:
        cursor.execute(
            """
            INSERT OR IGNORE INTO knowledge_base
                (title, content, category, tags, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item["title"], item["content"], item["category"], item["tags"], item["source"])
        )
    conn.commit()
    cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_base")
    return cursor.fetchone()["cnt"]


def seed_sample_patients(conn):
    """导入示例患者数据."""
    cursor = conn.cursor()
    sample_patients = [
        {"name": "张三", "gender": "男", "age": 35, "phone": "13800000001",
         "allergies": "青霉素", "medical_history": "高血压"},
        {"name": "李四", "gender": "女", "age": 28, "phone": "13800000002",
         "allergies": "", "medical_history": ""},
        {"name": "王五", "gender": "男", "age": 65, "phone": "13800000003",
         "allergies": "磺胺类", "medical_history": "糖尿病、冠心病"},
    ]
    for p in sample_patients:
        cursor.execute(
            """
            INSERT OR IGNORE INTO patients (name, gender, age, phone, allergies, medical_history)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (p["name"], p["gender"], p["age"], p["phone"], p["allergies"], p["medical_history"])
        )
    conn.commit()
    cursor.execute("SELECT COUNT(*) as cnt FROM patients")
    return cursor.fetchone()["cnt"]


def main():
    """主函数."""
    print("=" * 60)
    print("  MedTriage 智能分诊导诊系统 - 数据初始化")
    print("=" * 60)
    print()

    # 初始化数据库表
    print("📋 初始化数据库表结构...")
    init_db()
    print("✅ 数据库表结构创建完成")
    print()

    conn = get_connection()

    try:
        # 科室
        print("🏥 导入科室数据...")
        dept_count = seed_departments(conn)
        print(f"   已导入 {dept_count} 个科室")
        print()

        # 医生
        print("👨‍⚕️ 导入医生数据...")
        doc_count = seed_doctors(conn)
        print(f"   已导入 {doc_count} 位医生")
        print()

        # 症状和疾病
        print("🤒 导入症状、疾病和映射数据...")
        sym_count, dis_count, map_count = seed_symptoms_and_diseases(conn)
        print(f"   已导入 {sym_count} 个症状")
        print(f"   已导入 {dis_count} 种疾病")
        print(f"   已导入 {map_count} 条症状-疾病映射")
        print()

        # 药品
        print("💊 导入药品数据...")
        med_count = seed_medications(conn)
        print(f"   已导入 {med_count} 种药品")
        print()

        # 排班
        print("📅 生成排班数据（未来14天）...")
        sched_count = seed_schedules(conn)
        print(f"   已生成 {sched_count} 条排班记录")
        print()

        # 知识库
        print("📚 导入医学知识库...")
        kb_count = seed_knowledge(conn)
        print(f"   已导入 {kb_count} 条医学知识")
        print()

        # 示例患者
        print("👤 导入示例患者数据...")
        patient_count = seed_sample_patients(conn)
        print(f"   已导入 {patient_count} 个示例患者")
        print()

        print("=" * 60)
        print("  ✅ 数据初始化完成！")
        print("=" * 60)
        print()
        print("📊 数据统计：")
        print(f"   科室数量:     {dept_count}")
        print(f"   医生数量:     {doc_count}")
        print(f"   症状数量:     {sym_count}")
        print(f"   疾病数量:     {dis_count}")
        print(f"   症状-疾病映射: {map_count}")
        print(f"   药品数量:     {med_count}")
        print(f"   排班记录:     {sched_count}")
        print(f"   知识条目:     {kb_count}")
        print(f"   患者数量:     {patient_count}")
        print()
        print("🚀 启动服务: python -m uvicorn app.main:app --reload --port 8000")
        print()

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
