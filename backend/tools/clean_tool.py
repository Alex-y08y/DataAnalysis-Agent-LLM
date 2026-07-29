"""
DataCleanTool —— 数据清洗工具

功能：
- 批量处理缺失值（删除 / 填充 / 插值）
- 去除重复值
- 处理极端异常值（截尾 / 替换）
- 统一数据格式（日期 / 数字 / 文本）
"""

import math
import re
import statistics
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class DataCleanTool(BaseTool):
    """数据清洗工具

    对结构化数据集执行常见的数据清洗操作。

    参数：
        data (list):         待清洗的数据列表（字典列表）
        missing_strategy (str): 缺失值处理策略：drop / fill_mean / fill_median / fill_mode / fill_value / interpolate
        fill_value:             自定义填充值（当 missing_strategy='fill_value' 时使用）
        deduplicate (bool):     是否去重，默认 True
        outlier_strategy (str): 异常值处理策略：none / clip / remove
        outlier_method (str):   异常值检测方法：iqr / zscore
        outlier_threshold (float): 异常值阈值（IQR 倍数，默认 1.5；或 z-score 阈值，默认 3.0）
        date_columns (list):    需要解析为日期格式的列名列表
        number_columns (list):  需要转为数字格式的列名列表
        string_trim (bool):     是否 trim 字符串，默认 True

    返回：
        dict: {
            "cleaned_data": [...],     清洗后的数据
            "operations": [...],        执行的操作记录
            "stats": {...},             清洗统计信息
        }
    """

    def __init__(self):
        super().__init__(
            name="clean_tool",
            description="数据清洗工具，处理缺失值、重复值、异常值和格式统一",
        )
        self._parameters = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "description": "待清洗的数据列表（字典列表）",
                },
                "missing_strategy": {
                    "type": "string",
                    "enum": ["drop", "fill_mean", "fill_median", "fill_mode", "fill_value", "interpolate"],
                    "description": "缺失值处理策略",
                    "default": "fill_mean",
                },
                "fill_value": {
                    "description": "自定义填充值（当 missing_strategy='fill_value' 时使用）",
                },
                "deduplicate": {
                    "type": "boolean",
                    "description": "是否去重",
                    "default": True,
                },
                "outlier_strategy": {
                    "type": "string",
                    "enum": ["none", "clip", "remove"],
                    "description": "异常值处理策略",
                    "default": "clip",
                },
                "outlier_method": {
                    "type": "string",
                    "enum": ["iqr", "zscore"],
                    "description": "异常值检测方法",
                    "default": "iqr",
                },
                "date_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要解析为日期格式的列名",
                },
                "number_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要转为数字格式的列名",
                },
            },
            "required": ["data"],
        }

    def execute(
        self,
        data: List[Dict[str, Any]],
        missing_strategy: str = "fill_mean",
        fill_value: Any = None,
        deduplicate: bool = True,
        outlier_strategy: str = "clip",
        outlier_method: str = "iqr",
        outlier_threshold: float = 1.5,
        date_columns: Optional[List[str]] = None,
        number_columns: Optional[List[str]] = None,
        string_trim: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """执行数据清洗"""
        start_row_count = len(data)
        operations = []
        cleaned_data = [dict(row) for row in data]  # 深拷贝
        stats = {
            "start_rows": start_row_count,
            "end_rows": start_row_count,
            "missing_handled": 0,
            "duplicates_removed": 0,
            "outliers_handled": 0,
            "formats_converted": 0,
        }

        if not cleaned_data:
            return {"cleaned_data": [], "operations": [], "stats": stats}

        all_columns = list(cleaned_data[0].keys())
        date_columns = date_columns or []
        number_columns = number_columns or []

        # 步骤1：格式统一
        if date_columns or number_columns or string_trim:
            convert_count = self._unify_formats(
                cleaned_data, all_columns, date_columns, number_columns, string_trim
            )
            stats["formats_converted"] = convert_count
            operations.append({
                "step": "format_unify",
                "detail": f"格式统一处理 {convert_count} 个字段",
            })

        # 步骤2：缺失值处理
        if missing_strategy != "none":
            missing_handled = self._handle_missing_values(
                cleaned_data, all_columns, missing_strategy, fill_value
            )
            stats["missing_handled"] = missing_handled
            operations.append({
                "step": "missing_values",
                "detail": f"缺失值处理 ({missing_strategy})，共处理 {missing_handled} 个",
            })

        # 步骤3：去重
        if deduplicate:
            before_dedup = len(cleaned_data)
            cleaned_data = self._remove_duplicates(cleaned_data)
            removed = before_dedup - len(cleaned_data)
            stats["duplicates_removed"] = removed
            operations.append({"step": "deduplicate", "detail": f"移除了 {removed} 条重复数据"})

        # 步骤4：异常值处理
        if outlier_strategy != "none":
            numeric_cols = number_columns or self._detect_numeric_columns(cleaned_data, all_columns)
            cleaned_data, outliers_handled = self._handle_outliers(
                cleaned_data, numeric_cols, outlier_strategy, outlier_method, outlier_threshold
            )
            stats["outliers_handled"] = outliers_handled
            operations.append({
                "step": "outliers",
                "detail": f"异常值处理 ({outlier_strategy}/{outlier_method})，共处理 {outliers_handled} 个",
            })

        stats["end_rows"] = len(cleaned_data)

        logger.info(
            f"数据清洗完成: {stats['start_rows']}行→{stats['end_rows']}行, "
            f"缺失{stats['missing_handled']}, 去重{stats['duplicates_removed']}, "
            f"异常{stats['outliers_handled']}"
        )

        return {"cleaned_data": cleaned_data, "operations": operations, "stats": stats}

    # ── 格式统一 ──

    def _unify_formats(self, data, all_columns, date_columns, number_columns, string_trim):
        convert_count = 0
        for row in data:
            for col in all_columns:
                raw = row.get(col)
                if raw is None:
                    continue
                if col in date_columns and isinstance(raw, str):
                    try:
                        row[col] = self._parse_date(raw)
                        convert_count += 1
                    except (ValueError, TypeError):
                        pass
                elif col in number_columns and isinstance(raw, str):
                    try:
                        row[col] = self._parse_number(raw)
                        convert_count += 1
                    except (ValueError, TypeError):
                        pass
                elif string_trim and isinstance(raw, str):
                    trimmed = raw.strip()
                    if trimmed != raw:
                        row[col] = trimmed
                        convert_count += 1
        return convert_count

    @staticmethod
    def _parse_date(value: str) -> str:
        formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日",
            "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        raise ValueError(f"无法解析日期: {value}")

    @staticmethod
    def _parse_number(value: str) -> Union[int, float]:
        cleaned = value.strip().replace(",", "").replace(" ", "")
        if cleaned.endswith("%"):
            return float(cleaned.rstrip("%")) / 100.0
        return float(cleaned) if "." in cleaned else int(cleaned)

    @staticmethod
    def _detect_numeric_columns(data, all_columns):
        numeric_cols = []
        for col in all_columns:
            numeric_count = sum(1 for row in data if isinstance(row.get(col), (int, float)))
            if numeric_count >= len(data) * 0.8:
                numeric_cols.append(col)
        return numeric_cols

    # ── 缺失值处理 ──

    def _handle_missing_values(self, data, all_columns, strategy, fill_value):
        handled = 0
        numeric_cols = self._detect_numeric_columns(data, all_columns)

        fill_values = {}
        if strategy in ("fill_mean", "fill_median", "fill_mode"):
            for col in numeric_cols:
                values = [row[col] for row in data if row.get(col) is not None and isinstance(row.get(col), (int, float))]
                if not values:
                    continue
                if strategy == "fill_mean":
                    fill_values[col] = statistics.mean(values)
                elif strategy == "fill_median":
                    fill_values[col] = statistics.median(values)
                elif strategy == "fill_mode":
                    try:
                        fill_values[col] = statistics.mode(values)
                    except statistics.StatisticsError:
                        fill_values[col] = statistics.median(values)
        elif strategy == "fill_value":
            for col in all_columns:
                fill_values[col] = fill_value if fill_value is not None else "N/A"

        for row in data:
            for col in all_columns:
                val = row.get(col)
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    if strategy == "drop":
                        continue
                    elif col in fill_values:
                        row[col] = fill_values[col]
                        handled += 1
                    else:
                        row[col] = "N/A"
                        handled += 1

        if strategy == "drop":
            before = len(data)
            data[:] = [
                row for row in data
                if not any(
                    row.get(col) is None or (isinstance(row.get(col), float) and math.isnan(row.get(col)))
                    for col in all_columns
                )
            ]
            handled += before - len(data)

        if strategy == "interpolate":
            for col in numeric_cols:
                self._interpolate_column(data, col)
            handled = sum(1 for row in data for col in all_columns if row.get(col) is not None)

        return handled

    @staticmethod
    def _interpolate_column(data, col):
        indices = list(range(len(data)))
        values = []
        known_indices = []
        for i, row in enumerate(data):
            val = row.get(col)
            if val is not None and isinstance(val, (int, float)):
                values.append(val)
                known_indices.append(i)
        if len(values) < 2:
            return
        for i in indices:
            if i not in known_indices:
                prev_idx = max([k for k in known_indices if k < i], default=None)
                next_idx = min([k for k in known_indices if k > i], default=None)
                if prev_idx is not None and next_idx is not None:
                    ratio = (i - prev_idx) / (next_idx - prev_idx)
                    data[i][col] = data[prev_idx][col] + (data[next_idx][col] - data[prev_idx][col]) * ratio
                elif prev_idx is not None:
                    data[i][col] = data[prev_idx][col]
                elif next_idx is not None:
                    data[i][col] = data[next_idx][col]

    @staticmethod
    def _remove_duplicates(data):
        seen = set()
        result = []
        for row in data:
            key = tuple(sorted(row.items()))
            if key not in seen:
                seen.add(key)
                result.append(row)
        return result

    # ── 异常值处理 ──

    def _handle_outliers(self, data, numeric_cols, strategy, method, threshold):
        handled = 0
        rows_to_remove = set()

        for col in numeric_cols:
            values = [row[col] for row in data if row.get(col) is not None and isinstance(row.get(col), (int, float))]
            if len(values) < 4:
                continue
            if method == "iqr":
                lower, upper = self._iqr_bounds(values, threshold)
            else:
                lower, upper = self._zscore_bounds(values, threshold)

            for idx, row in enumerate(data):
                val = row.get(col)
                if val is not None and isinstance(val, (int, float)):
                    if val < lower or val > upper:
                        if strategy == "clip":
                            row[col] = lower if val < lower else upper
                        elif strategy == "remove":
                            rows_to_remove.add(idx)
                        handled += 1

        if strategy == "remove":
            data[:] = [row for i, row in enumerate(data) if i not in rows_to_remove]

        return data, handled

    @staticmethod
    def _iqr_bounds(values, multiplier=1.5):
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        return q1 - multiplier * iqr, q3 + multiplier * iqr

    @staticmethod
    def _zscore_bounds(values, threshold=3.0):
        mean = statistics.mean(values)
        if len(values) < 2:
            return mean - threshold, mean + threshold
        stdev = statistics.stdev(values)
        return mean - threshold * stdev, mean + threshold * stdev
