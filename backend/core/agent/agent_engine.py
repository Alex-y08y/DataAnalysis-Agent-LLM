"""
DataAnalysis-Agent-LLM Agent 引擎

DataAnalysisAgent 类 —— 基于 LangGraph 的多轮反思工作流（ReAct 模式）。
支持：
- 多轮反思工作流，自动拆解复杂分析需求
- 编排工具调用顺序
- 循环校验数据结果
- 状态管理（AgentState）
- 记忆管理：短期对话上下文 + 长期历史任务持久化
"""

import json
import logging
import hashlib
import datetime
from typing import Any, Dict, List, Optional, TypedDict, Annotated, Sequence
from enum import Enum

# 如果生产环境缺少 langgraph / langchain 包，此处设计为可降级运行
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("langgraph 未安装，Agent 引擎将运行在模拟模式。")

try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("langchain 未安装，Agent 引擎将运行在模拟模式。")


logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. 状态定义
# ──────────────────────────────────────────────

class IntentType(str, Enum):
    """分析意图枚举"""
    FETCH = "fetch"          # 取数 / 查询
    COMPARE = "compare"      # 对比分析
    ANOMALY = "anomaly"      # 异常检测
    FORECAST = "forecast"    # 预测
    REPORT = "report"        # 报告生成
    GENERAL = "general"      # 通用问答


class ToolCallRecord(TypedDict):
    """单次工具调用记录"""
    tool_name: str
    input: Dict[str, Any]
    output: Any
    status: str       # success / error
    timestamp: str


class AgentState(TypedDict):
    """Agent 全局状态

    字段说明：
        messages:         对话消息历史（LangChain message 列表）
        user_input:       用户当前输入原文
        intent:           分析意图（枚举）
        sub_goals:        子任务列表
        current_step:     当前执行步骤索引
        sql_query:        生成的 SQL 语句
        sql_results:      SQL 查询结果
        tool_results:     工具执行结果列表
        verified:         是否通过校验
        final_response:   最终回答文本
        short_term_memory: 短期对话上下文（保留最近 N 轮）
        long_term_memory:  长期任务持久化存储
        errors:           执行过程中的错误信息列表
    """
    messages: Annotated[Sequence[BaseMessage], "对话消息历史"]
    user_input: str
    intent: Optional[str]
    sub_goals: List[str]
    current_step: int
    sql_query: Optional[str]
    sql_results: Optional[List[Dict[str, Any]]]
    tool_results: List[ToolCallRecord]
    verified: bool
    final_response: Optional[str]
    short_term_memory: List[Dict[str, Any]]
    long_term_memory: List[Dict[str, Any]]
    errors: List[str]


def create_initial_state(user_input: str, messages: Optional[List[BaseMessage]] = None) -> AgentState:
    """创建初始 AgentState"""
    return AgentState(
        messages=messages or [],
        user_input=user_input,
        intent=None,
        sub_goals=[],
        current_step=0,
        sql_query=None,
        sql_results=None,
        tool_results=[],
        verified=False,
        final_response=None,
        short_term_memory=[],
        long_term_memory=[],
        errors=[],
    )


# ──────────────────────────────────────────────
# 2. 短期 / 长期记忆管理
# ──────────────────────────────────────────────

