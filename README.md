# DataAnalysis-Agent-LLM 智能数据分析 AI 智能体

> **个人独立开发开源作品集项目** — 面向数据分析师、AI 应用开发岗位求职展示
>
> 基于阿里云通义千问 LLM + LangGraph + **本地免费 Sentence-Transformers Embedding** + **ChromaDB 离线 RAG**

## 项目简介

**DataAnalysis-Agent-LLM** 是一个基于阿里云通义千问（DashScope）大语言模型 + **完全本地免费 Sentence-Transformers Embedding** + **ChromaDB 离线 RAG 向量存储** 构建的**企业级自然语言数据分析智能 Agent**。

### 解决的企业数据分析痛点

| 痛点 | 方案 |
|------|------|
| 业务人员取数门槛高 | 自然语言对话直接取数分析，零 SQL 基础可用 |
| 指标口径混乱 | RAG 知识库自动检索企业指标规范，杜绝编造 |
| 报表产出周期长 | 异步定时任务自动生成日报/周报/月报 |
| 多维分析重复劳动 | 分析模板一键复用，批量数据分析 |
| **向量额度限制/付费API依赖** | **100% 本地离线 Embedding，零 API 调用，永久免费** |

### 核心特性

- ✅ **全免费架构**：仅消耗通义千问对话免费额度
- ✅ **本地离线 RAG**：sentence-transformers + ChromaDB
- ✅ **多数据源支持**：MySQL、Hive、CSV/Excel、HTTP API
- ✅ **智能对话分析**：多轮上下文记忆，自动识别分析意图
- ✅ **全链路可视化**：知识库检索→SQL→清洗→绘图→结论
- ✅ **企业级安全**：RBAC权限、SQL防注入、数据脱敏、审计日志

## 系统架构

`
┌──────────────────────────────────────────────────┐
│              前端交互层 (Vue3 + Element Plus)       │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│            AI Agent 核心层 (LangGraph)             │
│  LLM封装 │ RAG离线检索 │ Agent调度引擎 │ 记忆管理 │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│           可插拔工具能力层                         │
│  SQL │ 清洗 │ 统计 │ 异常检测 │ 预测 │ 可视化     │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│        底层存储底座 (MySQL + ChromaDB + 文件)      │
└──────────────────────────────────────────────────┘
`

## 技术栈

**后端**: Python, FastAPI, LangChain, LangGraph, DashScope, Sentence-Transformers, ChromaDB, Pandas, Statsmodels, SQLAlchemy

**前端**: Vue3, Vite, Element Plus, ECharts, Pinia, Axios

**存储**: MySQL 8.0+, ChromaDB (本地), Docker

## 本地快速部署

`ash
# 1. 克隆仓库
git clone https://github.com/your-username/DataAnalysis-Agent-LLM.git
cd DataAnalysis-Agent-LLM

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填写 DASHSCOPE_API_KEY

# 3. 启动后端
cd backend
pip install -r requirements.txt
python scripts/init_db.py
python run.py

# 4. 启动前端
cd frontend
npm install
npm run dev

# 访问 http://localhost:5173
# 默认管理员: admin / admin123
`

## 项目目录

`
DataAnalysis-Agent-LLM/
├── backend/              # Python 后端
│   ├── core/llm/        # 通义千问 LLM 封装
│   ├── core/rag/        # 本地 RAG 知识库
│   ├── core/agent/      # LangGraph Agent 引擎
│   ├── tools/           # 9 大可插拔工具
│   ├── api/             # FastAPI 路由
│   ├── models/          # ORM 模型
│   └── services/        # 业务服务
├── frontend/             # Vue3 前端
│   └── src/views/       # 9 个功能页面
├── docs/                 # 项目文档
└── resume_intro.md       # 简历介绍文案
`

## 开源

本项目基于 MIT 协议开源，自由使用、修改、分发。
