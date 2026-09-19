# ==============================================================================
# 文件名: audio/tts.py
# 职责: Edge-TTS 语音合成（QThread）+ 播放由主线程负责
# ==============================================================================
import asyncio
import os
import re
import tempfile

import edge_tts
from PyQt6.QtCore import QThread, pyqtSignal


# ---- 可选音色 ----
VOICES = {
    "晓晓（女·温柔）": "zh-CN-XiaoxiaoNeural",
    "云希（男·沉稳）": "zh-CN-YunxiNeural",
    "云健（男·新闻）": "zh-CN-YunjianNeural",
    "晓伊（女·活泼）": "zh-CN-XiaoyiNeural",
    "云扬（男·专业）": "zh-CN-YunyangNeural",
}

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


class TTSThread(QThread):
    """
    只负责合成 mp3。合成完 emit `synthesized(mp3_path)`。
    播放由 MainWindow 里的 QMediaPlayer 在主线程完成。
    """

    synthesized = pyqtSignal(str)       # 🆕 传给主线程播放
    speak_failed = pyqtSignal(str)

    def __init__(self, text: str, voice: str = DEFAULT_VOICE, parent=None):
        super().__init__(parent)
        self.text = text
        self.voice = voice

    def run(self):
        try:
            if not self.text.strip():
                return

            path = self._synthesize(self.text, self.voice)
            self.synthesized.emit(path)   # 🆕 交给主线程播放

        except Exception as e:
            self.speak_failed.emit(f"语音合成失败: {e}")

    def _synthesize(self, text: str, voice: str) -> str:
        """调用 edge-tts 合成 mp3，返回文件路径"""
        fd, path = tempfile.mkstemp(suffix=".mp3", prefix="tts_")
        os.close(fd)

        async def _do():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(path)

        asyncio.run(_do())
        return path


# ==============================================================================
# 文本清理
# ==============================================================================
def strip_markdown(text: str) -> str:
    """去掉 markdown 标记，避免念出'星号星号'"""
    if not text:
        return ""

    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^\s*\|?[\s\-:|]+\|?\s*$", "", text, flags=re.M)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]+", "", text)

    return text.strip()