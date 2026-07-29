# 系统架构设计文档

## 1. 系统概述

DataAnalysis-Agent-LLM 是一个基于阿里云通义千问 LLM + 本地免费 Embedding + ChromaDB 离线 RAG 的企业级自然语言数据分析 Agent。

## 2. 四层架构详细设计

### 2.1 前端交互层（Presentation Layer）

- 框架: Vue 3 + Vite + Element Plus
- 页面: 对话分析、数据源管理、知识库管理、报表中心、任务管理、用户管理、审计日志
- 通信: HTTP REST API + WebSocket 实时对话

### 2.2 AI Agent 核心层（Agent Core Layer）

- LLM 封装: DashScope 通义千问 SDK，多模型切换，Token 统计
- RAG 检索: sentence-transformers 本地 Embedding + ChromaDB 离线存储
- Agent 引擎: LangGraph 多轮反思工作流
- 记忆管理: 短期对话上下文 + 长期任务持久化
- 报告生成: 结构化 Markdown 报告

### 2.3 可插拔工具能力层（Tool Layer）

- SQL查询工具: 安全SQL生成与执行
- 数据清洗工具: 缺失值、重复值、异常值处理
- 多维统计工具: 同比/环比/占比/相关性分析
- 异常检测工具: 指标波动检测与风险分级
- 时序预测工具: Statsmodels 本地算法
- 可视化工具: ECharts 图表渲染
- 数据脱敏工具: 敏感字段自动脱敏
- 文档解析工具: PDF/Excel/Markdown 解析

### 2.4 底层存储底座（Storage Layer）

- MySQL: 用户、数据源、任务、审计日志
- ChromaDB: 文档向量离线存储
- 本地文件系统: 上传文件、导出报表、日志

## 3. 系统流程图

用户提问 -> 意图识别 -> RAG知识库检索 -> SQL生成 -> 数据查询 -> 数据清洗统计 -> 异常检测/预测 -> 图表生成 -> 报告输出

## 4. 安全架构

- RBAC 三级权限: 管理员/分析师/操作员
- SQL 防注入: 语法校验拦截高危操作
- 数据脱敏: 自动脱敏敏感字段
- 全链路审计: 所有操作可追溯
- 密钥管理: .env 配置，不硬编码

## 5. 部署架构

- Docker 容器化部署
- MySQL 独立容器
- 后端 FastAPI + Uvicorn
- 前端 Vue3 + Vite (Nginx 生产环境)
