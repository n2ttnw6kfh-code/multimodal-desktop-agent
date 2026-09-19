# ==============================================================================
# 文件名: emotion/config.py
# 职责: 情感识别相关常量集中管理
# ==============================================================================
import os
from pathlib import Path

# ---- 模型路径 ----
EMOTION_MODEL_DIR = Path(__file__).resolve().parent.parent / "emotion_model"

# ---- 置信度低于此值 → 降级为中性 ----
EMOTION_MIN_CONFIDENCE = float(os.getenv("EMOTION_MIN_CONFIDENCE", "0.6"))

# ---- 最大 token 长度 ----
EMOTION_MAX_LENGTH = int(os.getenv("EMOTION_MAX_LENGTH", "128"))

# ---- 内部标准标签 → 人类可读 ----
EMOTION_LABELS = {
    "positive": "积极/高兴",
    "negative": "消极/低落",
    "neutral":  "中性/平静",
    "angry":    "愤怒",
    "sad":      "悲伤",
    "anxious":  "焦虑",
    "happy":    "开心",
}