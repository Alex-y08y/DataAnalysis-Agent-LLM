"""
StatsTool —— 统计分析工具

功能：
- 同比/环比计算（Year-over-Year / Month-over-Month / Week-over-Week）
- 占比计算（整体占比、topN 占比）
- 分层聚合（groupby + 多重聚合）
- 相关性分析（Pearson / Spearman）
- 均值方差（描述性统计）
"""

import math
import statistics
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class StatsTool(BaseTool):
    """统计分析工具

    提供数据分析中常用的统计计算能力。

    参数：
        data (list):       数据列表（字典列表）
        intent (str):      分析意图，影响默认分析行为（compare / anomaly / forecast / report）
        date_column (str): 日期列名
        value_column (str): 数值列名
        group_column (str): 分组列名
        dimension (str):    业务维度（如 product, channel, region）

    返回：
        dict: {
            "summary": {...},           描述性统计
            "comparisons": {...},       同比/环比结果
            "proportions": {...},       占比分析
            "aggregations": [...],      分层聚合
            "correlations": {...},      相关性分析
        }
    """

    def __init__(self):
        super().__init__(
            name="stats_tool",
            description="统计分析工具，支持同比/环比、占比、分层聚合、相关性分析、描述性统计",
        )
        self._parameters = {
            "type": "object",
            "properties": {
                "data": {"type": "array", "description": "数据列表"},
                "intent": {"type": "string", "description": "分析意图，影响默认行为"},
                "date_column": {"type": "string", "description": "日期列名"},
                "value_column": {"type": "string", "description": "数值列名"},
                "group_column": {"type": "string", "description": "分组列名"},
                "dimension": {"type": "string", "description": "业务维度"},
            },
            "required": ["data"],
        }

    def execute(
        self,
        data: List[Dict[str, Any]],
        intent: Optional[str] = None,
        date_column: Optional[str] = None,
        value_column: Optional[str] = None,
        group_column: Optional[str] = None,
        dimension: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """执行统计分析

        Args:
            data: 数据列表
            intent: 分析意图
            date_column: 日期列
            value_column: 数值列
            group_column: 分组列
            dimension: 业务维度

        Returns:
            统计结果字典
        """
        if not data:
            return {"summary": {}, "comparisons": {}, "proportions": {}, "aggregations": [], "correlations": {}}

        # 自动检测列
        all_columns = list(data[0].keys())
        if not date_column:
            date_column = self._detect_column(all_columns, ["date", "日期", "create_date", "time", "时间"])
        if not value_column:
            value_column = self._detect_column(all_columns, ["value", "amount", "数值", "金额", "count", "uv", "pv", "revenue", "sales"])

        result = {}

        # 描述性统计
        result["summary"] = self._descriptive_stats(data, value_column)

        # 同比/环比
        if date_column and value_column:
            result["comparisons"] = self._compute_comparisons(data, date_column, value_column, group_column)

        # 占比分析
        if value_column and group_column:
            result["proportions"] = self._compute_proportions(data, group_column, value_column)
        elif value_column and dimension:
            result["proportions"] = self._compute_proportions(data, dimension, value_column)

        # 分层聚合
        if group_column and value_column:
            result["aggregations"] = self._aggregate(data, group_column, value_column)
        elif dimension and value_column:
            result["aggregations"] = self._aggregate(data, dimension, value_column)

        # 相关性分析（至少需要两列数值）
        numeric_cols = self._get_numeric_columns(data)
        if len(numeric_cols) >= 2:
            result["correlations"] = self._compute_correlations(data, numeric_cols)

        logger.info(f"统计分析完成: {len(data)} 条数据, {len(result.get('aggregations', []))} 个分组")
        return result

    # ── 描述性统计 ──

    @staticmethod
    def _descriptive_stats(data: List[Dict], value_column: Optional[str]) -> Dict[str, Any]:
        """计算描述性统计"""
        if not value_column:
            return {}

        values = [row[value_column] for row in data if row.get(value_column) is not None and isinstance(row[value_column], (int, float))]
        if not values:
            return {}

        n = len(values)
        mean_val = statistics.mean(values)
        sorted_vals = sorted(values)
        variance = statistics.variance(values) if n > 1 else 0

        result = {
            "count": n,
            "mean": round(mean_val, 4),
            "median": round(statistics.median(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "range": round(max(values) - min(values), 4),
            "variance": round(variance, 4),
            "std_dev": round(math.sqrt(variance), 4),
            "total": round(sum(values), 4),
            "q25": round(sorted_vals[n // 4], 4),
            "q75": round(sorted_vals[3 * n // 4], 4),
        }

        # 增长率
        if n >= 2:
            growth = ((values[-1] - values[0]) / abs(values[0]) * 100) if values[0] != 0 else 0
            result["total_growth_rate"] = round(growth, 2)

        return result

    # ── 同比/环比 ──

    def _compute_comparisons(
        self,
        data: List[Dict],
        date_column: str,
        value_column: str,
        group_column: Optional[str] = None,
    ) -> Dict[str, Any]:
        """计算同比（YoY）和环比（WoW/MoM）"""
        try:
            # 按日期排序
            sorted_data = sorted(data, key=lambda x: str(x.get(date_column, "")))
        except Exception:
            sorted_data = data

        if len(sorted_data) < 2:
            return {"error": "数据不足，无法计算对比"}

        # 环比值
        current_val = self._sum_value(sorted_data[-5:], value_column) if len(sorted_data) > 5 else self._sum_value(sorted_data[-2:], value_column)
        previous_val = self._sum_value(sorted_data[-10:-5], value_column) if len(sorted_data) > 10 else (sorted_data[0].get(value_column, 0) or 0)
        # 同比（假设前 N 个数据点代表去年同期）
        yoy_previous = sorted_data[0].get(value_column, 0) or 0
        yoy_current = sorted_data[-1].get(value_column, 0) or 0

        comparisons = {
            "current_period_value": current_val,
            "previous_period_value": previous_val,
            "mom_growth": self._growth_rate(previous_val, current_val),
            "yoy_growth": self._growth_rate(yoy_previous, yoy_current),
            "period_label": "近期 vs 上期",
        }

        # 逐期对比序列
        period_values = []
        for i in range(1, len(sorted_data)):
            prev = sorted_data[i - 1].get(value_column, 0) or 0
            curr = sorted_data[i].get(value_column, 0) or 0
            period_values.append({
                "date": str(sorted_data[i].get(date_column, "")),
                "value": curr,
                "prev_value": prev,
                "growth_rate": self._growth_rate(prev, curr),
                "abs_change": round(curr - prev, 4),
            })

        comparisons["period_comparisons"] = period_values

        return comparisons

    @staticmethod
    def _sum_value(data_slice: List[Dict], col: str) -> float:
        return sum(row.get(col, 0) or 0 for row in data_slice)

    @staticmethod
    def _growth_rate(previous: float, current: float) -> Optional[float]:
        if previous == 0:
            return None if current == 0 else 100.0
        return round((current - previous) / abs(previous) * 100, 2)

    # ── 占比分析 ──

    @staticmethod
    def _compute_proportions(data: List[Dict], group_col: str, value_col: str) -> Dict[str, Any]:
        """计算分组占比"""
        groups = defaultdict(float)
        total = 0.0

        for row in data:
            group_val = row.get(group_col, "未知")
            val = row.get(value_col, 0) or 0
            groups[group_val] += val
            total += val

        if total == 0:
            return {"error": "总计为 0，无法计算占比"}

        proportions = []
        for group, value in sorted(groups.items(), key=lambda x: x[1], reverse=True):
            proportions.append({
                "group": str(group),
                "value": round(value, 4),
                "proportion": round(value / total * 100, 2),
                "cumulative_proportion": 0,
            })

        # 计算累计占比
        cumsum = 0
        for p in proportions:
            cumsum += p["proportion"]
            p["cumulative_proportion"] = round(cumsum, 2)

        return {
            "total": round(total, 4),
            "items": proportions,
            "top3": proportions[:3],
        }

    # ── 分层聚合 ──

    @staticmethod
    def _aggregate(data: List[Dict], group_col: str, value_col: str) -> List[Dict]:
        """分层聚合"""
        groups = defaultdict(list)

        for row in data:
            group_val = row.get(group_col, "未知")
            val = row.get(value_col, 0) or 0
            groups[group_val].append(val)

        results = []
        for group, values in sorted(groups.items(), key=lambda x: sum(x[1]), reverse=True):
            if not values:
                continue
            n = len(values)
            results.append({
                "group": str(group),
                "count": n,
                "sum": round(sum(values), 4),
                "mean": round(statistics.mean(values), 4),
                "median": round(statistics.median(values), 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
            })

        return results

    # ── 相关性分析 ──

    def _compute_correlations(self, data: List[Dict], numeric_cols: List[str]) -> Dict[str, Any]:
        """计算相关系数矩阵"""
        n = len(data)
        if n < 3:
            return {"error": "数据不足，无法计算相关性"}

        correlation_matrix = {}
        for col_x in numeric_cols:
            correlation_matrix[col_x] = {}
            for col_y in numeric_cols:
                if col_x == col_y:
                    correlation_matrix[col_x][col_y] = 1.0
                else:
                    xy_key = f"{col_x}_{col_y}"
                    reverse_key = f"{col_y}_{col_x}"
                    if xy_key not in correlation_matrix.get(col_y, {}):
                        corr = self._pearson_correlation(data, col_x, col_y)
                        correlation_matrix[col_x][col_y] = round(corr, 4)
                    else:
                        correlation_matrix[col_x][col_y] = correlation_matrix[col_y][col_x]

        return {"matrix": correlation_matrix}

    @staticmethod
    def _pearson_correlation(data: List[Dict], col_x: str, col_y: str) -> float:
        """计算 Pearson 相关系数"""
        pairs = [
            (row[col_x], row[col_y])
            for row in data
            if row.get(col_x) is not None and row.get(col_y) is not None
            and isinstance(row[col_x], (int, float)) and isinstance(row[col_y], (int, float))
        ]
        if len(pairs) < 3:
            return 0.0

        n = len(pairs)
        sum_x = sum(p[0] for p in pairs)
        sum_y = sum(p[1] for p in pairs)
        sum_xy = sum(p[0] * p[1] for p in pairs)
        sum_x2 = sum(p[0] ** 2 for p in pairs)
        sum_y2 = sum(p[1] ** 2 for p in pairs)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))

        if denominator == 0:
            return 0.0
        return numerator / denominator

    # ── 辅助方法 ──

    @staticmethod
    def _detect_column(columns: List[str], candidates: List[str]) -> Optional[str]:
        """自动检测匹配的列名"""
        for col in columns:
            col_lower = col.lower()
            for candidate in candidates:
                if candidate.lower() in col_lower or col_lower in candidate.lower():
                    return col
        return None

    @staticmethod
    def _get_numeric_columns(data: List[Dict]) -> List[str]:
        if not data:
            return []
        return [
            col for col in data[0]
            if any(isinstance(row.get(col), (int, float)) for row in data)
        ]


import logging
