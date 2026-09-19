# ==============================================================================
# 文件名: tools/read_url.py
# 职责: 抓取网页正文并清洗为纯文本，供 Agent 阅读
# ==============================================================================
import re
import requests
from bs4 import BeautifulSoup

from .base import register_tool

# 一些常见的"噪音"标签，直接删掉
_NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside",
               "form", "iframe", "noscript", "svg"]

_MAX_CHARS = 4000   # 截断，防止上下文爆炸


@register_tool(
    name="read_url",
    description=(
        "读取指定网页的正文内容并返回纯文本。"
        "当用户给出一个 URL 让你总结/分析，或搜索结果里的链接需要深入阅读时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "要读取的网页完整 URL"}
        },
        "required": ["url"],
    },
)
def read_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return f"URL 格式不正确: {url}"

    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        resp.raise_for_status()
    except Exception as e:
        return f"网页抓取失败: {e}"

    # 编码兜底：requests 猜错编码时从 content 里重新解
    if resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")

    # 删噪音
    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # 优先取 <article> 或 <main>，否则退到 <body>
    main = soup.find("article") or soup.find("main") or soup.body or soup

    text = main.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)   # 压缩空行

    if not text:
        return "（网页没有可读正文）"

    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS] + f"\n\n...（正文过长，已截断至 {_MAX_CHARS} 字）"

    return f"【网页正文】{url}\n\n{text}"