# ==============================================================================
# 文件名: tools/translate.py（重写版）
# 职责: 使用免费的 Google Translate 接口做翻译（不再内部调 LLM）
# ==============================================================================
from .base import register_tool

_LANG_ALIAS = {
    "中文": "zh-CN", "汉语": "zh-CN", "chinese": "zh-CN", "zh": "zh-CN",
    "英文": "en", "英语": "en", "english": "en", "en": "en",
    "日文": "ja", "日语": "ja", "japanese": "ja", "ja": "ja",
    "韩文": "ko", "韩语": "ko", "korean": "ko", "ko": "ko",
    "法文": "fr", "法语": "fr", "french": "fr",
    "德文": "de", "德语": "de", "german": "de",
    "俄文": "ru", "俄语": "ru", "russian": "ru",
}


def _normalize_lang(name: str) -> str:
    return _LANG_ALIAS.get(name.strip().lower(), name.strip())


@register_tool(
    name="translate",
    description=(
        "把文本翻译成目标语言。支持中文、英文、日文、韩文、法文、德文、俄文等。"
        "当用户明确要求翻译时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "text":   {"type": "string", "description": "要翻译的文本"},
            "target": {"type": "string", "description": "目标语言，如 '中文'、'英文'"},
            "source": {"type": "string", "description": "源语言（可选，默认自动检测）"},
        },
        "required": ["text", "target"],
    },
)
def translate(text: str, target: str, source: str = "auto") -> str:
    if not text.strip():
        return "翻译失败：文本为空"

    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return "缺少依赖：请先执行 pip install deep-translator"

    target_lang = _normalize_lang(target)
    source_lang = _normalize_lang(source) if source else "auto"

    try:
        result = GoogleTranslator(
            source=source_lang, target=target_lang
        ).translate(text)
        return f"【翻译 → {target_lang}】\n{result}"
    except Exception as e:
        return f"翻译失败: {e}"