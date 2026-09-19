# ==============================================================================
# 文件名: emotion/thread.py
# 职责: 把情感识别逻辑包成 QThread，只负责 emit 信号
# ==============================================================================
from PyQt6.QtCore import QThread, pyqtSignal

from .recognizer import recognize_emotion


class EmotionRecognitionThread(QThread):
    """
    后台线程执行情感识别，避免阻塞 UI。

    信号：
        emotion_ready(str, float)  -> (标准化情感标签, 置信度 0~1)
        emotion_failed(str)        -> 错误信息
    """
    emotion_ready = pyqtSignal(str, float)
    emotion_failed = pyqtSignal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text

    def run(self):
        try:
            label, conf = recognize_emotion(self.text)
            self.emotion_ready.emit(label, conf)
        except Exception as e:
            self.emotion_failed.emit(str(e))