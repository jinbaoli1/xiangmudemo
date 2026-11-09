"""
数据库基类和连接管理
使用 SQLAlchemy + SQLite
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# 创建引擎（SQLite 需加 check_same_thread=False）
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.APP_DEBUG,
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型以确保 Base.metadata 包含它们
    from app.models.product import Product  # noqa: F401
    from app.models.order import Order, OrderItem  # noqa: F401
    from app.models.after_sale import AfterSaleRequest  # noqa: F401
    from app.models.conversation import Conversation, Message  # noqa: F401

    Base.metadata.create_all(bind=engine)
