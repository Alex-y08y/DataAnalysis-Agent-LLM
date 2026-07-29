"""
DashScope 通义千问大模型客户端

封装阿里云 DashScope SDK，支持多模型切换、对话历史管理、长文本分片、
Token 用量统计与完整的异常处理。
"""

import logging
import time
from typing import Any

import dashscope
from dashscope import Generation

from config.settings import dashscope_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 自定义异常
# ---------------------------------------------------------------------------

class LLMException(Exception):
    """LLM 调用基类异常"""
    pass


class LLMTimeoutError(LLMException):
    """API 超时异常"""
    pass


class LLMRateLimitError(LLMException):
    """限流异常"""
    pass


class LLMQuotaExhaustedError(LLMException):
    """免费额度 / 余额耗尽异常"""
    pass


# ---------------------------------------------------------------------------
# 客户端
# ---------------------------------------------------------------------------

class DashScopeLLMClient:
    """
    阿里云 DashScope（通义千问）LLM 客户端

    用法:
        client = DashScopeLLMClient()
        reply = client.chat("你好，请介绍一下你自己")
        reply = client.chat("分析这段数据", model="qwen-max")
        reply = client.generate_with_memory(
            "基于以上的对话，总结一下",
            history=[...]
        )
        print(client.get_token_usage_stats())
    """

    # 支持的多模型列表
    AVAILABLE_MODELS = ("qwen-turbo", "qwen-plus", "qwen-max")

    def __init__(self, api_key: str | None = None) -> None:
        """
        初始化客户端

        Args:
            api_key: DashScope API Key。为 None 时从配置读取。
        """
        self._api_key = api_key or dashscope_config.api_key
        if not self._api_key:
            raise ValueError(
                "未配置 DASHSCOPE_API_KEY，请在 .env 文件中设置或传入 api_key 参数"
            )

        dashscope.api_key = self._api_key

        # Token 用量统计（累计）
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0
        self._total_cost: float = 0.0
        self._call_count: int = 0

        logger.info(
            "DashScopeLLMClient 初始化完成，默认模型: %s",
            dashscope_config.model,
        )

    # ------------------------------------------------------------------
    # 公共方法
    # ------------------------------------------------------------------

    def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
    ) -> str:
        """
        单次对话（无记忆）

        Args:
            prompt: 用户输入文本
            system_prompt: 系统提示词（可选）
            model: 模型名称，可选 qwen-turbo / qwen-plus / qwen-max
            temperature: 温度参数，默认 0.1
            max_retries: 最大重试次数

        Returns:
            模型回复文本

        Raises:
            LLMTimeoutError: API 超时
            LLMRateLimitError: 触发限流
            LLMQuotaExhaustedError: 额度耗尽
            LLMException: 其他异常
        """
        model = model or dashscope_config.model
        temperature = temperature if temperature is not None else dashscope_config.temperature
        max_retries = max_retries if max_retries is not None else dashscope_config.max_retries

        # 组装消息
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "调用 DashScope [%s]（尝试 %d/%d），prompt 长度 %d 字符",
                    model, attempt, max_retries, len(prompt),
                )
                resp = Generation.call(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    result_format="message",
                    timeout=dashscope_config.timeout,
                )

                if resp.status_code == 200:
                    # 成功
                    choice = resp.output.choices[0]
                    content = choice.message.content

                    # 统计 Token
                    usage = resp.usage
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)
                    self._record_usage(prompt_tokens, completion_tokens)

                    logger.info(
                        "DashScope 回复成功（prompt=%d, completion=%d, total=%d）",
                        prompt_tokens,
                        completion_tokens,
                        prompt_tokens + completion_tokens,
                    )
                    return content

                # 处理错误状态码
                error_code = resp.status_code
                error_msg = getattr(resp, "message", "未知错误")

                if error_code == 429:
                    raise LLMRateLimitError(
                        f"DashScope 限流（状态码 429）: {error_msg}"
                    )
                elif error_code == 401:
                    raise LLMQuotaExhaustedError(
                        f"认证失败或额度耗尽（状态码 401）: {error_msg}"
                    )
                elif error_code == 400:
                    raise LLMQuotaExhaustedError(
                        f"免费额度耗尽或参数错误（状态码 400）: {error_msg}"
                    )
                elif error_code in (502, 503, 504):
                    raise LLMTimeoutError(
                        f"DashScope 服务暂时不可用（状态码 {error_code}）: {error_msg}"
                    )
                else:
                    raise LLMException(
                        f"DashScope 返回异常状态码 {error_code}: {error_msg}"
                    )

            except LLMRateLimitError as e:
                last_error = e
                wait = min(2 ** attempt, 30)  # 指数退避，最大 30 秒
                logger.warning(
                    "触发限流，等待 %d 秒后重试...（错误: %s）", wait, e
                )
                time.sleep(wait)
                continue

            except LLMTimeoutError as e:
                last_error = e
                logger.warning("API 超时，重试 %d/%d", attempt, max_retries)
                time.sleep(1)
                continue

            except LLMQuotaExhaustedError as e:
                # 额度耗尽不重试
                logger.error("DashScope 额度耗尽: %s", e)
                raise e

            except Exception as e:
                last_error = e
                logger.error(
                    "DashScope 调用异常（尝试 %d/%d）: %s",
                    attempt, max_retries, e,
                    exc_info=True,
                )
                if attempt < max_retries:
                    time.sleep(1)
                continue

        # 所有重试均失败
        raise LLMException(
            f"DashScope 调用在 {max_retries} 次重试后仍然失败"
        ) from last_error

    def generate_with_memory(
        self,
        prompt: str,
        history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        带对话历史的生成

        Args:
            prompt: 当前用户输入
            history: 历史消息列表，示例:
                [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好，有什么可以帮你的？"},
                ]
            system_prompt: 系统提示词
            model: 模型名称
            temperature: 温度参数

        Returns:
            模型回复文本
        """
        model = model or dashscope_config.model
        temperature = temperature if temperature is not None else dashscope_config.temperature

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None
        max_retries = dashscope_config.max_retries

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "generate_with_memory [%s]（尝试 %d/%d），共 %d 条消息",
                    model, attempt, max_retries, len(messages),
                )
                resp = Generation.call(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    result_format="message",
                    timeout=dashscope_config.timeout,
                )

                if resp.status_code == 200:
                    choice = resp.output.choices[0]
                    content = choice.message.content
                    usage = resp.usage
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)
                    self._record_usage(prompt_tokens, completion_tokens)
                    logger.info(
                        "generate_with_memory 成功（prompt=%d, completion=%d）",
                        prompt_tokens, completion_tokens,
                    )
                    return content

                error_code = resp.status_code
                error_msg = getattr(resp, "message", "未知错误")
                if error_code == 429:
                    raise LLMRateLimitError(error_msg)
                elif error_code in (502, 503, 504):
                    raise LLMTimeoutError(f"服务不可用 {error_code}")
                else:
                    raise LLMException(f"状态码 {error_code}: {error_msg}")

            except (LLMRateLimitError, LLMTimeoutError) as e:
                last_error = e
                wait = min(2 ** attempt, 30)
                logger.warning("临时异常，%d 秒后重试: %s", wait, e)
                time.sleep(wait)
                continue
            except LLMQuotaExhaustedError:
                raise
            except Exception as e:
                last_error = e
                logger.error("generate_with_memory 异常: %s", e, exc_info=True)
                if attempt < max_retries:
                    time.sleep(1)
                continue

        raise LLMException(
            f"generate_with_memory 在 {max_retries} 次重试后失败"
        ) from last_error

    def chat_with_long_text(
        self,
        long_text: str,
        max_chunk_chars: int = 3000,
        system_prompt: str | None = None,
        model: str | None = None,
        chunk_summary_prompt: str | None = None,
    ) -> str:
        """
        对超长文本进行分片处理后逐段分析，最后汇总

        Args:
            long_text: 超长文本
            max_chunk_chars: 每片最大字符数（近似）
            system_prompt: 系统提示词
            model: 模型名称
            chunk_summary_prompt: 每段追加的分析指令

        Returns:
            最终汇总结果
        """
        model = model or dashscope_config.model
        chunk_summary_prompt = chunk_summary_prompt or "请分析以上内容的要点。"

        # 简单切分（按换行切，避免断句）
        paragraphs = long_text.split("\n")
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para) + 1  # +1 for newline
            if current_len + para_len > max_chunk_chars and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [para]
                current_len = para_len
            else:
                current_chunk.append(para)
                current_len += para_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        logger.info("长文本已切分为 %d 个分片", len(chunks))

        # 逐段分析
        partial_results: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            logger.info("处理分片 %d/%d（%d 字符）", idx, len(chunks), len(chunk))
            prompt = f"以下是第 {idx} 段文本：\n\n{chunk}\n\n{chunk_summary_prompt}"
            result = self.chat(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
            )
            partial_results.append(f"【分片 {idx} 分析】\n{result}")

        # 汇总
        summary_prompt = (
            f"以下是对同一份长文本分 {len(chunks)} 段分别分析的结果，"
            f"请将它们汇总成一份完整的分析报告：\n\n"
            + "\n\n".join(partial_results)
        )
        final_result = self.chat(
            prompt=summary_prompt,
            system_prompt=system_prompt,
            model=model,
        )
        return final_result

    # ------------------------------------------------------------------
    # Token 用量统计
    # ------------------------------------------------------------------

    def _record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """记录 Token 消耗"""
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens
        self._call_count += 1
        # 粗略费用估算（仅供参考）
        self._total_cost += (
            prompt_tokens * 0.000002 + completion_tokens * 0.000006
        )

    def get_token_usage_stats(self) -> dict[str, Any]:
        """
        获取 Token 用量统计数据

        Returns:
            包含调用次数、Token 累计消耗和估算费用的字典
        """
        return {
            "total_calls": self._call_count,
            "total_prompt_tokens": self._total_prompt_tokens,
            "total_completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
            "estimated_cost_usd": round(self._total_cost, 6),
        }

    def reset_usage_stats(self) -> None:
        """重置 Token 用量统计"""
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_cost = 0.0
        self._call_count = 0
        logger.info("Token 用量统计已重置")

    @property
    def api_key(self) -> str:
        """当前使用的 API Key（安全起见，只返回前 8 位）"""
        return self._api_key[:8] + "..." if len(self._api_key) > 8 else self._api_key
