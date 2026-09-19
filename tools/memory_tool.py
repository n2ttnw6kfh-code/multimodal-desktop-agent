# ==============================================================================
# 文件名: tools/memory_tool.py
# ==============================================================================
from .base import register_tool
from memory import MemoryService


@register_tool(
    name="memory_search",
    description=(
        "检索与用户过往对话相关的长期记忆。"
        "当用户提及过去说过的事、或者你判断需要回忆历史时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "要检索的关键信息"}
        },
        "required": ["query"],
    },
)
def memory_search(query: str) -> str:
# def memory_search(query: str, **_kwargs) -> str:
    try:
        memory = MemoryService()
        return memory.memory_search_tool(query)
    except Exception as e:
        return f"记忆检索失败: {e}"