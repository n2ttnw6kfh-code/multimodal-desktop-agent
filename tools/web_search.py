# ==============================================================================
# 文件名: tools/web_search.py
# ==============================================================================
import datetime
import requests

from .base import register_tool


@register_tool(
    name="search_tavily",
    description=(
        "联网搜索天气、新闻、比赛、股价、实时事件等最新信息。"
        "当用户询问需要实时数据的问题时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"}
        },
        "required": ["query"],
    },
)
def search_tavily(query: str, tavily_api_key: str) -> str:
    """注意：tavily_api_key 由 ToolExecutor 通过 context 注入"""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        results = resp.json().get("results", [])
        content = "\n".join(
            f"标题: {r['title']}\n内容: {r['content']}\n---" for r in results[:5]
        )

        now = datetime.datetime.now()
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        day_after = today + datetime.timedelta(days=2)

        return (
            f"【系统补充信息（最高优先级）】\n"
            f"当前时间：{now.strftime('%Y年%m月%d日 %H时%M分')}\n"
            f"今天={today.strftime('%Y年%m月%d日')}，"
            f"明天={tomorrow.strftime('%Y年%m月%d日')}，"
            f"后天={day_after.strftime('%Y年%m月%d日')}\n"
            f"注意：网页中的相对日期不一定指真实今天，须以上面系统时间为准。\n"
            f"========================\n{content}"
        )
    except Exception as e:
        return f"联网搜索失败: {e}"