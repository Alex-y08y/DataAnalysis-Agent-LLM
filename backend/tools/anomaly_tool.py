"""
AnomalyDetectionTool —— 异常检测工具

功能：
- 识别指标大幅波动（3-Sigma / IQR / 移动平均偏差）
- 自动溯源异常维度
- 划分风险等级（critical / high / medium / low）

提供基于统计学的无监督异常检测能力，无需外部 ML 依赖。
"""

import math
import statistics
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class AnomalyDetectionTool(BaseTool):
    """异常检测工具

    通过统计方法自动识别数据中的异常波动，并溯源相关维度。

    参数：
        data (list):          数据列表，每条需包含时间戳和数值
        date_column (str):    日期/时间列名
        value_column (str):   需要检测的数值列名
        dimension_columns (list): 用于溯源的维度列名（如 region, product, channel）
        method (str):         检测方法：zscore / iqr / mad（默认 zscore）
        threshold (float):    异常阈值：Z-Score 默认 3.0，IQR 倍数默认 1.5
        window_size (int):    移动平均窗口大小（默认 7）

    返回：
        dict: {
            "anomalies": [...],          异常点列表
            "summary": {...},             总体概况
            "dimension_insights": [...],  维度溯源
            "risk_level": str,            整体风险等级
        }
    """

    RISK_LEVELS = {
        "critical": {"max_ratio": float("inf"), "label": "🔴 严重"},
        "high": {"max_ratio": 50, "label": "🟠 较高"},
        "medium": {"max_ratio": 30, "label": "🟡 中等"},
        "low": {"max_ratio": 15, "label": "🟢 较低"},
    }

    def __init__(self):
        super().__init__(
            name="anomaly_tool",
            description="异常检测工具，识别指标波动、溯源异常维度、划分风险等级",
        )
        self._parameters = {
            "type": "object",
            "properties": {
                "data": {"type": "array", "description": "数据列表"},
                "date_column": {"type": "string", "description": "日期列名"},
                "value_column": {"type": "string", "description": "数值列名"},
                "dimension_columns": {
                    "type": "array", "items": {"type": "string"},
                    "description": "溯源维度列名列表",
                },
                "method": {
                    "type": "string", "enum": ["zscore", "iqr", "mad"],
                    "description": "检测方法",
                },
                "threshold": {"type": "number", "description": "异常阈值"},
                "window_size": {"type": "integer", "description": "移动平均窗口大小"},
            },
            "required": ["data", "value_column"],
        }

    def execute(
        self,
        data: List[Dict[str, Any]],
        date_column: Optional[str] = None,
        value_column: Optional[str] = None,
        dimension_columns: Optional[List[str]] = None,
        method: str = "zscore",
        threshold: float = 3.0,
        window_size: int = 7,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """执行异常检测

        Args:
            data: 数据列表
            date_column: 日期列名
            value_column: 数值列名
            dimension_columns: 溯源维度
            method: 检测方法
            threshold: 异常阈值
            window_size: 移动平均窗口

        Returns:
            异常检测结果
        """
        if not data or not value_column:
            return {"anomalies": [], "summary": {"error": "数据或数值列为空"}, "risk_level": "unknown"}

        # 自动检测日期列
        if not date_column:
            all_columns = list(data[0].keys())
            for col in all_columns:
                if col.lower() in ("date", "日期", "create_date", "time", "时间", "day", "dt"):
                    date_column = col
                    break

        # 提取数值序列
        series = self._extract_series(data, date_column, value_column)
        if len(series) < 4:
            return {"anomalies": [], "summary": {"error": "数据点数不足（至少需要 4 个）"}, "risk_level": "unknown"}

        values = [s["value"] for s in series]

        # 执行检测
        if method == "iqr":
            anomalies = self._detect_iqr(values, threshold)
        elif method == "mad":
            anomalies = self._detect_mad(values, threshold)
        else:  # zscore
            anomalies = self._detect_zscore(values, threshold)

        # 装配异常数据
        anomaly_points = []
        for idx in anomalies:
            point = dict(series[idx])
            point["anomaly_score"] = round(self._anomaly_score(values, idx, method), 4)
            point["risk"] = self._classify_risk(point["anomaly_score"])

            # 维度溯源
            if dimension_columns and idx < len(data):
                point["dimensions"] = {
                    col: data[idx].get(col, "未知")
                    for col in dimension_columns if col in data[idx]
                }
            anomaly_points.append(point)

        # 总体概况
        summary = self._compute_summary(series, anomaly_points, method)

        # 维度洞察
        dimension_insights = []
        if dimension_columns:
            dimension_insights = self._analyze_dimensions(data, anomaly_points, dimension_columns, value_column)

        return {
            "anomalies": anomaly_points,
            "summary": summary,
            "dimension_insights": dimension_insights,
            "risk_level": summary.get("risk_level", "low"),
        }

    # ── 序列处理 ──

    @staticmethod
    def _extract_series(data: List[Dict], date_col: Optional[str], value_col: str) -> List[Dict]:
        """提取时间序列"""
        series = []
        for row in data:
            val = row.get(value_col)
            if val is not None and isinstance(val, (int, float)):
                entry = {"index": len(series), "value": val}
                if date_col and date_col in row:
                    entry["date"] = str(row[date_col])
                series.append(entry)
        return series

    # ── 检测方法 ──

    @staticmethod
    def _detect_zscore(values: List[float], threshold: float = 3.0) -> List[int]:
        """Z-Score 异常检测"""
        n = len(values)
        if n < 3:
            return []
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if n > 1 else 0
        if stdev == 0:
            return []
        return [i for i, v in enumerate(values) if abs(v - mean) / stdev > threshold]

    @staticmethod
    def _detect_iqr(values: List[float], multiplier: float = 1.5) -> List[int]:
        """IQR 异常检测"""
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        return [i for i, v in enumerate(values) if v < lower or v > upper]

    @staticmethod
    def _detect_mad(values: List[float], threshold: float = 3.0) -> List[int]:
        """MAD（Median Absolute Deviation）异常检测"""
        median = statistics.median(values)
        deviations = [abs(v - median) for v in values]
        mad = statistics.median(deviations)
        if mad == 0:
            mad = statistics.mean(deviations)
        if mad == 0:
            return []
        modified_z_scores = [0.6745 * (v - median) / mad for v in values]
        return [i for i, z in enumerate(modified_z_scores) if abs(z) > threshold]

    # ── 评分与分类 ──

    def _anomaly_score(self, values: List[float], idx: int, method: str) -> float:
        """计算异常分数（越大越异常）"""
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 1
        if method == "iqr":
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            q1 = sorted_vals[n // 4]
            q3 = sorted_vals[3 * n // 4]
            iqr = q3 - q1
            return abs(values[idx] - mean) / (iqr if iqr > 0 else stdev)
        else:
            return abs(values[idx] - mean) / (stdev if stdev > 0 else 1)

    def _classify_risk(self, score: float) -> str:
        """划分风险等级"""
        if score < 2:
            return "low"
        elif score < 3:
            return "medium"
        elif score < 4:
            return "high"
        return "critical"

    # ── 汇总分析 ──

    def _compute_summary(self, series: List[Dict], anomalies: List[Dict], method: str) -> Dict[str, Any]:
        """计算异常概况"""
        n = len(series)
        anomaly_count = len(anomalies)
        anomaly_ratio = round(anomaly_count / n * 100, 2) if n > 0 else 0

        # 整体风险等级
        if anomaly_count == 0:
            risk_level = "low"
        else:
            max_score = max(a.get("anomaly_score", 0) for a in anomalies)
            risk_level = self._classify_risk(max_score)

        # 均值与标准差
        values = [s["value"] for s in series]
        mean_val = statistics.mean(values)
        stdev_val = statistics.stdev(values) if len(values) > 1 else 0

        return {
            "total_points": n,
            "anomaly_count": anomaly_count,
            "anomaly_ratio": anomaly_ratio,
            "mean": round(mean_val, 4),
            "std_dev": round(stdev_val, 4),
            "method": method,
            "risk_level": risk_level,
            "max_anomaly_score": max((a.get("anomaly_score", 0) for a in anomalies), default=0),
        }

    def _analyze_dimensions(
        self, data: List[Dict], anomalies: List[Dict], dim_cols: List[str], value_col: str
    ) -> List[Dict]:
        """分析异常维度分布"""
        total_by_dim = defaultdict(float)
        anomaly_by_dim = defaultdict(float)

        for row in data:
            val = row.get(value_col, 0) or 0
            for col in dim_cols:
                dim_val = str(row.get(col, "未知"))
                total_by_dim[f"{col}={dim_val}"] += val

        for a in anomalies:
            dims = a.get("dimensions", {})
            for col, val in dims.items():
                anomaly_by_dim[f"{col}={val}"] += a.get("value", 0)

        insights = []
        for key, total in sorted(total_by_dim.items(), key=lambda x: x[1], reverse=True):
            anomaly_total = anomaly_by_dim.get(key, 0)
            if total > 0 and anomaly_total > 0:
                impact_ratio = round(anomaly_total / total * 100, 2)
                insights.append({
                    "dimension": key,
                    "total_value": round(total, 2),
                    "anomaly_value": round(anomaly_total, 2),
                    "impact_ratio": impact_ratio,
                    "severity": "critical" if impact_ratio > 50 else "high" if impact_ratio > 30 else "medium",
                })

        return sorted(insights, key=lambda x: x["impact_ratio"], reverse=True)


import logging
