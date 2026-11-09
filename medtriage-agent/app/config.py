"""项目配置."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置."""

    app_name: str = "MedTriage 智能分诊导诊系统"
    version: str = "1.0.0"
    debug: bool = True

    # 数据库
    database_url: str = "medtriage.db"

    # 会话
    session_ttl_seconds: int = 3600 * 24  # 24小时

    # 检索配置
    bm25_top_k: int = 20
    tfidf_top_k: int = 20
    reranker_top_k: int = 5

    # 分诊配置
    triage_confidence_threshold: float = 0.6
    max_diagnosis_candidates: int = 5
    critical_symptom_keywords: list = [
        "胸痛", "胸闷", "呼吸困难", "窒息", "咯血", "呕血", "便血",
        "昏迷", "抽搐", "癫痫", "中风", "偏瘫", "失语",
        "剧烈头痛", "高热不退", "严重腹痛", "休克", "晕厥",
        "心脏骤停", "心肌梗塞", "脑溢血", "大出血", "严重外伤"
    ]

    class Config:
        env_file = ".env"


settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app" / "data"
KNOWLEDGE_DIR = BASE_DIR / "app" / "knowledge"
