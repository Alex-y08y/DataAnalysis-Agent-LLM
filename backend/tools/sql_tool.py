"""
SQLQueryTool —— SQL 查询工具

功能：
- 自动生成合规可执行 SQL
- 语法校验
- 拦截 DROP / DELETE / ALTER 高危语句
- 防 SQL 注入
- 查询 MySQL 数据

依赖：pymysql 或 mysql-connector-python
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# 高危 SQL 关键词列表
DANGEROUS_KEYWORDS = [
    r'\bDROP\b',
    r'\bDELETE\b',
    r'\bALTER\b',
    r'\bTRUNCATE\b',
    r'\bUPDATE\b',
    r'\bINSERT\b',
    r'\bCREATE\b',
    r'\bREPLACE\b',
    r'\bGRANT\b',
    r'\bREVOKE\b',
]

# SQL 注入特征
SQL_INJECTION_PATTERNS = [
    r"'.*OR.*'",
    r"'.*--",
    r"'.*;",
    r"1\s*=\s*1",
    r"'\)\s*OR\s*",
    r"UNION.*SELECT",
    r"SLEEP\s*\(",
    r"BENCHMARK\s*\(",
]


class SQLQueryTool(BaseTool):
    """SQL 查询工具

    安全地执行 SQL 查询，带有语法校验、高危拦截和注入防护。

    参数：
        sql_query (str):    需要执行的 SQL 查询语句
        database (str):     数据库名称（可选，默认为配置值）
        params (dict):      查询参数（可选，用于参数化查询）
        limit (int):        返回行数上限（默认 1000）

    返回：
        dict: {
            "columns": [...],      列名列表
            "rows": [...],         数据行列表
            "row_count": int,      行数
            "query_time": float,   查询耗时（秒）
        }
    """

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Args:
            db_config: MySQL 连接配置
                {
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "xxx",
                    "database": "default_db",
                }
        """
        super().__init__(
            name="sql_tool",
            description="执行 SQL 查询，支持 SELECT 语句的语法校验、高危拦截和注入防护",
        )
        self.db_config = db_config or {}
        self._connection = None
        self._parameters = {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "需要执行的 SQL 查询语句",
                },
                "database": {
                    "type": "string",
                    "description": "数据库名称（可选）",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回行数上限，默认 1000",
                    "default": 1000,
                },
            },
            "required": ["sql_query"],
        }

    def execute(
        self,
        sql_query: str,
        database: Optional[str] = None,
        limit: int = 1000,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """执行 SQL 查询

        Args:
            sql_query: SQL 查询语句
            database: 数据库名称（覆盖默认）
            limit: 返回行数上限

        Returns:
            查询结果字典

        Raises:
            ValueError: SQL 校验失败或被拦截时
            RuntimeError: 数据库连接或执行失败时
        """
        # 步骤1：语法校验
        self._validate_sql(sql_query)

        # 步骤2：高危语句拦截
        self._check_dangerous(sql_query)

        # 步骤3：防 SQL 注入
        self._check_injection(sql_query)

        # 步骤4：添加 LIMIT 保护
        safe_query = self._add_limit(sql_query.strip().rstrip(";"), limit)

        # 步骤5：执行查询
        if self.db_config:
            return self._execute_mysql(safe_query, database)
        else:
            logger.info("未配置数据库连接，返回模拟数据。")
            return self._mock_execute(safe_query)

    # ── 安全校验 ──

    def _validate_sql(self, sql: str) -> None:
        """基础 SQL 语法校验

        校验规则：
        - 非空
        - 以 SELECT 开头
        - 括号匹配

        Raises:
            ValueError: 语法不合法时
        """
        sql_stripped = sql.strip()

        if not sql_stripped:
            raise ValueError("SQL 语句不能为空")

        # 允许前导注释和空格
        sql_upper = sql_stripped.upper().lstrip()

        # 仅允许 SELECT 和 WITH（CTE），及 EXPLAIN / DESCRIBE / SHOW
        allowed_prefixes = ("SELECT", "WITH", "EXPLAIN", "DESCRIBE", "DESC", "SHOW")
        if not any(sql_upper.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(
                f"仅支持查询类 SQL（SELECT / WITH / EXPLAIN / DESCRIBE / SHOW），"
                f"当前语句以 '{sql_upper[:20]}' 开头"
            )

        # 括号匹配
        if sql.count("(") != sql.count(")"):
            raise ValueError("SQL 语句括号不匹配")

        logger.info("SQL 语法校验通过")

    def _check_dangerous(self, sql: str) -> None:
        """拦截高危 DDL/DML 语句"""
        sql_upper = sql.strip().upper()
        for pattern in DANGEROUS_KEYWORDS:
            if re.search(pattern, sql_upper):
                raise ValueError(f"高危 SQL 操作已被拦截: 包含关键词 '{pattern}'。出于安全原因，仅允许查询操作。")

        logger.info("高危语句检测通过")

    def _check_injection(self, sql: str) -> None:
        """检测 SQL 注入特征

        此方法用于辅助防护，实际安全应依赖参数化查询。
        """
        sql_normalized = re.sub(r'\s+', ' ', sql.strip())

        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, sql_normalized, re.IGNORECASE):
                logger.warning(f"检测到可能的 SQL 注入特征: 匹配模式 '{pattern}'")
                raise ValueError(f"SQL 注入检测未通过，语句包含可疑特征。请使用参数化查询。")

        logger.info("SQL 注入检测通过")

    @staticmethod
    def _add_limit(sql: str, limit: int) -> str:
        """如果查询没有 LIMIT 子句，自动添加 LIMIT"""
        sql_upper = sql.upper().rstrip()
        if "LIMIT" not in sql_upper:
            sql = f"{sql}\nLIMIT {limit}"
        return sql

    # ── 数据执行 ──

    def _execute_mysql(self, sql: str, database: Optional[str] = None) -> Dict[str, Any]:
        """执行 MySQL 查询"""
        try:
            import pymysql
        except ImportError:
            logger.warning("pymysql 未安装，尝试使用 mysql.connector。")
            try:
                import mysql.connector as connector
                pymysql = None
                use_connector = True
            except ImportError:
                raise RuntimeError("未安装数据库驱动，请安装 pymysql 或 mysql-connector-python")

        db_name = database or self.db_config.get("database", "")
        config = {**self.db_config, "database": db_name}

        import time
        start_time = time.time()

        try:
            if use_connector:
                conn = connector.connect(**config)
            else:
                conn = pymysql.connect(**config)

            with conn.cursor() as cursor:
                cursor.execute(sql)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    # 转为字典列表
                    result_rows = []
                    for row in rows:
                        result_rows.append(dict(zip(columns, row)))
                else:
                    columns = []
                    result_rows = []

            conn.close()

            elapsed = time.time() - start_time
            logger.info(f"SQL 查询完成，返回 {len(result_rows)} 行，耗时 {elapsed:.3f}s")

            return {
                "columns": columns,
                "rows": result_rows,
                "row_count": len(result_rows),
                "query_time": round(elapsed, 3),
            }

        except Exception as e:
            raise RuntimeError(f"MySQL 查询执行失败: {str(e)}")

    def _mock_execute(self, sql: str) -> Dict[str, Any]:
        """模拟执行模式（无数据库时）"""
        import time
        start_time = time.time()

        # 解析 SQL 中的关键信息（模拟用）
        mock_columns = ["id", "name", "value", "create_date"]
        mock_rows = [
            {"id": 1, "name": "样本_A", "value": 100.0, "create_date": "2025-07-01"},
            {"id": 2, "name": "样本_B", "value": 200.0, "create_date": "2025-07-02"},
            {"id": 3, "name": "样本_C", "value": 150.0, "create_date": "2025-07-03"},
        ]

        elapsed = time.time() - start_time

        return {
            "columns": mock_columns,
            "rows": mock_rows,
            "row_count": len(mock_rows),
            "query_time": round(elapsed, 3),
            "mock": True,
            "note": "使用模拟数据运行，未连接真实数据库",
        }
