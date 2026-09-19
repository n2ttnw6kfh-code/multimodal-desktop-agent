# ==============================================================================
# 文件名: audio/recorder.py
# 职责: 音频录制与保存（不对外暴露 PyAudio 细节）
# ==============================================================================
import wave
import pyaudio
from PyQt6.QtCore import QThread, pyqtSignal

from .config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_CHUNK


class AudioRecorderThread(QThread):
    """录音线程：录完后把 wav 文件路径通过信号发回主线程。"""

    recording_finished = pyqtSignal(str)

    def __init__(self, filename: str = "temp_record.wav"):
        super().__init__()
        self.filename = filename
        self._is_recording = False

        self.chunk = AUDIO_CHUNK
        self.format = pyaudio.paInt16
        self.channels = AUDIO_CHANNELS
        self.rate = AUDIO_SAMPLE_RATE

    def stop_recording(self):
        """外部调用：安全停止录音循环。"""
        self._is_recording = False

    def run(self):
        self._is_recording = True
        p = pyaudio.PyAudio()
        stream = None
        frames = []          # 🆕 提到 try 外，避免异常路径未定义

        try:
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )

            while self._is_recording:
                frames.append(stream.read(self.chunk))

            # ---- 停止音频流 ----
            stream.stop_stream()
            stream.close()
            stream = None

            # ---- 写 wav（此时 p 仍存活）----
            self._write_wav(p, frames)

            p.terminate()
            p = None

            self.recording_finished.emit(self.filename)

        except Exception as e:
            print(f"[录音] 硬件调用失败: {e}")

        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            if p is not None:
                try:
                    p.terminate()
                except Exception:
                    pass

    def _write_wav(self, pyaudio_instance, frames):
        with wave.open(self.filename, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(pyaudio_instance.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b"".join(frames))