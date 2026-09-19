# ==============================================================================
# 文件名: tools/base.py
# 职责: 工具注册中心、@register_tool 装饰器、ToolExecutor 调度器
# ==============================================================================
import json
from typing import Callable, Dict, Any
from langsmith import traceable

# ==============================================================================
# 全局注册表：tool_name -> {"func": ..., "schema": ...}
# ==============================================================================
_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, parameters: dict):
    """
    装饰器：把一个函数注册为 Agent 工具。

    用法：
        @register_tool(
            name="get_weather",
            description="查询城市天气",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )
        def get_weather(city: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        if name in _REGISTRY:
            raise ValueError(f"工具名重复注册: {name}")
        _REGISTRY[name] = {
            "func": func,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
        return func
    return decorator


def build_tools_schema() -> list:
    """返回所有已注册工具的 Schema 列表"""
    return [entry["schema"] for entry in _REGISTRY.values()]


class ToolExecutor:

    def __init__(self, **context):
        self.context = context

    @traceable(name="tool_execute", run_type="tool")
    def execute(self, tool_name: str, arguments_json: str) -> str:
        try:
            args = json.loads(arguments_json) if arguments_json else {}
        except json.JSONDecodeError:
            return f"工具参数解析失败: {arguments_json}"

        print(f"[工具] 调用 {tool_name}({args})")

        entry = _REGISTRY.get(tool_name)
        if entry is None:
            return f"未知工具: {tool_name}"

        try:
            # 🆕 只注入工具签名里实际需要的 context 参数
            import inspect
            sig = inspect.signature(entry["func"])
            accepted = set(sig.parameters.keys())
            context_to_inject = {
                k: v for k, v in self.context.items() if k in accepted
            }
            merged = {**context_to_inject, **args}
            return entry["func"](**merged)
        except Exception as e:
            return f"工具执行异常: {e}"