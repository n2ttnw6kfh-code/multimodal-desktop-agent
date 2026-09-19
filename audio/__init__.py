# ==============================================================================
# 文件名: audio/__init__.py
# 职责: 音频软件包对外出口
# ==============================================================================
from .recorder import AudioRecorderThread
from .config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_CHUNK
from .tts import TTSThread, strip_markdown, DEFAULT_VOICE, VOICES
from .continuous import ContinuousController, ContinuousState   # 🆕

__all__ = [
    "AudioRecorderThread",
    "AUDIO_SAMPLE_RATE",
    "AUDIO_CHANNELS",
    "AUDIO_CHUNK",
    "TTSThread",
    "strip_markdown",
    "DEFAULT_VOICE",
    "VOICES",
    "ContinuousController",   # 🆕
    "ContinuousState",        # 🆕
]