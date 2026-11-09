"""SQLite 数据库连接管理."""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from app.config import settings, BASE_DIR

_db_path = BASE_DIR / settings.database_url
_local = threading.local()


def get_db_path() -> Path:
    return _db_path


def get_connection() -> sqlite3.Connection:
    """获取当前线程的数据库连接."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _create_connection()
        _local.conn = conn
    else:
        # 检查连接是否仍然有效
        try:
            conn.execute("SELECT 1")
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            # 连接已关闭或无效，重新创建
            conn = _create_connection()
            _local.conn = conn
    return conn


def _create_connection() -> sqlite3.Connection:
    """创建新的数据库连接."""
    conn = sqlite3.connect(str(_db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """上下文管理器形式的数据库连接."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db():
    """初始化数据库表结构."""
    conn = get_connection()
    cursor = conn.cursor()

    # 科室表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        code TEXT NOT NULL UNIQUE,
        description TEXT,
        category TEXT,
        severity_level INTEGER DEFAULT 2,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 医生表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        title TEXT,
        specialty TEXT,
        experience_years INTEGER DEFAULT 0,
        rating REAL DEFAULT 5.0,
        consultation_count INTEGER DEFAULT 0,
        introduction TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)

    # 排班表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        department_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        total_quota INTEGER DEFAULT 20,
        remaining_quota INTEGER DEFAULT 20,
        fee REAL DEFAULT 50.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id),
        FOREIGN KEY (department_id) REFERENCES departments(id),
        UNIQUE(doctor_id, date, time_slot)
    )
    """)

    # 症状表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symptoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        body_part TEXT,
        severity INTEGER DEFAULT 2,
        is_critical INTEGER DEFAULT 0,
        related_departments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 疾病表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diseases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        department_id INTEGER,
        description TEXT,
        common_symptoms TEXT,
        severity_level INTEGER DEFAULT 2,
        treatment_method TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)

    # 症状-疾病映射表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symptom_disease_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symptom_id INTEGER NOT NULL,
        disease_id INTEGER NOT NULL,
        weight REAL DEFAULT 1.0,
        FOREIGN KEY (symptom_id) REFERENCES symptoms(id),
        FOREIGN KEY (disease_id) REFERENCES diseases(id),
        UNIQUE(symptom_id, disease_id)
    )
    """)

    # 药品表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        generic_name TEXT,
        category TEXT,
        indication TEXT,
        dosage TEXT,
        side_effects TEXT,
        contraindications TEXT,
        interactions TEXT,
        pregnancy_warning INTEGER DEFAULT 0,
        controlled INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 患者表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        gender TEXT,
        age INTEGER,
        phone TEXT UNIQUE,
        id_card TEXT UNIQUE,
        allergies TEXT,
        medical_history TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 预约表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        schedule_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        department_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        time_slot TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        symptoms TEXT,
        initial_diagnosis TEXT,
        idempotency_key TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (schedule_id) REFERENCES schedules(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)

    # 会话表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL UNIQUE,
        patient_id INTEGER,
        history TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 医学知识库表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT,
        tags TEXT,
        source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
