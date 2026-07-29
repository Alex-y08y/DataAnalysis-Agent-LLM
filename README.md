# DataAnalysis-Agent-LLM · 智能数据分析 AI 智能体

> **个人独立开发开源作品集 · 面向数据分析师 / AI 应用开发求职**
>
> 基于阿里云通义千问 LLM + LangGraph + 本地免费 Embedding + ChromaDB 离线 RAG

---

## 📋 项目简介

**DataAnalysis-Agent-LLM** 是一个企业级自然语言数据分析 AI Agent，业务人员只需中文提问，即可自动完成 **取数 → 清洗 → 统计 → 异常诊断 → 预测 → 可视化 → 报告生成** 全流程。

### 🎯 解决什么问题

| 痛点 → | 解决方案 |
|--------|----------|
| 业务人员取数需等分析师 → | 自然语言对话直接查询，零 SQL 基础 |
| 指标口径混乱难理解 → | RAG 知识库自动检索指标定义 |
| 报表产出慢响应不及时 → | 定时任务自动生成日/周/月报 |
| 向量 API 额度限制/付费 → | 100% 本地 Embedding，零 API 调用，永久免费 |
| 数据安全难管控 → | RBAC 权限 + 数据脱敏 + 全链路审计 |

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                         🖥️  前端交互层                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ 对话分析  │ │ 数据源   │ │ 知识库   │ │ 报表中心 · 任务  │   │
│  │          │ │ 管理     │ │ 管理     │ │ 管理 · 审计日志 │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│                     Vue3 + Element Plus + ECharts                │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼───────────────────────────────────────┐
│                    🤖  AI Agent 核心层                           │
│                                                                  │
│  ┌─────────────────┐    ┌──────────────────────────────────┐    │
│  │  通义千问 LLM    │    │     LangGraph 多轮反思工作流      │    │
│  │  qwen-turbo      │    │  意图识别 → 工具编排 → 结果校验  │    │
│  │  qwen-plus       │    │                                  │    │
│  │  qwen-max        │    └──────────────────────────────────┘    │
│  └─────────────────┘                                            │
│                                                                  │
│  ┌─────────────────┐    ┌──────────────────────────────────┐    │
│  │  本地 RAG 知识库 │    │     记忆管理 + 报告生成           │    │
│  │  Sentence-       │    │  短期记忆 · 长期记忆             │    │
│  │  Transformers    │    │  Markdown / 结构化报告           │    │
│  │  + ChromaDB      │    │                                  │    │
│  │  ✅ 零云端 API   │    │                                  │    │
│  └─────────────────┘    └──────────────────────────────────┘    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    🔧  可插拔工具能力层                          │
│                                                                  │
│  SQL查询(防注入) │ 数据清洗(异常值) │ 多维统计(同比/环比/占比)   │
│  异常检测(风险分级) │ 时序预测(Statsmodels) │ ECharts 可视化     │
│  报告生成(PDF/Excel) │ 数据脱敏(手机号/身份证) │ 文档解析入库    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                    💾  底层存储底座                              │
│         MySQL(业务)  │  ChromaDB(向量)  │  本地文件系统           │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✨ 核心功能

### 💬 智能对话分析
口语化提问自动识别意图：取数、对比、异常、预测、报表 · 缺失条件主动追问 · 多轮上下文记忆 · 执行链路全透明

### 📊 多数据源
MySQL 直连 · Hive 数仓 · CSV/Excel 离线 · HTTP API

### 📈 可视化报表
自动匹配图表类型 · 分析模板复用 · 定时日报/周报/月报 · PDF/Excel 导出

### 🔒 企业级安全
RBAC 三级权限 · 数据脱敏 · SQL 防注入 · 全链路审计日志

---

## 🚀 快速部署

### 前置条件
Python 3.10+ · Node.js 18+ · MySQL 8.0+ · [通义千问 API Key](https://help.aliyun.com/zh/dashscope/)

### 3 分钟启动

```bash
git clone https://github.com/Alex-y08y/DataAnalysis-Agent-LLM.git
cd DataAnalysis-Agent-LLM

cp .env.example .env          # 填写 DASHSCOPE_API_KEY 和 MySQL 密码

cd backend
pip install -r requirements.txt
python scripts/init_db.py
python run.py                  # 后端 → http://localhost:8000

cd frontend
npm install
npm run dev                    # 前端 → http://localhost:5173
```

管理员 **admin / admin123**

### Docker
```bash
docker-compose up -d
```

---

## 📁 项目结构

```
DataAnalysis-Agent-LLM/
├── backend/                     # Python 后端
│   ├── core/llm/               # 通义千问封装（多模型切换·Token统计·异常处理）
│   ├── core/rag/               # 离线 RAG（Sentence-Transformers + ChromaDB）
│   ├── core/agent/             # LangGraph 多轮反思工作流
│   ├── tools/                  # 9 大分析工具（SQL/清洗/统计/异常/预测/图表/报告/脱敏/解析）
│   ├── api/                    # FastAPI 路由（6 个模块）
│   ├── models/                 # SQLAlchemy ORM（5 张表）
│   └── services/               # 业务服务层
├── frontend/                    # Vue3 前端
│   └── src/views/              # 9 个功能页面
├── docs/                       # 系统架构文档 · ER 图 · 建表语句 · 部署手册 · 测试用例
├── resume_intro.md             # 简历介绍文案（可直接复制到简历）
├── .env.example                # 环境变量模板
├── .gitignore                  # 屏蔽密钥/向量库/日志/缓存
├── Dockerfile & docker-compose.yml
└── README.md
```

---

## 🛠️ 技术栈

**后端**: Python · FastAPI · LangChain · LangGraph · DashScope · Sentence-Transformers · ChromaDB · Pandas · Statsmodels · SQLAlchemy · PyJWT

**前端**: Vue3 · Vite · Element Plus · ECharts · Axios · Pinia

**部署**: MySQL · Docker · Docker Compose

---

## 📜 开源 & 求职

- **协议**: MIT License
- **安全**: 密钥 .env 管理，chroma_db/upload_files/report_output/logs 全部 gitignore
- **求职**: 本项目为**个人独立开发开源作品集**，面向**数据分析师、AI 应用开发工程师**岗位

---

> ⭐ 如果对你有帮助，欢迎 Star！
