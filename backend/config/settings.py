"""
DataAnalysis-Agent-LLM 全局配置模块

从 .env 文件读取环境变量，提供统一的配置入口。
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录（backend 上一层）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 加载 .env 文件
dotenv_path = PROJECT_ROOT / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    # 尝试从父级加载
    load_dotenv(override=True)


def _bool(val: str | None, default: bool = False) -> bool:
    """将环境变量字符串转换为布尔值"""
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _int(val: str | None, default: int) -> int:
    """将环境变量字符串转换为整数"""
    if val is None:
        return default
    try:
        return int(val.strip())
    except (ValueError, TypeError):
        return default


def _float(val: str | None, default: float) -> float:
    """将环境变量字符串转换为浮点数"""
    if val is None:
        return default
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# 配置数据类
# ---------------------------------------------------------------------------

@dataclass
class DashScopeConfig:
    """通义千问 / DashScope API 配置"""
    api_key: str = field(
        default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", "")
    )
    model: str = field(
        default_factory=lambda: os.getenv("QWEN_MODEL", "qwen-plus")
    )
    temperature: float = field(
        default_factory=lambda: _float(os.getenv("QWEN_TEMPERATURE"), 0.1)
    )
    # 可选备选模型
    turbo_model: str = "qwen-turbo"
    plus_model: str = "qwen-plus"
    max_model: str = "qwen-max"
    # API 超时（秒）
    timeout: int = field(
        default_factory=lambda: _int(os.getenv("QWEN_TIMEOUT"), 60)
    )
    # 最大重试次数
    max_retries: int = 3


@dataclass
class MySQLConfig:
    """MySQL 数据库连接配置"""
    host: str = field(
        default_factory=lambda: os.getenv("MYSQL_HOST", "127.0.0.1")
    )
    port: int = field(
        default_factory=lambda: _int(os.getenv("MYSQL_PORT"), 3306)
    )
    user: str = field(
        default_factory=lambda: os.getenv("MYSQL_USER", "root")
    )
    password: str = field(
        default_factory=lambda: os.getenv("MYSQL_PASSWORD", "")
    )
    database: str = field(
        default_factory=lambda: os.getenv("MYSQL_DATABASE", "data_analysis")
    )
    charset: str = "utf8mb4"
    pool_size: int = field(
        default_factory=lambda: _int(os.getenv("MYSQL_POOL_SIZE"), 10)
    )
    pool_recycle: int = 3600

    @property
    def dsn(self) -> str:
        """返回 SQLAlchemy 连接字符串"""
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset={self.charset}"
        )


@dataclass
class JWTConfig:
    """JWT 鉴权配置"""
    secret_key: str = field(
        default_factory=lambda: os.getenv(
            "JWT_SECRET_KEY",
            "change_this_to_a_random_secret_key_in_production"
        )
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = field(
        default_factory=lambda: _int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"), 1440
        )
    )  # 默认 24 小时


@dataclass
class RAGConfig:
    """RAG（检索增强生成）配置"""
    # ChromaDB 持久化目录（相对于项目根目录）
    chroma_db_dir: str = field(
        default_factory=lambda: os.getenv(
            "CHROMA_DB_DIR",
            str(PROJECT_ROOT / "chroma_db")
        )
    )
    # Embedding 模型名称
    embedding_model_name: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL_NAME",
            "all-MiniLM-L6-v2"
        )
    )
    # 检索 Top-K
    top_k: int = field(
        default_factory=lambda: _int(os.getenv("RAG_TOP_K"), 5)
    )
    # 相似度阈值（低于该值的结果将被丢弃）
    similarity_threshold: float = field(
        default_factory=lambda: _float(
            os.getenv("RAG_SIMILARITY_THRESHOLD"), 0.45
        )
    )
    # 切分参数
    chunk_size: int = 512
    chunk_overlap: int = 64


@dataclass
class LogConfig:
    """日志配置"""
    log_dir: str = field(
        default_factory=lambda: os.getenv(
            "LOG_DIR",
            str(PROJECT_ROOT / "logs")
        )
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    # 日志保留天数
    log_retention_days: int = 30


@dataclass
class AppConfig:
    """应用整体配置"""
    # 上传文件存储目录
    upload_dir: str = field(
        default_factory=lambda: os.getenv(
            "UPLOAD_DIR",
            str(PROJECT_ROOT / "uploads")
        )
    )
    # FastAPI / 服务端口
    server_host: str = field(
        default_factory=lambda: os.getenv("SERVER_HOST", "0.0.0.0")
    )
    server_port: int = field(
        default_factory=lambda: _int(os.getenv("SERVER_PORT"), 8000)
    )

    # CORS 允许的前端地址
    cors_origins: list = field(
        default_factory=lambda: [
            orig.strip()
            for orig in os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
        ]
    )

    # 是否启用热重载
    reload: bool = field(
        default_factory=lambda: _bool(os.getenv("RELOAD", "true"), True)
    )

    debug: bool = field(
        default_factory=lambda: _bool(os.getenv("DEBUG"), False)
    )


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------

dashscope_config = DashScopeConfig()
mysql_config = MySQLConfig()
jwt_config = JWTConfig()
rag_config = RAGConfig()
log_config = LogConfig()
app_config = AppConfig()


