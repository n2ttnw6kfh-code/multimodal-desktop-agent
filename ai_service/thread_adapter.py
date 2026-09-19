# ==============================================================================
# 文件名: ai_service/thread_adapter.py
# 职责: 把纯逻辑包装成 QThread，负责信号发射与中断检查
# ==============================================================================
from PyQt6.QtCore import QThread, pyqtSignal

from .config import TAVILY_API_KEY
from .llm_client import build_client, prepare_messages
from .agent_loop import run_agent_loop, AgentCallbacks
from .asr_service import transcribe
from tools import ToolExecutor

# ==============================================================================
# ASR 线程
# ==============================================================================
class ASRTranscriptionThread(QThread):
    transcribe_success = pyqtSignal(str)
    transcribe_failed = pyqtSignal(str)

    def __init__(self, audio_filename: str):
        super().__init__()
        self.audio_filename = audio_filename

    def run(self):
        try:
            text = transcribe(self.audio_filename)
            self.transcribe_success.emit(text)
        except Exception as e:
            self.transcribe_failed.emit(f"本地语音识别出错: {str(e)}")


# ==============================================================================
# DeepSeek 调用线程
# ==============================================================================
class FetchAIResponseThread(QThread):
    reply_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    stream_started = pyqtSignal()
    chunk_received = pyqtSignal(str)
    stream_finished = pyqtSignal()

    def __init__(self, chat_history_list, emotion_hint: str = ""):
        super().__init__()
        self.chat_history_list = chat_history_list
        self.emotion_hint = emotion_hint
        self.tool_executor = ToolExecutor(tavily_api_key=TAVILY_API_KEY)

    def run(self):
        try:
            client = build_client()
            messages = prepare_messages(self.chat_history_list, self.emotion_hint)

            callbacks = AgentCallbacks(
                on_stream_started=self.stream_started.emit,
                on_chunk=self.chunk_received.emit,
                on_stream_finished=self.stream_finished.emit,
                is_interrupted=self.isInterruptionRequested,
            )

            full_reply = run_agent_loop(
                client, messages, self.tool_executor, callbacks
            )

            # 🆕 只把"用户消息 + 最终回复"写回主历史
            #    不写 tool_calls / tool 消息，避免污染历史结构
            #    messages 里最后的 assistant 回复就是完整回答
            clean_history = self._extract_clean_history(messages)
            self.chat_history_list[:] = clean_history

            self.reply_received.emit(full_reply)

        except Exception as e:
            self.error_occurred.emit(f"DeepSeek API 调用失败: {str(e)}")
            self.stream_finished.emit()

    def _extract_clean_history(self, messages: list) -> list:
        """
        从完整 messages 里提取"干净历史"：
        - 保留 system
        - 保留 user 消息
        - 保留 assistant 的纯文本回复（不要 tool_calls 字段）
        - 丢弃所有 role="tool" 和带 tool_calls 的 assistant
        """
        clean = []
        for m in messages:
            role = m.get("role")
            if role == "system":
                clean.append(m)
            elif role == "user":
                clean.append({"role": "user", "content": m.get("content", "")})
            elif role == "assistant":
                # 只保留有实际文本内容的 assistant（跳过纯 tool_calls 的）
                content = m.get("content", "")
                if content and content.strip():
                    clean.append({"role": "assistant", "content": content})
            # tool 消息直接跳过
        return clean