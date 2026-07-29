import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import app_config, log_config
from utils.db_utils import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时运行
    print("[启动] DataAnalysis-Agent-LLM 服务启动中...")
    init_db()
    print("[启动] 数据库初始化完成")
    print(f"[启动] 服务监听端口: {app_config.server_port}")
    print(f"[启动] 日志级别: {log_config.log_level}")
    yield
    # 关闭时运行
    print("[关闭] 服务正在关闭...")


app = FastAPI(
    title="DataAnalysis-Agent-LLM API",
    description="智能数据分析 AI 智能体后端 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================
from api.auth_api import router as auth_router
from api.chat_api import router as chat_router
from api.datasource_api import router as datasource_router
from api.knowledge_api import router as knowledge_router
from api.report_api import router as report_router
from api.admin_api import router as admin_router

app.include_router(auth_router, tags=["认证管理"])
app.include_router(chat_router, tags=["智能对话"])
app.include_router(datasource_router, tags=["数据源管理"])
app.include_router(knowledge_router, tags=["知识库管理"])
app.include_router(report_router, tags=["报表管理"])
app.include_router(admin_router, tags=["系统管理"])


@app.get("/")
async def root():
    """根路径，返回服务状态"""
    return {
        "service": "DataAnalysis-Agent-LLM",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=app_config.server_host,
        port=app_config.server_port,
        reload=app_config.reload
    )



