# ==============================================================================
# 文件名: tools/emotion_kb.py
# ==============================================================================
from .base import register_tool
from memory import MemoryService


@register_tool(
    name="search_driving_emotion",
    description=(
        "检索车载语音情感分析知识库，包含 200 条驾驶员/乘客语音的情绪分析记录。"
        "每条记录含：语音内容、情绪类型、情绪强度（1-10）、声学特征、场景、分析结论。\n"
        "⚠️ 严格约束：\n"
        "1. 回答必须100%基于本工具返回的记录，禁止编造、猜测、补充任何未出现的场景或结论\n"
        "2. 如果返回结果里没有用户问的内容，直接说'知识库里没有相关记录'\n"
        "3. 引用记录时必须逐字对应，不要改写场景名或结论\n"
        "4. 不要为了凑数补充'类似案例'，有多少条说多少条"
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "检索关键词，可以是情绪类型（如'愤怒'）、场景（如'堵车'、'深夜'）、或自然语言描述",
            },
        },
        "required": ["query"],
    },
)
def search_driving_emotion(query: str) -> str:
    try:
        return MemoryService().search_documents(query, top_k=5)
    except Exception as e:
        return f"知识库检索失败: {e}"