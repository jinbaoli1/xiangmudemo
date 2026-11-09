"""应用配置"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # LLM 配置
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_USE_MOCK: bool = True

    # 向量模型配置
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_USE_MOCK: bool = True

    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库
    DATABASE_URL: str = "sqlite:///./data/opsalert.db"

    # 数据文件路径
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RUNBOOKS_DIR: Path = DATA_DIR / "runbooks"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()
