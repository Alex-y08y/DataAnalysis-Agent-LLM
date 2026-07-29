# 本地部署操作手册

## 环境要求

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- MySQL 8.0 或更高版本
- 阿里云 DashScope API Key（免费开通）

## 第一步：环境准备

### 1.1 安装 Python 3.10+
下载地址：https://www.python.org/downloads/
验证安装：
`ash
python --version
`

### 1.2 安装 Node.js 18+
下载地址：https://nodejs.org/
验证安装：
`ash
node --version
npm --version
`

### 1.3 安装 MySQL 8.0+
下载地址：https://dev.mysql.com/downloads/mysql/
创建数据库：
`sql
CREATE DATABASE IF NOT EXISTS data_analysis_agent
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
`

## 第二步：克隆项目并配置

`ash
git clone https://github.com/your-username/DataAnalysis-Agent-LLM.git
cd DataAnalysis-Agent-LLM

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，修改以下配置：
# DASHSCOPE_API_KEY=你的通义千问API Key
# MYSQL_PASSWORD=你的MySQL密码
`

## 第三步：启动后端服务

`ash
cd backend

# 创建 Python 虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（创建表和默认管理员）
python scripts/init_db.py

# 启动后端服务
python run.py
# 或: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
`

后端启动后，访问 http://localhost:8000/docs 查看 API 文档。

## 第四步：启动前端服务

`ash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
`

前端启动后，访问 http://localhost:5173 进入系统。

## 第五步：验证部署

1. 访问前端页面：http://localhost:5173
2. 使用默认管理员账号登录：admin / admin123
3. 测试对话分析功能
4. 测试数据源管理
5. 测试知识库上传

## Docker 部署

`ash
# 确保已安装 Docker 和 Docker Compose
# 编辑 .env 文件配置 DASHSCOPE_API_KEY 和 MySQL 密码

# 一键启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
`

## 常见问题

### Q: 首次启动下载 Embedding 模型很慢？
模型文件约 90MB，首次启动会自动下载到 HuggingFace 缓存目录。后续启动将离线运行。

### Q: MySQL 连接失败？
检查 .env 中的 MYSQL_HOST、MYSQL_PORT、MYSQL_USER、MYSQL_PASSWORD 配置是否正确。

### Q: 通义千问 API 调用失败？
确认 DASHSCOPE_API_KEY 正确且账户有免费额度。DashScope 新用户有免费额度。
