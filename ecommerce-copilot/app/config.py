"""
应用配置模块
使用 Pydantic Settings 从环境变量加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用全局配置"""

    # ---- LLM 配置 ----
    LLM_API_KEY: Optional[str] = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"

    # Embedding 配置
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ---- 应用配置 ----
    APP_NAME: str = "Commerce Copilot"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True

    # ---- 数据库配置 ----
    DATABASE_URL: str = "sqlite:///./ecommerce.db"

    # ---- 检索配置 ----
    HYBRID_SEARCH_TOP_K: int = 10
    RERANK_TOP_N: int = 3
    BM25_WEIGHT: float = 0.4
    VECTOR_WEIGHT: float = 0.6

    # ---- Mock 模式 ----
    # auto: 自动判断（无 API Key 时启用）
    # always: 始终启用
    # never: 始终禁用
    MOCK_MODE: str = "auto"

    # ---- 售后规则配置 ----
    REFUND_MAX_DAYS: int = 7          # 签收后多少天内可退款
    EXCHANGE_MAX_DAYS: int = 15       # 签收后多少天内可换货
    MAX_REFUND_AMOUNT: float = 10000  # 单笔最大退款金额

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def is_mock_mode(self) -> bool:
        """判断是否处于 Mock 模式"""
        if self.MOCK_MODE == "always":
            return True
        if self.MOCK_MODE == "never":
            return False
        # auto 模式：没有配置 API Key 时启用 mock
        return not bool(self.LLM_API_KEY)


# 全局单例
settings = Settings()
