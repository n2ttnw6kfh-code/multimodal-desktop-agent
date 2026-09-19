# ==============================================================================
# 文件名: audio/continuous.py
# 职责: 连续对话模式的状态机
# 说明: 只管"什么时候该录、什么时候该播、什么时候该停"，不碰 UI
# ==============================================================================
from enum import Enum


class ContinuousState(Enum):
    """连续对话的状态"""
    IDLE = "idle"              # 未启用
    LISTENING = "listening"    # 正在录音
    TRANSCRIBING = "transcribing"  # 正在识别
    THINKING = "thinking"      # AI 思考中
    SPEAKING = "speaking"      # TTS 播报中


class ContinuousController:
    """
    连续对话状态机。
    由 MainWindow 驱动：
    - start() / stop() 由按钮触发
    - on_recorded() / on_transcribed() / on_reply_done() / on_speak_done() 由各回调触发
    """

    def __init__(self):
        self.enabled = False
        self.state = ContinuousState.IDLE
        self.silent_count = 0          # 连续静音次数（连续 2 次静音自动停）
        self.max_silent = 2            # 连续静音阈值

    def start(self):
        """启用连续对话"""
        self.enabled = True
        self.state = ContinuousState.IDLE
        self.silent_count = 0

    def stop(self):
        """关闭连续对话"""
        self.enabled = False
        self.state = ContinuousState.IDLE

    def is_active(self) -> bool:
        """是否处于活跃状态"""
        return self.enabled

    def set_state(self, state: ContinuousState):
        self.state = state

    def record_silent(self) -> bool:
        """
        记录一次静音。
        返回 True 表示"连续静音达到阈值，应该停止连续对话"。
        """
        self.silent_count += 1
        return self.silent_count >= self.max_silent

    def reset_silent(self):
        """有有效语音时，重置静音计数"""
        self.silent_count = 0