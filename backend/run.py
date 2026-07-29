#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
DataAnalysis-Agent-LLM 后端启动脚本
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import app_config

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  DataAnalysis-Agent-LLM 服务启动")
    print(f"  地址: http://{app_config.server_host}:{app_config.server_port}")
    print(f"  API文档: http://{app_config.server_host}:{app_config.server_port}/docs")
    print("=" * 50)
    uvicorn.run(
        "main:app",
        host=app_config.server_host,
        port=app_config.server_port,
        reload=app_config.reload,
        log_level="info"
    )

