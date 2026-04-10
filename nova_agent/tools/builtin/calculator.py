"""
Calculator Plugin - 计算器插件

简单数学计算工具。
"""

import math

from nova_agent.tools.plugin_base import PluginBase, PluginResult


class CalculatorPlugin(PluginBase):
    """计算器插件"""

    name = "calculator"
    description = "Evaluate mathematical expressions"
    version = "0.1.0"
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
        },
        "required": ["expression"],
    }

    def execute(self, parameters: dict, **kwargs) -> PluginResult:
        expression = parameters["expression"]

        # 安全评估：只允许数学运算和基本函数
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "math": math,
            "pi": math.pi,
            "e": math.e,
        }

        try:
            # 评估表达式
            result = eval(expression, {"__builtins__": None}, allowed_names)
            return PluginResult(success=True, result=result)
        except Exception as e:
            return PluginResult(success=False, error=f"Calculation error: {str(e)}")
