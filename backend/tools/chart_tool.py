"""ECharts 可视化工具：后端自动匹配图表类型，输出图表配置 JSON"""

import json
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool


class ChartTool(BaseTool):
    """ECharts 可视化引擎：根据数据分布自动匹配最佳图表类型"""

    CHART_TYPES = {
        "line": "折线图 - 适合展示趋势变化",
        "bar": "柱状图 - 适合展示分类对比",
        "pie": "饼图 - 适合展示占比分布",
        "heatmap": "热力图 - 适合展示密度分布",
        "scatter": "散点图 - 适合展示相关性"
    }

    def __init__(self):
        super().__init__(
            name="chart_generator",
            description="根据数据自动生成 ECharts 图表配置"
        )

    def validate(self, **kwargs) -> bool:
        return "data" in kwargs and "columns" in kwargs

    def execute(self, data: List[Dict], columns: List[str],
                chart_type: Optional[str] = None, title: str = "",
                x_axis: Optional[str] = None,
                y_axis: Optional[str] = None) -> Dict[str, Any]:
        """生成 ECharts 图表配置

        Args:
            data: 数据列表
            columns: 列名列表
            chart_type: 图表类型（自动检测 None）
            title: 图表标题
            x_axis: X轴字段
            y_axis: Y轴字段（多个逗号分隔）

        Returns:
            ECharts 配置字典
        """
        if not data:
            return {"error": "无数据可绘图"}

        if not chart_type:
            chart_type = self._auto_detect_chart_type(data, columns)

        if not x_axis:
            x_axis = columns[0] if columns else ""
        if not y_axis:
            y_axis = columns[1] if len(columns) > 1 else columns[0]

        # 提取数据
        x_data = [str(row.get(x_axis, "")) for row in data]

        y_fields = [f.strip() for f in y_axis.split(",")] if y_axis else []
        series = []
        for field in y_fields:
            y_values = []
            for row in data:
                val = row.get(field, 0)
                try:
                    y_values.append(float(val) if val else 0)
                except (ValueError, TypeError):
                    y_values.append(0)
            series.append({
                "name": field,
                "type": chart_type if chart_type != "pie" else "pie",
                "data": y_values if chart_type != "pie" else
                        [{"name": x_data[i], "value": y_values[i]} for i in range(len(x_data))]
            })

        option = {
            "title": {"text": title, "left": "center"},
            "tooltip": {"trigger": "axis" if chart_type != "pie" else "item"},
            "legend": {"data": y_fields, "bottom": 10},
            "xAxis": {"type": "category", "data": x_data} if chart_type != "pie" else {},
            "yAxis": {"type": "value"} if chart_type != "pie" else {},
            "series": series
        }

        if chart_type == "pie":
            option["series"] = [{
                "type": "pie",
                "radius": "50%",
                "data": [{"name": x_data[i], "value": series[0]["data"][i]["value"] if isinstance(series[0]["data"][i], dict) else series[0]["data"][i]} for i in range(len(x_data))],
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }]

        return {
            "chart_type": chart_type,
            "option": option,
            "title": title
        }

    def _auto_detect_chart_type(self, data: List[Dict], columns: List[str]) -> str:
        """自动检测最佳图表类型"""
        if len(data) <= 1:
            return "pie"

        # 检测是否有时间序列字段
        time_keywords = ["日期", "时间", "月", "年", "date", "time", "month", "year"]
        for col in columns:
            if any(kw in col.lower() for kw in time_keywords):
                return "line"

        # 检测类别数量
        if len(data) <= 8:
            return "bar"

        return "line"

    def get_parameters(self) -> Dict:
        return {
            "data": {"type": "array", "description": "数据列表", "required": True},
            "columns": {"type": "array", "description": "列名", "required": True},
            "chart_type": {"type": "string", "description": "图表类型", "required": False},
            "title": {"type": "string", "description": "图表标题", "required": False}
        }
