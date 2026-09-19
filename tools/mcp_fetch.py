# ==============================================================================
# 文件名: tools/mcp_fetch.py
# 职责: 通过魔搭托管的 Fetch MCP 抓取网页内容
# 说明:
#   - MCP 是异步的，工具是同步的 → 用独立线程桥接
#   - 每次调用新建连接（简单可靠，性能可接受）
# ==============================================================================
import asyncio
import threading

from .base import register_tool


# ---- 从魔搭复制的配置 ----
MCP_URL = (
    "https://mcp.api-inference.modelscope.net/4606b73e350b4b/sse"     # ⚠️ 换成你自己的完整 URL
)


def _run_mcp_tool(tool_name: str, arguments: dict, timeout: int = 30) -> str:
    """
    在独立线程里跑 asyncio 调用 MCP，避免和 Qt 事件循环冲突。

    Returns:
        工具返回的文本，失败时返回错误信息。
    """
    result_holder = {"value": None, "error": None}

    def _worker():
        try:
            from mcp import ClientSession
            from mcp.client.sse import sse_client

            async def _call():
                async with sse_client(MCP_URL) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        res = await session.call_tool(tool_name, arguments)
                        # MCP 返回的内容是 content 列表，拼接文本部分
                        parts = []
                        for item in res.content:
                            text = getattr(item, "text", None)
                            if text:
                                parts.append(text)
                        return "\n".join(parts)

            result_holder["value"] = asyncio.run(_call())

        except Exception as e:
            result_holder["error"] = str(e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        return f"MCP 调用超时（>{timeout}s）"
    if result_holder["error"]:
        return f"MCP 调用失败: {result_holder['error']}"
    return result_holder["value"] or "（MCP 返回为空）"


@register_tool(
    name="fetch_webpage",
    description=(
        "抓取一个网页的正文内容并转换为 markdown 格式返回。"
        "当用户给出一个 URL 让你阅读/总结/分析，"
        "或搜索结果里的链接需要深入阅读时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要抓取的网页完整 URL",
            },
            "max_length": {
                "type": "integer",
                "description": "返回的最大字符数（默认 5000）",
                "default": 5000,
            },
            "start_index": {
                "type": "integer",
                "description": "从此字符索引开始提取（默认 0）",
                "default": 0,
            },
            "raw": {
                "type": "boolean",
                "description": "是否返回未经 markdown 转换的原始内容（默认 false）",
                "default": False,
            },
        },
        "required": ["url"],
    },
)
def fetch_webpage(
    url: str,
    max_length: int = 5000,
    start_index: int = 0,
    raw: bool = False,
) -> str:
    if not url.startswith(("http://", "https://")):
        return f"URL 格式不正确: {url}"

    arguments = {
        "url": url,
        "max_length": max_length,
        "start_index": start_index,
        "raw": raw,
    }

    print(f"[MCP Fetch] 抓取: {url}")
    result = _run_mcp_tool("fetch", arguments)

    # 简单截断，防止超长内容污染上下文
    MAX_CHARS = 6000
    if len(result) > MAX_CHARS:
        result = result[:MAX_CHARS] + "\n\n...（内容过长，已截断）"

    return f"【网页内容】{url}\n\n{result}"