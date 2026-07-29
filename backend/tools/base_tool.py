"""
BaseTool —— 工具抽象基类

所有数据分析工具必须继承此类，并实现 execute() 抽象方法。
提供统一的 name / description / parameters 属性定义和 validate() 方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTool(ABC):
    """工具抽象基类

    属性：
        name:        工具名称（唯一标识，用于 Agent 路由）
        description: 工具功能描述（供 LLM 理解使用场景）
        parameters:  工具入参 schema（OpenAI function calling 风格）

    方法：
        execute(**kwargs) -> Any:   执行工具核心逻辑
        validate(**kwargs) -> bool: 校验输入参数合法性
    """

    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        self._name = name or self.__class__.__name__
        self._description = description or ""
        self._parameters: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        """获取工具名称"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def description(self) -> str:
        """获取工具描述"""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @property
    def parameters(self) -> Dict[str, Any]:
        """获取工具参数 schema

        返回 OpenAI function calling 兼容的 JSON Schema 格式：
        {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
        """
        return self._parameters

    @parameters.setter
    def parameters(self, schema: Dict[str, Any]) -> None:
        self._parameters = schema

    def to_openai_function(self) -> Dict[str, Any]:
        """转为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_langchain_tool(self) -> Dict[str, Any]:
        """转为 LangChain Tool 配置格式"""
        return {
            "name": self.name,
            "description": self.description,
            "args_schema": self.parameters,
        }

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """执行工具核心逻辑

        所有子类必须实现此方法。

        Args:
            **kwargs: 工具执行所需的参数

        Returns:
            工具执行结果

        Raises:
            NotImplementedError: 未实现时抛出
        """
        raise NotImplementedError(f"工具 {self.name} 未实现 execute() 方法")

    def validate(self, **kwargs: Any) -> bool:
        """校验输入参数合法性

        基类默认实现：检查 parameters 中 required 字段是否全部提供。
        子类可覆盖此方法添加自定义校验逻辑。

        Args:
            **kwargs: 待校验的输入参数

        Returns:
            True 表示校验通过，False 表示校验失败

        Raises:
            ValueError: 缺失必填参数时抛出
        """
        required_params = self.parameters.get("required", [])
        for param in required_params:
            if param not in kwargs or kwargs[param] is None:
                raise ValueError(f"缺少必填参数: {param}")
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
