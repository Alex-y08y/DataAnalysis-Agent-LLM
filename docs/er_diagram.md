# 数据库 ER 图

## 表关系概览

`
┌───────────────┐       ┌──────────────────┐
│     User      │       │  DataSource      │
│───────────────│       │──────────────────│
│ id (PK)       │◄──────│ created_by (FK)  │
│ username      │       │ id (PK)          │
│ password_hash │       │ name             │
│ email         │       │ type             │
│ role          │       │ host             │
│ is_active     │       │ port             │
│ created_at    │       │ user             │
│ updated_at    │       │ password_encrypt │
└───────┬───────┘       │ database_name    │
        │               │ bind_roles       │
        │               │ created_at       │
        │               └──────────────────┘
        │
        │ 1:N
        │
┌───────▼───────────┐   ┌──────────────────┐
│  AnalysisTask     │   │ KnowledgeDoc     │
│───────────────────│   │──────────────────│
│ id (PK)           │   │ id (PK)          │
│ user_id (FK)      │   │ title            │
│ title             │   │ doc_type         │
│ question_text     │   │ file_path        │
│ intent_type       │   │ content_summary  │
│ sql_generated     │   │ chunk_count      │
│ data_result (JSON)│   │ metadata_tags    │
│ chart_config (JSON)│  │ status           │
│ report_content    │   │ created_by (FK)  │
│ status            │   │ created_at       │
│ started_at        │   └──────────────────┘
│ completed_at      │
│ created_at        │
└────────┬──────────┘
         │
         │ 1:N
         │
┌────────▼──────────┐
│    AuditLog       │
│───────────────────│
│ id (PK)           │
│ user_id (FK)      │
│ action_type       │
│ question_text     │
│ sql_executed      │
│ tool_calls (JSON) │
│ file_exported     │
│ ip_address        │
│ created_at        │
└───────────────────┘
`

## 表说明

1. User - 用户表：存储系统用户信息、角色权限
2. DataSource - 数据源表：存储 MySQL/Hive/API 等数据源连接配置
3. AnalysisTask - 分析任务表：记录所有分析任务和结果
4. KnowledgeDocument - 知识库文档表：记录上传的指标文档信息
5. AuditLog - 审计日志表：全链路操作日志
