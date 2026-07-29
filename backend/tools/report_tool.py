import markdown
from datetime import datetime
from typing import Optional, List, Dict, Any
import os
from tools.base_tool import BaseTool


class ReportTool(BaseTool):
    """智能报告生成工具：产出结构化 Markdown 分析报告，支持导出"""

    def __init__(self):
        super().__init__(
            name="report_generator",
            description="生成结构化数据分析报告，支持 Markdown 格式"
        )

    def validate(self, **kwargs) -> bool:
        required = ["title", "summary", "conclusions"]
        return all(k in kwargs for k in required)

    def execute(self, title: str, summary: str, conclusions: List[str],
                data_tables: Optional[List[Dict]] = None,
                charts: Optional[List[str]] = None,
                recommendations: Optional[List[str]] = None,
                metrics: Optional[Dict] = None,
                report_type: str = "analysis") -> Dict[str, Any]:
        """生成结构化分析报告"""
        sections = []
        sections.append(f"# {title}")
        sections.append("")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"> 生成时间: {now_str}")
        sections.append(f"> 报告类型: {report_type}")
        sections.append("")

        sections.append("## 1. 摘要")
        sections.append("")
        sections.append(f"{summary}")
        sections.append("")

        if metrics:
            sections.append("## 2. 关键指标")
            sections.append("")
            sections.append("| 指标 | 数值 |")
            sections.append("|------|------|")
            for k, v in metrics.items():
                sections.append(f"| {k} | {v} |")
            sections.append("")

        if data_tables:
            sections.append("## 3. 数据详情")
            sections.append("")
            for i, table in enumerate(data_tables, 1):
                tbl_name = table.get("name", "")
                sections.append(f"### 表{i}: {tbl_name}")
                if table.get("headers") and table.get("rows"):
                    sections.append("|" + "|".join(table["headers"]) + "|")
                    sections.append("|" + "|".join(["---"] * len(table["headers"])) + "|")
                    for row in table["rows"]:
                        sections.append("|" + "|".join(str(c) for c in row) + "|")
                sections.append("")

        if charts:
            sections.append("## 4. 可视化图表")
            sections.append("")
            for i, chart_desc in enumerate(charts, 1):
                sections.append(f"- 图表{i}: {chart_desc}")
            sections.append("")

        sections.append("## 5. 分析结论")
        sections.append("")
        for i, conclusion in enumerate(conclusions, 1):
            sections.append(f"{i}. {conclusion}")
        sections.append("")

        if recommendations:
            sections.append("## 6. 业务建议")
            sections.append("")
            for i, rec in enumerate(recommendations, 1):
                sections.append(f"{i}. {rec}")
            sections.append("")

        sections.append("---")
        sections.append("*报告由 DataAnalysis-Agent-LLM 自动生成*")

        markdown_content = "\n".join(sections)

        return {
            "markdown_content": markdown_content,
            "title": title,
            "generated_at": datetime.now().isoformat()
        }

    def get_parameters(self) -> Dict:
        return {
            "title": {"type": "string", "description": "报告标题", "required": True},
            "summary": {"type": "string", "description": "报告摘要", "required": True},
            "conclusions": {"type": "array", "description": "分析结论列表", "required": True}
        }
