#!/bin/bash
# ============================================================
# DataAnalysis-Agent-LLM 一键启动脚本
# ============================================================

echo "============================================"
echo " DataAnalysis-Agent-LLM 一键启动"
echo "============================================"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "[警告] 未找到 .env 文件，正在从 .env.example 复制..."
    cp .env.example .env
    echo "[提示] 请编辑 .env 文件填写 DASHSCOPE_API_KEY 和 MySQL 配置"
    exit 1
fi

# 启动后端
echo "[1/2] 启动后端服务..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
echo "初始化数据库..."
python scripts/init_db.py
echo "启动 API 服务..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=\$!
cd ..

# 启动前端
echo "[2/2] 启动前端服务..."
cd frontend
npm install --silent
npm run dev &
FRONTEND_PID=\$!
cd ..

echo "============================================"
echo " 后端服务: http://localhost:8000"
echo " 前端页面: http://localhost:5173"
echo " API文档: http://localhost:8000/docs"
echo "============================================"
echo "按 Ctrl+C 停止所有服务"

# 捕获 SIGINT 信号
trap "kill \ \ 2>/dev/null; exit" SIGINT SIGTERM

# 等待子进程
wait