class MemoryManager:
    """记忆管理器

    短期记忆：保留最近 N 轮对话摘要
    长期记忆：将已完成任务持久化到本地 JSON 文件
    """

    def __init__(self, short_term_window: int = 10, memory_file: Optional[str] = None):
        self.short_term_window = short_term_window
        self.memory_file = memory_file  # 如提供路径，长期记忆会持久化

    def update_short_term(self, state: AgentState, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """更新短期记忆（FIFO 窗口）"""
        memory = state.get("short_term_memory", [])
        memory.append(entry)
        if len(memory) > self.short_term_window:
            memory = memory[-self.short_term_window:]
        return memory

    def archive_to_long_term(self, state: AgentState) -> List[Dict[str, Any]]:
        """将当前任务归档到长期记忆"""
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_input": state["user_input"],
            "intent": state["intent"],
            "sub_goals": state["sub_goals"],
            "sql_query": state["sql_query"],
            "tool_calls": len(state["tool_results"]),
            "final_response": state["final_response"],
            "task_hash": self._compute_hash(state["user_input"]),
        }
        long_term = state.get("long_term_memory", [])
        # 去重：相同 hash 不重复存储
        if not any(r.get("task_hash") == record["task_hash"] for r in long_term):
            long_term.append(record)
        # 持久化
        if self.memory_file:
            self._persist(long_term)
        return long_term

    def recall_similar(self, state: AgentState, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """基于简单哈希召回相似历史任务（生产环境可替换为向量检索）"""
        query_hash = self._compute_hash(query)
        long_term = state.get("long_term_memory", [])
        # 简单前缀匹配
        matched = [r for r in long_term if query_hash[:8] == r.get("task_hash", "")[:8]]
        return matched[:top_k]

    @staticmethod
    def _compute_hash(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _persist(self, records: List[Dict[str, Any]]) -> None:
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"长期记忆持久化失败: {e}")


# ──────────────────────────────────────────────
# 3. Agent 引擎
# ──────────────────────────────────────────────

class DataAnalysisAgent:
    """数据分析 Agent 主引擎

    基于 LangGraph 的工作流编排：
      analyze_intent → retrieve_knowledge → generate_sql → execute_tools
      → verify_results → generate_response

    使用示例：
        agent = DataAnalysisAgent()
        result = agent.run("上月销售额与去年同期对比如何？")
        print(result["final_response"])
    """

    def __init__(
        self,
        llm=None,
        tools: Optional[List[Any]] = None,
        memory_file: Optional[str] = None,
        max_iterations: int = 5,
        max_retries: int = 3,
    ):
        """
        初始化 Agent

        Args:
            llm: LLM 实例（如 OpenAI / ChatGLM 等），若为 None 则使用模拟模式
            tools: 可用工具列表，每个工具需实现 name / execute 接口
            memory_file: 长期记忆持久化文件路径
            max_iterations: 最大工作流迭代轮数
            max_retries: 每个节点的最大重试次数
        """
        self.llm = llm
        self.tools = {t.name: t for t in (tools or [])}
        self.memory_manager = MemoryManager(memory_file=memory_file)
        self.max_iterations = max_iterations
        self.max_retries = max_retries
        self._build_graph()

    # ── 工作流构建 ──

    def _build_graph(self) -> None:
        """构建 LangGraph 状态图"""
        if not LANGGRAPH_AVAILABLE:
            logger.info("LangGraph 不可用，跳过图构建。将使用顺序执行模式。")
            return

        workflow = StateGraph(AgentState)

        # 注册节点
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("retrieve_knowledge", self.retrieve_knowledge)
        workflow.add_node("generate_sql", self.generate_sql)
        workflow.add_node("execute_tools", self.execute_tools)
        workflow.add_node("verify_results", self.verify_results)
        workflow.add_node("generate_response", self.generate_response)

        # 设置入口
        workflow.set_entry_point("analyze_intent")

        # 条件边：根据意图决定是否需要知识检索
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_after_intent,
            {
                "retrieve_knowledge": "retrieve_knowledge",
                "generate_sql": "generate_sql",
                "execute_tools": "execute_tools",
                "generate_response": "generate_response",
            },
        )

        # 知识检索后进入 SQL 生成
        workflow.add_edge("retrieve_knowledge", "generate_sql")

        # SQL 生成后执行工具
        workflow.add_edge("generate_sql", "execute_tools")

        # 校验：通过则生成回答，否则重新执行（最多 max_iterations 次）
        workflow.add_conditional_edges(
            "execute_tools",
            self._route_after_tools,
            {
                "verify_results": "verify_results",
                "execute_tools": "execute_tools",  # 重试
            },
        )

        workflow.add_conditional_edges(
            "verify_results",
            self._route_after_verify,
            {
                "generate_response": "generate_response",
                "execute_tools": "execute_tools",  # 重试
                "analyze_intent": "analyze_intent",  # 重新分析
            },
        )

        workflow.add_edge("generate_response", END)

        # 编译
        self.graph = workflow.compile(checkpointer=MemorySaver())

    def _route_after_intent(self, state: AgentState) -> str:
        """根据意图路由"""
        intent = state.get("intent")
        if intent in (IntentType.REPORT, IntentType.FORECAST):
            return "retrieve_knowledge"
        elif intent in (IntentType.FETCH, IntentType.COMPARE):
            return "generate_sql"
        elif intent == IntentType.ANOMALY:
            return "execute_tools"
        return "generate_response"

    def _route_after_tools(self, state: AgentState) -> str:
        """工具执行后路由"""
        if state["current_step"] >= self.max_iterations:
            return "verify_results"
        # 如果工具调用有错误，需要校验
        return "verify_results"

    def _route_after_verify(self, state: AgentState) -> str:
        """校验后路由"""
        if state.get("verified"):
            return "generate_response"
        if state["current_step"] < self.max_iterations:
            state["current_step"] += 1
            return "execute_tools"
        return "generate_response"

    # ── 核心节点 ──

    def analyze_intent(self, state: AgentState) -> Dict[str, Any]:
        """分析用户意图

        基于用户输入判断分析类型：
        - fetch（取数）："查询近7天注册用户"
        - compare（对比）："对比A款和B款转化率"
        - anomaly（异常检测）："检测昨日UV异常下跌原因"
        - forecast（预测）："预测Q3季度销售额"
        - report（报告）："生成本周运营周报"

        Args:
            state: 当前 Agent 状态

        Returns:
            更新后的状态片段
        """
        user_input = state.get("user_input", "")
        updates: Dict[str, Any] = {
            "sub_goals": [],
            "errors": [],
        }

        # 关键词匹配 + 拆解子任务
        intent = IntentType.GENERAL
        sub_goals = []

        input_lower = user_input.lower()

        # 意图识别规则
        if any(kw in input_lower for kw in ["预测", "forecast", "趋势", "未来"]):
            intent = IntentType.FORECAST
            sub_goals = ["提取历史数据", "选择预测模型", "生成预测结果", "校验预测精度"]
        elif any(kw in input_lower for kw in ["异常", "波动", "下跌", "上涨", "anomaly", "突变"]):
            intent = IntentType.ANOMALY
            sub_goals = ["提取指标序列", "检测异常点", "溯源异常维度", "评估影响范围"]
        elif any(kw in input_lower for kw in ["对比", "比较", "同比", "环比", "vs", "versus"]):
            intent = IntentType.COMPARE
            sub_goals = ["确定对比维度", "提取对比数据", "计算差异", "生成对比结论"]
        elif any(kw in input_lower for kw in ["报告", "周报", "月报", "report", "总结"]):
            intent = IntentType.REPORT
            sub_goals = ["确定报告范围", "提取关键指标", "生成报告草稿", "格式化输出"]
        elif any(kw in input_lower for kw in ["查询", "取数", "多少", "列出", "fetch", "query"]):
            intent = IntentType.FETCH
            sub_goals = ["解析查询条件", "生成 SQL", "执行查询", "格式化结果"]

        updates["intent"] = intent.value
        updates["sub_goals"] = sub_goals

        # 记录短期记忆
        updated_memory = self.memory_manager.update_short_term(
            state,
            {"role": "intent", "content": intent.value, "timestamp": datetime.datetime.now().isoformat()},
        )
        updates["short_term_memory"] = updated_memory

        logger.info(f"分析意图: {intent.value}, 子目标: {sub_goals}")
        return updates

    def retrieve_knowledge(self, state: AgentState) -> Dict[str, Any]:
        """检索知识库（RAG）

        若配置了知识库检索接口，调用 RAG 获取相关领域知识辅助分析；
        否则返回默认知识提示。

        Args:
            state: 当前 Agent 状态

        Returns:
            更新后的状态片段
        """
        intent = state.get("intent", "general")
        user_input = state.get("user_input", "")

        knowledge = {
            "intent": intent,
            "context": f"用户需求: {user_input}",
            "domain_hints": [],
        }

        # 模拟知识检索（生产环境接入向量数据库）
        if intent == IntentType.FORECAST.value:
            knowledge["domain_hints"] = [
                "短期预测建议使用 ARIMA 或 Holt-Winters 模型",
                "至少需要 30 个历史数据点",
                "建议剔除节假日效应",
            ]
        elif intent == IntentType.ANOMALY.value:
            knowledge["domain_hints"] = [
                "异常检测建议使用 3-Sigma 或 IQR 方法",
                "需排除周期性波动的影响",
                "度量为当日值与移动均值的偏差比例",
            ]
        elif intent == IntentType.COMPARE.value:
            knowledge["domain_hints"] = [
                "同比：与去年同期比较",
                "环比：与上期（上月/上周）比较",
                "建议同时展示绝对值与增长率",
            ]

        # 回忆长期记忆中的相似任务
        similar_tasks = self.memory_manager.recall_similar(state, user_input)
        updates = {
            "long_term_memory": similar_tasks,
        }

        logger.info(f"知识检索完成，获取到 {len(knowledge['domain_hints'])} 条领域提示")
        return updates

    def generate_sql(self, state: AgentState) -> Dict[str, Any]:
        """生成 SQL 查询

        根据用户意图和已有上下文生成 SQL 语句。
        在无 LLM 时使用模板匹配生成。

        Args:
            state: 当前 Agent 状态

        Returns:
            更新后的状态片段
        """
        intent = state.get("intent", "")
        user_input = state.get("user_input", "")

        sql_query = None

        # 模拟 SQL 生成（生产环境通过 LLM 生成）
        if intent == IntentType.FETCH.value:
            sql_query = "-- 自动生成查询 SQL\nSELECT * FROM business_table WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) LIMIT 100;"
        elif intent == IntentType.COMPARE.value:
            sql_query = "-- 对比分析 SQL\nSELECT \n    DATE_FORMAT(create_date, '%%Y-%%m') AS period,\n    SUM(CASE WHEN product_type = 'A' THEN amount ELSE 0 END) AS product_a,\n    SUM(CASE WHEN product_type = 'B' THEN amount ELSE 0 END) AS product_b\nFROM business_table\nWHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)\nGROUP BY period\nORDER BY period;"
        elif intent == IntentType.ANOMALY.value:
            sql_query = "-- 异常检测 SQL\nSELECT \n    create_date,\n    uv,\n    AVG(uv) OVER (ORDER BY create_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d\nFROM daily_stats\nWHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)\nORDER BY create_date;"

        updates = {"sql_query": sql_query}
        logger.info(f"SQL 生成完成: {sql_query[:80] if sql_query else '无 SQL'}")
        return updates

    def execute_tools(self, state: AgentState) -> Dict[str, Any]:
        """编排工具调用

        根据当前意图和子目标按顺序调用已注册的工具。
        每个工具调用都会记录执行状态。

        Args:
            state: 当前 Agent 状态

        Returns:
            更新后的状态片段
        """
        intent = state.get("intent", "")
        sub_goals = state.get("sub_goals", [])
        tool_results: List[ToolCallRecord] = list(state.get("tool_results", []))
        errors: List[str] = list(state.get("errors", []))

        # 如果没有工具注册，模拟执行结果
        if not self.tools:
            logger.info("无可用工具，使用模拟数据。")
            mock_result = ToolCallRecord(
                tool_name="mock_executor",
                input={"intent": intent},
                output={"message": f"模拟执行 {intent} 分析完成"},
                status="success",
                timestamp=datetime.datetime.now().isoformat(),
            )
            tool_results.append(mock_result)
        else:
            # 按子目标依次执行对应工具
            tool_order = self._plan_tool_sequence(intent)
            for tool_name in tool_order:
                tool = self.tools.get(tool_name)
                if not tool:
                    continue
                try:
                    tool_input = self._prepare_tool_input(tool_name, state)
                    for attempt in range(self.max_retries):
                        try:
                            output = tool.execute(**tool_input)
                            record = ToolCallRecord(
                                tool_name=tool_name,
                                input=tool_input,
                                output=output,
                                status="success",
                                timestamp=datetime.datetime.now().isoformat(),
                            )
                            tool_results.append(record)
                            logger.info(f"工具 {tool_name} 执行成功")
                            break
                        except Exception as e:
                            if attempt == self.max_retries - 1:
                                raise
                            logger.warning(f"工具 {tool_name} 第 {attempt+1} 次重试")
                except Exception as e:
                    err_msg = f"工具 {tool_name} 执行失败: {str(e)}"
                    errors.append(err_msg)
                    record = ToolCallRecord(
                        tool_name=tool_name,
                        input={"error": err_msg},
                        output=None,
                        status="error",
                        timestamp=datetime.datetime.now().isoformat(),
                    )
                    tool_results.append(record)
                    logger.error(err_msg)

        updates = {
            "tool_results": tool_results,
            "errors": errors,
        }
        return updates

    def _plan_tool_sequence(self, intent: str) -> List[str]:
        """规划工具调用顺序"""
        sequence = []
        if intent == IntentType.FETCH.value:
            sequence = ["sql_tool", "clean_tool"]
        elif intent == IntentType.COMPARE.value:
            sequence = ["sql_tool", "stats_tool"]
        elif intent == IntentType.ANOMALY.value:
            sequence = ["sql_tool", "stats_tool", "anomaly_tool"]
        elif intent == IntentType.FORECAST.value:
            sequence = ["stats_tool", "forecast_tool", "chart_tool"]
        elif intent == IntentType.REPORT.value:
            sequence = ["sql_tool", "stats_tool", "chart_tool", "report_tool"]
        return sequence

    def _prepare_tool_input(self, tool_name: str, state: AgentState) -> Dict[str, Any]:
        """为工具准备输入参数"""
        base = {"user_input": state.get("user_input", "")}
        if tool_name == "sql_tool":
            base["sql_query"] = state.get("sql_query")
        elif tool_name == "stats_tool":
            base["data"] = state.get("sql_results")
            base["intent"] = state.get("intent")
        elif tool_name == "chart_tool":
            base["data"] = state.get("sql_results")
        return base

    def verify_results(self, state: AgentState) -> Dict[str, Any]:
        """校验数据结果

        检查：
        1. 工具调用是否全部成功
        2. 数据结果是否为空
        3. 是否达到最大迭代次数

        Args:
            state: 当前 Agent 状态

        Returns:
            更新后的状态片段
        """
        tool_results = state.get("tool_results", [])
        errors = state.get("errors", [])
        verified = True

        # 校验1：没有错误
        if errors:
            verified = False
            logger.warning(f"校验失败: 存在 {len(errors)} 个错误")

        # 校验2：工具调用全部成功
        failed_tools = [r for r in tool_results if r.get("status") == "error"]
        if failed_tools:
            verified = False
            logger.warning(f"校验失败: {len(failed_tools)} 个工具调用失败")

        # 校验3：数据不为空（若有 SQL 查询）
        if state.get("sql_results") is not None and len(state["sql_results"]) == 0:
            verified = False
            logger.warning("校验失败: SQL 查询结果为空")

        updates = {"verified": verified}
        if verified:
            logger.info("数据校验通过")
        return updates

    def generate_response(self, state: AgentState) -> Dict[str, Any]:
        """生成最终回答

        基于所有工具执行结果和校验状态生成结构化的最终回答。
        包含分析结论、关键数据和下一步建议。

        Args:
            state: 当前 Agent 状态

        Returns:
            更新后的状态片段
        """
        intent = state.get("intent", "general")
        tool_results = state.get("tool_results", [])
        verified = state.get("verified", False)
        errors = state.get("errors", [])

        # 构建回答
        lines = []
        lines.append(f"## 数据分析结果\n")
        lines.append(f"**分析类型**: {intent}")
        lines.append(f"**校验状态**: {'✅ 通过' if verified else '⚠️ 有异常'}\n")

        if errors:
            lines.append("### ⚠️ 执行告警")
            for err in errors:
                lines.append(f"- {err}")
            lines.append("")

        lines.append("### 执行流程")
        for i, record in enumerate(tool_results, 1):
            status_icon = "✅" if record.get("status") == "success" else "❌"
            lines.append(f"{i}. {status_icon} **{record.get('tool_name', 'unknown')}**: {record.get('status', 'unknown')}")
        lines.append("")

        # 从工具结果中提取关键数据
        for record in tool_results:
            output = record.get("output")
            if output and isinstance(output, dict):
                summary = output.get("summary") or output.get("message")
                if summary:
                    lines.append(f"**{record['tool_name']} 产出**: {summary}")
                    lines.append("")

        # 下一步建议
        lines.append("### 💡 建议")
        if intent == IntentType.FETCH.value:
            lines.append("- 如需更细粒度数据，请补充筛选条件")
            lines.append("- 可进行对比分析或趋势分析")
        elif intent == IntentType.ANOMALY.value:
            lines.append("- 建议深入排查异常维度的明细数据")
            lines.append("- 可设置监控告警阈值")
        elif intent == IntentType.FORECAST.value:
            lines.append("- 预测结果仅供参考，实际业务可能有偏差")
            lines.append("- 建议定期更新模型以保持精度")
        elif intent == IntentType.REPORT.value:
            lines.append("- 报告已生成，请检查数据准确性")
            lines.append("- 可根据需要调整报告模板")

        final_response = "\n".join(lines)

        updates = {"final_response": final_response}

        # 归档到长期记忆
        updated_long_term = self.memory_manager.archive_to_long_term(state)
        updates["long_term_memory"] = updated_long_term

        logger.info("最终回答生成完成")
        return updates

    # ── 对外接口 ──

    def run(self, user_input: str, messages: Optional[List[BaseMessage]] = None) -> AgentState:
        """运行 Agent，执行完整的分析工作流

        Args:
            user_input: 用户的输入文本
            messages: 历史对话消息（可选）

        Returns:
            最终的 AgentState，包含 final_response 等字段
        """
        state = create_initial_state(user_input, messages)

        if LANGGRAPH_AVAILABLE and hasattr(self, "graph"):
            # LangGraph 执行模式
            logger.info("使用 LangGraph 执行工作流")
            try:
                result = self.graph.invoke(state)
                return result
            except Exception as e:
                logger.error(f"LangGraph 执行失败: {e}，降级到顺序模式。")
                # 降级到顺序模式

        # 顺序执行模式（降级方案）
        logger.info("使用顺序执行模式")
        state.update(self.analyze_intent(state))
        state.update(self.retrieve_knowledge(state))
        state.update(self.generate_sql(state))
        state.update(self.execute_tools(state))
        state.update(self.verify_results(state))
        state.update(self.generate_response(state))

        return state

    def stream(self, user_input: str, messages: Optional[List[BaseMessage]] = None):
        """流式执行，逐步 yield 每个节点的状态

        Args:
            user_input: 用户的输入文本
            messages: 历史对话消息（可选）

        Yields:
            每个节点执行完成后的状态片段
        """
        state = create_initial_state(user_input, messages)

        if LANGGRAPH_AVAILABLE and hasattr(self, "graph"):
            for step in self.graph.stream(state):
                yield step
        else:
            # 顺序流式
            nodes = [
                ("analyze_intent", self.analyze_intent),
                ("retrieve_knowledge", self.retrieve_knowledge),
                ("generate_sql", self.generate_sql),
                ("execute_tools", self.execute_tools),
                ("verify_results", self.verify_results),
                ("generate_response", self.generate_response),
            ]
            for node_name, node_fn in nodes:
                updates = node_fn(state)
                state.update(updates)
                yield {node_name: updates}

    def reset_memory(self) -> None:
        """重置短期记忆和长期记忆"""
        self.memory_manager = MemoryManager()
        logger.info("Agent 记忆已重置")

    def get_tool_status(self) -> Dict[str, str]:
        """获取当前已注册工具的状态"""
        return {name: "available" for name in self.tools}

    def register_tool(self, tool) -> None:
        """动态注册工具

        Args:
            tool: 需包含 name 属性和 execute() 方法的工具实例
        """
        if not hasattr(tool, "name") or not hasattr(tool, "execute"):
            raise ValueError("工具必须具有 name 属性和 execute() 方法")
        self.tools[tool.name] = tool
        logger.info(f"工具已注册: {tool.name}")
