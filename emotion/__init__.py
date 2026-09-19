# ==============================================================================
# 文件名: emotion/__init__.py
# 职责: 情感识别软件包对外出口
# ==============================================================================
from .thread import EmotionRecognitionThread
from .recognizer import recognize_emotion
from .config import EMOTION_LABELS

__all__ = [
    "EmotionRecognitionThread",
    "recognize_emotion",
    "EMOTION_LABELS",
]