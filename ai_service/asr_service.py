# ==============================================================================
# 文件名: ai_service/asr_service.py
# 职责: Whisper 本地语音识别
# 变更: 🆕 模型类级别缓存（双检锁），避免每次识别都重新加载
# ==============================================================================
import os
import threading
from pathlib import Path

from faster_whisper import WhisperModel

from .config import WHISPER_MODEL_DIR


class _WhisperHolder:
    """线程安全的 Whisper 模型持有者（双检锁）"""
    _model = None
    _lock = threading.Lock()

    @classmethod
    def get(cls) -> WhisperModel:
        if cls._model is not None:
            return cls._model
        with cls._lock:
            if cls._model is not None:
                return cls._model
            model_path = str(WHISPER_MODEL_DIR)
            if not Path(model_path).exists():
                raise FileNotFoundError(f"找不到 Whisper 模型目录: {model_path}")
            cls._model = WhisperModel(
                model_path, device="cpu", compute_type="int8", cpu_threads=4
            )
            return cls._model


def transcribe(audio_filename: str) -> str:
    """
    识别音频文件，返回文本。
    失败时抛异常，由调用方（QThread 适配层）捕获并 emit 错误信号。
    """
    if not os.path.exists(audio_filename) or os.path.getsize(audio_filename) == 0:
        raise FileNotFoundError("找不到录音文件或录音文件为空。")

    model = _WhisperHolder.get()
    segments, _info = model.transcribe(
        audio_filename, beam_size=5, language="zh"
    )
    return "".join(segment.text for segment in segments)