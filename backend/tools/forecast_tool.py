"""
ForecastTool —— 预测工具

基于 Statsmodels 的本地预测算法，无需付费模型依赖。
支持：
- 短期销量 / 用户量 / 流水预测
- Simple Moving Average（简单移动平均）
- Exponential Smoothing（指数平滑）
- Linear Regression Trend（线性回归趋势）

注意：statsmodels 为可选依赖。若未安装，使用纯 Python 实现降级。
"""

import math
from typing import Any, Dict, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# 尝试导入 statsmodels
try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.info("statsmodels 未安装，使用内置算法进行预测。")


class ForecastTool(BaseTool):
    """预测工具

    基于统计学的短期预测能力，适用于销量、用户量、流水等 KPI 预测。

    参数：
        data (list):       历史数据列表（字典列表）
        value_column (str): 数值列名（预测目标）
        date_column (str):  日期列名（可选，用于排序）
        periods (int):      预测期数（默认 7）
        method (str):       预测方法：sma / exponential / linear / auto
        window (int):       滑动窗口大小（SMA / 指数平滑适用，默认 7）
        confidence_level (float): 置信区间（默认 0.95）

    返回：
        dict: {
            "forecast": [...],         预测结果
            "history": [...],          历史数据
            "metrics": {...},          模型评估指标
            "summary": str,            预测摘要
        }
    """

    def __init__(self):
        super().__init__(
            name="forecast_tool",
            description="预测工具，支持移动平均/指数平滑/趋势回归等本地预测算法",
        )
        self._parameters = {
            "type": "object",
            "properties": {
                "data": {"type": "array", "description": "历史数据"},
                "value_column": {"type": "string", "description": "数值列名"},
                "date_column": {"type": "string", "description": "日期列名"},
                "periods": {"type": "integer", "description": "预测期数，默认 7"},
                "method": {
                    "type": "string",
                    "enum": ["sma", "exponential", "linear", "auto"],
                    "description": "预测方法",
                },
                "window": {"type": "integer", "description": "滑动窗口大小，默认 7"},
            },
            "required": ["data", "value_column"],
        }

    def execute(
        self,
        data: List[Dict[str, Any]],
        value_column: Optional[str] = None,
        date_column: Optional[str] = None,
        periods: int = 7,
        method: str = "auto",
        window: int = 7,
        confidence_level: float = 0.95,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """执行预测

        Args:
            data: 历史数据
            value_column: 数值列
            date_column: 日期列
            periods: 预测期数
            method: 预测方法
            window: 窗口大小
            confidence_level: 置信区间

        Returns:
            预测结果字典
        """
        if not data or not value_column:
            return {"forecast": [], "history": [], "metrics": {}, "summary": "数据为空"}

        # 提取历史值
        if date_column:
            sorted_data = sorted(data, key=lambda x: str(x.get(date_column, "")))
        else:
            sorted_data = data

        history = []
        for row in sorted_data:
            val = row.get(value_column)
            if val is not None and isinstance(val, (int, float)):
                history.append(val)

        if len(history) < 3:
            return {
                "forecast": [],
                "history": [{"index": i, "value": v, "type": "actual"} for i, v in enumerate(history)],
                "metrics": {"error": "历史数据不足（至少需要 3 个数据点）"},
                "summary": f"历史数据不足，无法进行预测（仅 {len(history)} 个数据点）",
            }

        # 选择方法
        if method == "auto":
            method = self._auto_select(history)

        # 执行预测
        if method == "sma":
            forecast_values = self._sma_forecast(history, periods, window)
        elif method == "exponential":
            forecast_values = self._exponential_smoothing(history, periods, window)
        elif method == "linear":
            forecast_values, slope, intercept = self._linear_trend(history, periods)
        elif STATSMODELS_AVAILABLE and method == "statsmodels_arima":
            forecast_values = self._arima_forecast(history, periods)
        else:
            forecast_values = self._sma_forecast(history, periods, window)

        # 计算预测区间
        residuals = self._compute_residuals(history)
        stdev_residuals = statistics.stdev(residuals) if len(residuals) > 1 else 1

        # 装配结果
        last_date = ""
        if date_column:
            last_date = str(sorted_data[-1].get(date_column, ""))

        forecast_result = []
        for i, fv in enumerate(forecast_values):
            margin = 1.96 * stdev_residuals * (1 + i * 0.05)  # 预测越远，区间越大
            forecast_result.append({
                "period": i + 1,
                "date": self._future_date(last_date, i + 1) if last_date else f"T+{i+1}",
                "value": round(fv, 4),
                "lower_bound": round(fv - margin, 4),
                "upper_bound": round(fv + margin, 4),
                "type": "forecast",
            })

        history_result = [
            {"index": i, "value": v, "type": "actual", "label": f"T-{len(history)-i}"}
            for i, v in enumerate(history)
        ]

        # 模型评估
        fitted = self._fitted_values(history, method, window)
        metrics = self._evaluate(history, fitted)

        # 摘要
        last_actual = history[-1]
        first_forecast = forecast_result[0]["value"] if forecast_result else 0
        change_pct = ((first_forecast - last_actual) / abs(last_actual) * 100) if last_actual != 0 else 0

        summary = (
            f"基于 {len(history)} 个历史数据点，使用 {method.upper()} 方法预测未来 {periods} 期。"
            f"下期预测值为 {first_forecast:.2f}，较当前值变化 {change_pct:+.2f}%。"
            f"模型拟合 R²={metrics.get('r2', 0):.4f}，RMSE={metrics.get('rmse', 0):.4f}。"
        )

        return {
            "forecast": forecast_result,
            "history": history_result,
            "metrics": metrics,
            "summary": summary,
            "method": method,
        }

    # ── 预测方法 ──

    @staticmethod
    def _auto_select(history: List[float]) -> str:
        """自动选择最佳预测方法"""
        n = len(history)
        if n < 10:
            return "sma"
        # 简单趋势检测
        if n > 5:
            first_half = statistics.mean(history[: n // 2])
            second_half = statistics.mean(history[n // 2:])
            if abs(second_half - first_half) / (abs(first_half) + 0.001) > 0.1:
                return "linear"
        return "exponential"

    @staticmethod
    def _sma_forecast(history: List[float], periods: int, window: int) -> List[float]:
        """简单移动平均预测"""
        window = min(window, len(history))
        recent_values = history[-window:]
        forecast = [statistics.mean(recent_values)] * periods
        return forecast

    @staticmethod
    def _exponential_smoothing(history: List[float], periods: int, window: int) -> List[float]:
        """指数平滑预测"""
        alpha = 2.0 / (window + 1)  # 自适应平滑系数
        smoothed = history[0]

        for v in history[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed

        forecast = [smoothed] * periods
        return forecast

    @staticmethod
    def _linear_trend(history: List[float], periods: int) -> tuple:
        """线性回归趋势预测"""
        n = len(history)
        x = list(range(n))
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(history)

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, history))
        denominator = sum((xi - mean_x) ** 2 for xi in x)

        slope = numerator / denominator if denominator != 0 else 0
        intercept = mean_y - slope * mean_x

        forecast = [slope * (n + i) + intercept for i in range(periods)]
        return forecast, slope, intercept

    def _arima_forecast(self, history: List[float], periods: int) -> List[float]:
        """ARIMA 预测（需要 statsmodels）"""
        if not STATSMODELS_AVAILABLE:
            return self._sma_forecast(history, periods, 7)

        try:
            model = sm.tsa.ARIMA(history, order=(1, 1, 1))
            fitted = model.fit()
            forecast = fitted.forecast(steps=periods)
            return forecast.tolist()
        except Exception as e:
            logger.warning(f"ARIMA 预测失败: {e}, 降级到 SMA。")
            return self._sma_forecast(history, periods, 7)

    # ── 评估与辅助 ──

    def _fitted_values(self, history: List[float], method: str, window: int) -> List[Optional[float]]:
        """获取历史拟合值"""
        if method == "sma":
            fitted = []
            for i in range(len(history)):
                if i < window:
                    fitted.append(None)
                else:
                    fitted.append(statistics.mean(history[i - window:i]))
            return fitted
        elif method == "exponential" or method == "linear":
            alpha = 2.0 / (window + 1)
            fitted = [history[0]]
            for v in history[1:]:
                fitted.append(alpha * v + (1 - alpha) * fitted[-1])
            return fitted
        return [None] * len(history)

    @staticmethod
    def _compute_residuals(history: List[float]) -> List[float]:
        """计算残差"""
        if len(history) < 2:
            return [0]
        mean = statistics.mean(history)
        return [v - mean for v in history]

    @staticmethod
    def _evaluate(history: List[float], fitted: List[Optional[float]]) -> Dict[str, float]:
        """评估模型精度"""
        valid_pairs = [(h, f) for h, f in zip(history, fitted) if f is not None]
        if len(valid_pairs) < 3:
            return {"rmse": 0, "mae": 0, "mape": 0, "r2": 0}

        errors = [h - f for h, f in valid_pairs]
        mse = sum(e ** 2 for e in errors) / len(errors)
        rmse = math.sqrt(mse)
        mae = sum(abs(e) for e in errors) / len(errors)
        mape = sum(abs(e) / abs(h) * 100 for h, e in zip([h for h, _ in valid_pairs], errors) if h != 0) / len(errors)

        # R²
        mean_actual = statistics.mean([h for h, _ in valid_pairs])
        ss_res = sum(e ** 2 for e in errors)
        ss_tot = sum((h - mean_actual) ** 2 for h, _ in valid_pairs)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0

        return {
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "mape": round(mape, 4),
            "r2": round(r2, 4),
        }

    @staticmethod
    def _future_date(last_date: str, offset: int) -> str:
        """计算未来日期字符串"""
        try:
            from datetime import datetime, timedelta
            dt = datetime.strptime(last_date, "%Y-%m-%d") if "-" in last_date else datetime.now()
            future = dt + timedelta(days=offset)
            return future.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return f"T+{offset}"


import statistics
import logging
