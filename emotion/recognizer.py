# ==============================================================================
# 文件名: emotion/recognizer.py
# 职责: 情感识别纯逻辑：文本 → (标准标签, 置信度)
# ==============================================================================
from typing import Tuple

from .config import EMOTION_MIN_CONFIDENCE, EMOTION_MAX_LENGTH
from .label_utils import normalize_label
from .model_loader import _ModelHolder


def recognize_emotion(text: str) -> Tuple[str, float]:
    """
    对文本做情感识别。

    Returns:
        (label, confidence)  label 为内部标准标签，confidence ∈ [0, 1]

    Raises:
        ValueError: 文本为空
        RuntimeError: 模型加载/推理失败
    """
    if not text or not text.strip():
        raise ValueError("文本为空，无法识别情感")

    import torch  # 延迟导入，避免包 import 时就加载 torch

    tokenizer, model = _ModelHolder.get()

    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=EMOTION_MAX_LENGTH
    )
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
        idx = int(torch.argmax(probs).item())
        conf = float(probs[idx].item())

    id2label = getattr(model.config, "id2label", {}) or {}
    raw_label = id2label.get(idx, id2label.get(str(idx), "neutral"))
    label = normalize_label(raw_label)

    # 置信度过低 → 降级为中性
    if conf < EMOTION_MIN_CONFIDENCE:
        label = "neutral"

    return label, conf