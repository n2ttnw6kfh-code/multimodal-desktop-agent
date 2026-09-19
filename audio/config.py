# ==============================================================================
# 文件名: audio/config.py
# 职责: 音频采集参数集中管理
# ==============================================================================
import os

# 16kHz 是 Whisper / 主流 ASR 的黄金采样率
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "1"))
AUDIO_CHUNK = int(os.getenv("AUDIO_CHUNK", "1024"))
AUDIO_FORMAT_WIDTH = 2          # paInt16 = 2 字节