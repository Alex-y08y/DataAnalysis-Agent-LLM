import re
from typing import Any, List, Dict
from tools.base_tool import BaseTool


class DataMaskTool(BaseTool):
    """数据脱敏工具：自动脱敏敏感字段（手机号、身份证、大额金额等）"""

    def __init__(self):
        super().__init__(
            name="data_masker",
            description="自动脱敏手机号、身份证号、大额金额等敏感数据"
        )

    def validate(self, **kwargs) -> bool:
        return "data" in kwargs

    def execute(self, data: Any, fields: List[str] = None,
                mask_all: bool = True) -> Any:
        """执行数据脱敏

        Args:
            data: 输入数据（字典列表或单条记录）
            fields: 需脱敏的字段名列表，None时自动检测
            mask_all: 是否对所有可能的敏感字段自动脱敏

        Returns:
            脱敏后的数据
        """
        if isinstance(data, dict):
            return self._mask_record(data, fields, mask_all)
        elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return [self._mask_record(item, fields, mask_all) for item in data]
        elif hasattr(data, "to_dict"):
            records = data.to_dict(orient="records")
            return [self._mask_record(item, fields, mask_all) for item in records]
        return data

    def _mask_record(self, record: Dict, fields: List[str] = None,
                     mask_all: bool = True) -> Dict:
        """对单条记录进行脱敏"""
        masked = {}
        for key, value in record.items():
            if fields and key not in fields:
                masked[key] = value
                continue

            str_val = str(value) if value is not None else ""

            if mask_all or (fields and key in fields):
                # 手机号脱敏
                if re.match(r"^1[3-9]\d{9}$", str_val):
                    masked[key] = str_val[:3] + "****" + str_val[7:]
                # 身份证号脱敏
                elif re.match(r"^\d{17}[\dXx]$", str_val) or re.match(r"^\d{15}$", str_val):
                    masked[key] = str_val[:6] + "********" + str_val[-4:]
                # 银行卡号脱敏
                elif re.match(r"^\d{16,19}$", str_val):
                    masked[key] = str_val[:4] + " **** **** " + str_val[-4:]
                else:
                    masked[key] = value
            else:
                masked[key] = value

        return masked

    def get_parameters(self) -> Dict:
        return {
            "data": {"type": "object", "description": "待脱敏数据", "required": True},
            "fields": {"type": "array", "description": "需脱敏字段列表", "required": False}
        }
