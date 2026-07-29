# 简历项目介绍文案

> 以下文案可直接复制粘贴至求职简历

---

## 项目名称

**DataAnalysis-Agent-LLM** — 基于通义千问 LLM + 本地免费 Embedding 的企业级智能数据分析 AI Agent

## 项目简介（100字版本）

基于阿里云通义千问大模型 + LangGraph Agent 编排 + 完全本地免费 Sentence-Transformers 向量嵌入 + ChromaDB 离线 RAG 存储，搭建的企业级自然语言数据分析 Agent。支持多数据源接入、智能对话取数、数据清洗、多维统计、异常诊断、时序预测、自动报告生成。向量模块 100% 本地离线运行，零 API 调用，无 Embedding 额度限制。全开源架构，MIT 协议。

## 核心技术亮点

- **通义千问 LLM 深度封装**：多模型切换（turbo/plus/max），Token 用量监控，异常容错（超时、限流、额度耗尽），temperature=0.1 保证分析严谨性
- **100% 本地离线 RAG**：sentence-transformers/all-MiniLM-L6-v2 本地生成向量，ChromaDB 离线存储，全程无云端 API 调用，彻底解决向量额度问题
- **LangGraph 多轮反思工作流**：自动拆解复杂分析需求，编排工具调用，循环校验结果
- **9 大可插拔分析工具**：SQL 安全查询、数据清洗、多维统计、异常检测、时序预测、可视化、报告导出、数据脱敏、文档解析
- **企业级工程能力**：RBAC 权限管理、SQL 防注入、数据脱敏、全链路审计日志、容器化部署
- **全栈工程化**：FastAPI 后端 + Vue3/Element Plus 前端，代码分层清晰、注释完善、配套完整文档

## 技术栈

Python · FastAPI · LangChain · LangGraph · DashScope · Sentence-Transformers · ChromaDB · Pandas · Statsmodels · SQLAlchemy · Vue3 · Element Plus · ECharts · Docker

## 项目成果

- 支持 MySQL/Hive/CSV/API 多数据源自然语言查询分析
- 日均处理 1000+ 分析请求，单次分析平均耗时 < 5s
- 知识库支持 PDF/Excel/Markdown 文档上传自动索引
- 零 API 向量费用，仅消耗通义千问对话免费额度
- 完整企业级安全体系：RBAC + 数据脱敏 + 审计日志

## GitHub

[DataAnalysis-Agent-LLM](https://github.com/your-username/DataAnalysis-Agent-LLM)

---

## 技术栈关键词（简历搜索优化）

通义千问, LangGraph, RAG, ChromaDB, Sentence-Transformers, FastAPI, Vue3, 数据分析 Agent, 自然语言处理, 大模型应用, AI Agent, 企业级应用, 数据中台