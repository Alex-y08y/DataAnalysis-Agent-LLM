# DataAnalysis-Agent-LLM

> 基于阿里云通义千问 LLM + LangGraph + 本地免费 Embedding + ChromaDB 离线 RAG 的企业级智能数据分析 Agent

---

## 简介

自然语言对话完成数据分析：取数、清洗、统计、异常诊断、预测、可视化、报告生成。**向量模块 100% 本地离线运行，零云端 API 调用，无 Embedding 额度限制。**

## 技术栈

| 层 | 技术 |
|------|------|
| 后端框架 | Python · FastAPI · Uvicorn |
| AI 引擎 | LangChain · LangGraph |
| 大语言模型 | 阿里云通义千问 DashScope (qwen-turbo/plus/max) |
| 本地 Embedding | Sentence-Transformers / all-MiniLM-L6-v2 |
| 向量存储 | ChromaDB (本地离线) |
| 数据处理 | Pandas · NumPy · Statsmodels |
| 数据库 | MySQL · SQLAlchemy |
| 安全 | JWT · RBAC · 数据脱敏 |
| 前端 | Vue3 · Vite · Element Plus · ECharts |
| 部署 | Docker · Docker Compose |

## 架构

`
┌────────────────────────────────────────┐
│  前端交互 (Vue3 + Element Plus)         │
├────────────────────────────────────────┤
│  AI Agent 核心层                       │
│  LLM → RAG检索 → Agent调度 → 报告生成  │
├────────────────────────────────────────┤
│  可插拔工具层                          │
│  SQL查询 · 数据清洗 · 统计 · 异常检测   │
│  时序预测 · 可视化 · 脱敏 · 文档解析    │
├────────────────────────────────────────┤
│  存储底座 (MySQL + ChromaDB + 文件)     │
└────────────────────────────────────────┘
`

## 快速开始

`ash
# 1. 克隆
git clone https://github.com/Alex-y08y/DataAnalysis-Agent-LLM.git
cd DataAnalysis-Agent-LLM

# 2. 配置
cp .env.example .env
# 编辑 .env 填写 DASHSCOPE_API_KEY 和 MySQL 密码

# 3. 后端
cd backend
pip install -r requirements.txt
python scripts/init_db.py
python run.py

# 4. 前端
cd frontend
npm install
npm run dev
`

访问 http://localhost:5173，默认管理员 admin / admin123。

## 目录结构

`
DataAnalysis-Agent-LLM/
├── backend/           # Python 后端
│   ├── core/llm/     # 通义千问 LLM 封装
│   ├── core/rag/     # 本地离线 RAG 知识库
│   ├── core/agent/   # LangGraph Agent 引擎
│   ├── tools/        # 9 个分析工具
│   ├── api/          # FastAPI 路由
│   ├── models/       # ORM 模型
│   └── services/     # 业务服务
├── frontend/          # Vue3 前端
│   └── src/views/    # 9 个功能页面
├── docs/              # 项目文档
└── resume_intro.md    # 简历介绍
`

## 核心特性

- 自然语言对话取数分析，无需 SQL 基础
- 知识库 RAG 检索业务指标定义，杜绝编造
- 多数据源：MySQL / Hive / CSV / API
- 全链路可视化：检索→SQL→清洗→统计→绘图→结论
- RBAC 权限 + 数据脱敏 + 审计日志
- Docker 容器化部署

## 协议

MIT License
