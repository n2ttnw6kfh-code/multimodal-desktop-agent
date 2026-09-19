# ==============================================================================
# 文件名: emotion/model_loader.py
# 职责: 线程安全地加载/缓存情感模型（双检锁 + 失败缓存，避免反复重试）
# ==============================================================================
import threading
from typing import Optional, Tuple

from .config import EMOTION_MODEL_DIR


class _ModelHolder:
    """全局单例持有者，带失败缓存。"""

    _model = None
    _tokenizer = None
    _load_error: Optional[str] = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> Tuple[object, object]:
        """
        返回 (tokenizer, model)。
        若之前加载失败过，直接抛异常，避免每次重复尝试。
        """
        if cls._model is not None:
            return cls._tokenizer, cls._model

        with cls._lock:
            if cls._model is not None:
                return cls._tokenizer, cls._model

            # 🆕 失败缓存：之前失败过就不再重试
            if cls._load_error is not None:
                raise RuntimeError(cls._load_error)

            try:
                cls._tokenizer, cls._model = cls._do_load()
            except Exception as e:
                cls._load_error = f"加载情感模型失败: {e}"
                raise RuntimeError(cls._load_error) from e

            return cls._tokenizer, cls._model

    @classmethod
    def _do_load(cls):
        from transformers import (
            AutoTokenizer,
            AutoModelForSequenceClassification,
        )

        if not EMOTION_MODEL_DIR.exists():
            raise FileNotFoundError(f"找不到本地模型目录: {EMOTION_MODEL_DIR}")

        tokenizer = AutoTokenizer.from_pretrained(EMOTION_MODEL_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(EMOTION_MODEL_DIR)
        model.eval()
        return tokenizer, model

    @classmethod
    def reset(cls):
        """测试用：清空缓存。"""
        with cls._lock:
            cls._model = None
            cls._tokenizer = None
            cls._load_error = None