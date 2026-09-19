# ==============================================================================
# 文件名: emotion/label_utils.py
# 职责: 把模型输出的各种标签写法归一化成内部标准标签（纯函数，无副作用）
# ==============================================================================
from .config import EMOTION_LABELS

# 同义词/缩写映射
_ALIAS = {
    "pos": "positive",
    "neg": "negative",
    "neu": "neutral",
    "label_0": "negative",
    "label_1": "positive",
    "label0": "negative",
    "label1": "positive",
    "0": "negative",
    "1": "positive",
}

# 关键词模糊匹配规则（按优先级从高到低）
# 每条: (目标标签, 关键词元组)
_KEYWORD_RULES = [
    ("angry",   ("angry", "anger", "愤怒", "生气")),
    ("sad",     ("sad", "depress", "悲伤", "难过", "低落")),
    ("anxious", ("anxious", "worry", "焦虑", "紧张", "恐惧")),
    ("happy",   ("happy", "joy", "glad", "excited", "高兴", "开心")),
    ("positive", ("pos", "good", "favor")),
    ("negative", ("neg", "bad", "unfavor")),
]


def normalize_label(raw_label) -> str:
    """
    把模型 config.id2label 返回的字符串统一成内部标准标签。
    兼容 Negative / NEGATIVE / negative / LABEL_0 / 数字索引 等写法。

    >>> normalize_label("Negative")
    'negative'
    >>> normalize_label("LABEL_1")
    'positive'
    >>> normalize_label(None)
    'neutral'
    """
    if raw_label is None:
        return "neutral"

    s = str(raw_label).strip().lower()

    if s in EMOTION_LABELS:
        return s
    if s in _ALIAS:
        return _ALIAS[s]

    for label, keywords in _KEYWORD_RULES:
        if any(w in s for w in keywords):
            return label

    return "neutral"