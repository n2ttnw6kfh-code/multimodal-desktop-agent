# ==============================================================================
# 文件名: ui/main_window.py
# 职责: 主窗口 —— 界面构建、事件绑定、线程生命周期管理
# 变更: 🆕 图片理解（VLM） + 文生图（Agent 工具）
#           - 📎 按钮上传图片 → 通义千问 VL 理解 → 拼进消息
#           - 文生图由 Agent 工具 generate_image 完成，自动打开看图器
# ==============================================================================
import os
import re
import subprocess
import platform

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFileDialog,
)
from PyQt6.QtGui import QTextCursor, QFont
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from audio import (
    AudioRecorderThread,
    TTSThread, strip_markdown, DEFAULT_VOICE,
    ContinuousController, ContinuousState,
)
from ai_service import FetchAIResponseThread, ASRTranscriptionThread
from ai_service.vlm_client import describe_image      # 🆕
from prompt import manager as prompt_manager
from prompt import build_emotion_hint
from emotion import EmotionRecognitionThread
from memory import MemoryService

from .styles import APP_QSS
from .widgets import GlowLineEdit, PulsingButton
from .chat_view import ChatView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多模态智能体桌面助手")
        self.resize(880, 660)

        # ===== 状态 =====
        self.chat_history_list = [
            {"role": "system", "content": "你是一个高度严谨的实时联网AI助手。"}
        ]
        self.recorder_thread = None
        self.asr_thread = None
        self.thread = None
        self.emotion_thread = None

        self.current_reply_text = ""
        self.is_streaming = False

        # ===== 流式渲染状态 =====
        self._stream_buffer = ""
        self._stream_start_pos = None

        # ===== 情感识别中间态 =====
        self.pending_user_text = ""
        self.pending_emotion_hint = ""
        self.pending_emotion_label = ""

        # ===== 🆕 图片状态 =====
        self.pending_image_path = None

        # ===== TTS 状态 =====
        self.tts_thread = None
        self.tts_enabled = True
        self.tts_voice = DEFAULT_VOICE
        self._tts_temp_file = None

        self.tts_player = QMediaPlayer(self)
        self.tts_audio = QAudioOutput(self)
        self.tts_player.setAudioOutput(self.tts_audio)
        self.tts_audio.setVolume(1.0)
        self.tts_player.mediaStatusChanged.connect(self._on_media_status_changed)

        # ===== 连续对话状态机 =====
        self.continuous = ContinuousController()

        # ===== 录音定时器（连续对话用）=====
        self.record_seconds = int(os.getenv("CONTINUOUS_RECORD_SECONDS", "5"))
        self.record_timer = QTimer(self)
        self.record_timer.setSingleShot(True)
        self.record_timer.timeout.connect(self._auto_stop_recording)

        # ===== 长期记忆 =====
        try:
            self.memory = MemoryService()
        except Exception as e:
            print(f"[记忆] 初始化失败: {e}")
            self.memory = None

        # ===== 样式 & UI =====
        self.setStyleSheet(APP_QSS)
        self._build_ui()

        # ===== 欢迎消息 =====
        self.chat_view.append_ai(
            "你好！我是多模态智能体桌面助手 🤖\n\n"
            "我支持：\n"
            "• 💬 文字对话\n"
            "• 🎤 语音输入（Whisper）\n"
            "• 📎 图片理解（通义千问 VL）\n"
            "• 🎨 文生图（通义万相）\n"
            "• 🌐 联网搜索 / 天气 / 计算 / 地图 / 知识库\n\n"
            "有什么可以帮你的吗？"
        )

    # ==========================================================================
    # UI 构建
    # ==========================================================================
    def _build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        # --- 标题栏 ---
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 4)
        self.title_label = QLabel("🤖 多模态智能体桌面助手")
        self.title_label.setObjectName("appTitle")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        # --- 聊天区 ---
        self.chat_history = QTextEdit()
        self.chat_history.setObjectName("chatHistory")
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Microsoft YaHei", 11))
        self.chat_history.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.chat_history.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        main_layout.addWidget(self.chat_history, stretch=1)

        self.chat_view = ChatView(self.chat_history)

        # --- 输入行 ---
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 4, 0, 0)
        input_layout.setSpacing(8)

        self.input_field = GlowLineEdit()
        self.input_field.setPlaceholderText("输入你的问题，按回车发送...")
        self.input_field.setFont(QFont("Microsoft YaHei", 11))
        self.input_field.setObjectName("inputField")

        # 🆕 图片上传按钮
        self.attach_button = QPushButton("📎")
        self.attach_button.setObjectName("attachButton")
        self.attach_button.setFont(QFont("Microsoft YaHei", 12))
        self.attach_button.setToolTip("上传图片（VLM 理解）")
        self.attach_button.setFixedWidth(44)
        self.attach_button.clicked.connect(self._on_attach_image)

        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFont(QFont("Microsoft YaHei", 11))

        # TTS 开关
        self.tts_button = QPushButton("🔊")
        self.tts_button.setObjectName("ttsButton")
        self.tts_button.setCheckable(True)
        self.tts_button.setChecked(True)
        self.tts_button.setFont(QFont("Microsoft YaHei", 12))
        self.tts_button.setToolTip("语音播报：开/关")
        self.tts_button.setFixedWidth(44)
        self.tts_button.toggled.connect(self._on_tts_toggle)

        # 连续对话按钮
        self.continuous_button = QPushButton("🔄 连续对话")
        self.continuous_button.setObjectName("continuousButton")
        self.continuous_button.setCheckable(True)
        self.continuous_button.setFont(QFont("Microsoft YaHei", 10))
        self.continuous_button.setToolTip("连续对话：AI 播报完自动开麦")
        self.continuous_button.toggled.connect(self._on_continuous_toggle)

        self.voice_button = PulsingButton("🎤 语音")
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.setFont(QFont("Microsoft YaHei", 10))
        self.voice_button.clicked.connect(self.toggle_recording)

        input_layout.addWidget(self.input_field, stretch=1)
        input_layout.addWidget(self.attach_button)       # 🆕
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.tts_button)
        input_layout.addWidget(self.continuous_button)
        input_layout.addWidget(self.voice_button)
        main_layout.addLayout(input_layout)

        # --- 事件 ---
        self.send_button.clicked.connect(self.handle_send)
        self.input_field.returnPressed.connect(self.handle_send)

        # --- 状态栏 ---
        self.statusBar().showMessage("就绪")
        self.statusBar().setFont(QFont("Microsoft YaHei", 9))

    # ==========================================================================
    # 🆕 图片上传
    # ==========================================================================
    def _on_attach_image(self):
        """弹出文件选择框，选图片"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp)",
        )
        if not path:
            return

        self.pending_image_path = path
        self.chat_view.append_system(
            f"📎 已附加图片：{os.path.basename(path)}", color="#4E79A7"
        )
        self.statusBar().showMessage("📎 已附加图片，输入问题后发送（或直接发送图片）")

    # ==========================================================================
    # 发送消息
    # ==========================================================================
    def handle_send(self):
        text = self.input_field.text().strip()

        # 允许"只发图片"
        if not text and not self.pending_image_path:
            return
        if self.is_streaming:
            return
        if self.emotion_thread and self.emotion_thread.isRunning():
            return

        # 中断 TTS
        self._stop_tts()

        # 🆕 有图片 → 先调 VLM 理解
        if self.pending_image_path:
            image_path = self.pending_image_path
            self.pending_image_path = None
            self.statusBar().showMessage("🔍 正在理解图片...")
            self.send_button.setEnabled(False)

            try:
                desc = describe_image(image_path, text)
                text = (
                    f"{text}\n\n【图片内容】\n{desc}"
                    if text else f"【图片内容】\n{desc}"
                )
                self.chat_view.append_system(
                    f"[图片理解完成] {desc[:80]}..."
                    if len(desc) > 80 else f"[图片理解完成] {desc}",
                    color="#2ECC71",
                )
            except Exception as e:
                self.chat_view.append_system(
                    f"[图片理解失败] {e}", color="#E03131"
                )
                self.send_button.setEnabled(True)
                self.statusBar().clearMessage()
                return
            finally:
                self.statusBar().clearMessage()

        if not text:
            return

        self.chat_view.append_user(text)
        self.statusBar().showMessage("正在分析情绪...")

        self.pending_user_text = text
        self.input_field.clear()
        self.send_button.setEnabled(False)

        self.emotion_thread = EmotionRecognitionThread(text)
        self.emotion_thread.emotion_ready.connect(self.on_emotion_ready)
        self.emotion_thread.emotion_failed.connect(self.on_emotion_failed)
        self.emotion_thread.start()

    # ==========================================================================
    # 情感识别回调
    # ==========================================================================
    def on_emotion_ready(self, label, conf):
        self.statusBar().clearMessage()
        self.pending_emotion_hint = build_emotion_hint(label, conf)
        self.pending_emotion_label = label

        emoji_map = {
            "positive": "😊", "negative": "😔", "neutral": "😐",
            "angry": "😠", "sad": "😢", "anxious": "😰", "happy": "😄",
        }
        emoji = emoji_map.get(label, "🤔")
        self.chat_view.append_system(
            f"[情绪识别] {emoji} {label}（置信度 {conf:.0%}）"
        )
        self._do_send_with_emotion(self.pending_user_text)

    def on_emotion_failed(self, err):
        self.statusBar().clearMessage()
        self.chat_view.append_system(f"[情绪识别跳过] {err}", color="#FFA500")
        self.pending_emotion_hint = ""
        self.pending_emotion_label = ""
        self._do_send_with_emotion(self.pending_user_text)

    # ==========================================================================
    # 发起大模型请求
    # ==========================================================================
    def _do_send_with_emotion(self, text):
        self.chat_history_list = prompt_manager.update_history_with_time(
            self.chat_history_list
        )
        self.chat_history_list.append({"role": "user", "content": text})
        self._history_len_before = len(self.chat_history_list)

        if self.memory is not None:
            try:
                self.memory.add_memory(
                    role="user",
                    content=text,
                    extra={"emotion": self.pending_emotion_label or "unknown"},
                )
            except Exception as e:
                print(f"[记忆] 写入用户消息失败: {e}")

        self.current_reply_text = ""
        self._stream_buffer = ""
        self._stream_start_pos = None
        self.is_streaming = False

        if self.continuous.is_active():
            self.continuous.set_state(ContinuousState.THINKING)

        self.thread = FetchAIResponseThread(
            self.chat_history_list,
            emotion_hint=self.pending_emotion_hint,
        )
        self.thread.reply_received.connect(self.on_reply_received)
        self.thread.error_occurred.connect(self.on_error_occurred)
        self.thread.stream_started.connect(self.on_stream_started)
        self.thread.chunk_received.connect(self.on_chunk_received)
        self.thread.stream_finished.connect(self.on_stream_finished)
        self.thread.start()

    # ==========================================================================
    # 流式回调
    # ==========================================================================
    def on_stream_started(self):
        self.is_streaming = True
        self.current_reply_text = ""
        self._stream_buffer = ""
        self.statusBar().showMessage("✨ AI 正在思考...")
        self._stream_start_pos = max(
            0, self.chat_history.document().characterCount() - 1
        )

    def on_chunk_received(self, piece):
        self.current_reply_text += piece
        self._stream_buffer += piece

        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(piece)
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()

    def on_stream_finished(self):
        self.is_streaming = False
        self.statusBar().showMessage("就绪")
        self._finalize_stream_render()

    def _finalize_stream_render(self):
        if not self._stream_buffer.strip():
            return

        if self._stream_start_pos is None:
            try:
                self.chat_view.append_ai(self._stream_buffer)
            except Exception as e:
                print(f"[UI] 流式兜底渲染失败: {e}")
            return

        try:
            doc = self.chat_history.document()
            cursor = QTextCursor(doc)
            start = min(self._stream_start_pos, doc.characterCount() - 1)
            cursor.setPosition(start)
            cursor.movePosition(
                QTextCursor.MoveOperation.End,
                QTextCursor.MoveMode.KeepAnchor,
            )
            cursor.removeSelectedText()
            self.chat_view.append_ai(self._stream_buffer)
        except Exception as e:
            print(f"[UI] 流式重绘失败: {e}")
            try:
                self.chat_view.append_ai(self._stream_buffer)
            except Exception:
                pass

    # ==========================================================================
    # 回复 / 错误
    # ==========================================================================
    def on_reply_received(self, reply_text):
        if not self._stream_buffer.strip() and reply_text.strip():
            self.chat_view.append_ai(reply_text)

        self.chat_history_list.append(
            {"role": "assistant", "content": reply_text}
        )

        if self.memory is not None and reply_text.strip():
            try:
                self.memory.add_memory(role="assistant", content=reply_text)
            except Exception as e:
                print(f"[记忆] 写入 AI 回复失败: {e}")

        # 🆕 检测是否生成了图片，自动打开看图器
        self._maybe_open_generated_image(reply_text)

        # TTS 播报
        if self.tts_enabled and reply_text.strip():
            self._speak(reply_text)
        else:
            if self.continuous.is_active():
                QTimer.singleShot(500, self._start_listening)

        self.send_button.setEnabled(True)
        self._stream_buffer = ""
        self._stream_start_pos = None

    def _maybe_open_generated_image(self, reply_text: str):
        """检测回复里是否有'图片已生成：xxx'，自动打开"""
        m = re.search(r"图片已生成：([^\n]+)", reply_text)
        if not m:
            return
        path = m.group(1).strip()
        if not os.path.exists(path):
            return
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print(f"[图片] 打开失败: {e}")

    def on_error_occurred(self, error_str):
        self._stream_buffer = ""
        self._stream_start_pos = None

        self.chat_view.append_system(f"[系统错误] {error_str}", color="#E03131")
        self.send_button.setEnabled(True)

        if hasattr(self, "_history_len_before"):
            del self.chat_history_list[self._history_len_before:]

        if self.continuous.is_active():
            self._exit_continuous("系统错误")

    # ==========================================================================
    # TTS 语音播报
    # ==========================================================================
    def _on_tts_toggle(self, checked):
        self.tts_enabled = checked
        self.tts_button.setText("🔊" if checked else "🔇")
        self.statusBar().showMessage(
            "🔊 语音播报已开启" if checked else "🔇 语音播报已关闭"
        )
        if not checked:
            self._stop_tts()

    def _speak(self, text: str):
        self._stop_tts()

        clean = strip_markdown(text)
        if not clean:
            if self.continuous.is_active():
                QTimer.singleShot(300, self._start_listening)
            return

        self.tts_thread = TTSThread(clean, self.tts_voice)
        self.tts_thread.synthesized.connect(self._on_tts_synthesized)
        self.tts_thread.speak_failed.connect(
            lambda err: print(f"[TTS] {err}")
        )
        self.statusBar().showMessage("🔊 正在合成语音...")
        self.tts_thread.start()

        if self.continuous.is_active():
            self.continuous.set_state(ContinuousState.SPEAKING)

    def _on_tts_synthesized(self, mp3_path: str):
        self._tts_temp_file = mp3_path
        self.tts_player.setSource(QUrl.fromLocalFile(mp3_path))
        self.tts_player.play()
        self.statusBar().showMessage("🔊 正在播报...")

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._cleanup_tts_file()
            if not self.is_streaming:
                self.statusBar().showMessage("就绪")
            if self.continuous.is_active():
                QTimer.singleShot(500, self._start_listening)
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print("[TTS] 播放失败：无效媒体")
            self._cleanup_tts_file()
            if self.continuous.is_active():
                QTimer.singleShot(500, self._start_listening)

    def _stop_tts(self):
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.terminate()
            self.tts_thread.wait(500)
        if self.tts_player:
            self.tts_player.stop()
        self._cleanup_tts_file()

    def _cleanup_tts_file(self):
        if self._tts_temp_file and os.path.exists(self._tts_temp_file):
            try:
                os.remove(self._tts_temp_file)
            except Exception:
                pass
        self._tts_temp_file = None

    # ==========================================================================
    # 连续对话模式
    # ==========================================================================
    def _on_continuous_toggle(self, checked):
        if checked:
            self.continuous.start()
            self.continuous_button.setText("⏹ 停止")
            self.chat_view.append_system(
                f"🔄 连续对话模式已开启，每次录 {self.record_seconds} 秒"
                f"（连续 2 次静音自动退出）",
                color="#2ECC71",
            )
            QTimer.singleShot(300, self._start_listening)
        else:
            self._exit_continuous("用户手动停止")

    def _exit_continuous(self, reason: str = ""):
        self.continuous.stop()
        self.continuous_button.setChecked(False)
        self.continuous_button.setText("🔄 连续对话")

        if self.record_timer.isActive():
            self.record_timer.stop()

        if self.recorder_thread and self.recorder_thread.isRunning():
            self.recorder_thread.stop_recording()
        self._stop_tts()

        if reason:
            self.chat_view.append_system(
                f"⏹ 连续对话已退出（{reason}）", color="#FFA500"
            )
        self.statusBar().showMessage("就绪")

    def _start_listening(self):
        if not self.continuous.is_active():
            return
        if self.is_streaming:
            return
        if self.recorder_thread and self.recorder_thread.isRunning():
            return

        self.continuous.set_state(ContinuousState.LISTENING)
        self.voice_button.setChecked(True)
        self.voice_button.setText("⏹ 停止录音")
        self.input_field.setEnabled(False)
        self.statusBar().showMessage(
            f"🎤 正在聆听...（{self.record_seconds} 秒）"
        )

        self.recorder_thread = AudioRecorderThread(filename="temp_record.wav")
        self.recorder_thread.recording_finished.connect(
            self.on_recording_finished
        )
        self.recorder_thread.start()

        self.record_timer.start(self.record_seconds * 1000)

    def _auto_stop_recording(self):
        if self.recorder_thread and self.recorder_thread.isRunning():
            print(f"[连续对话] {self.record_seconds} 秒到，自动停止录音")
            self.recorder_thread.stop_recording()

    # ==========================================================================
    # 语音录制
    # ==========================================================================
    def toggle_recording(self):
        if self.voice_button.isChecked():
            self.voice_button.setText("⏹ 停止录音")
            self.input_field.setEnabled(False)

            self.recorder_thread = AudioRecorderThread(filename="temp_record.wav")
            self.recorder_thread.recording_finished.connect(
                self.on_recording_finished
            )
            self.recorder_thread.start()
        else:
            self.voice_button.setText("🎤 语音")
            self.input_field.setEnabled(True)
            if self.recorder_thread:
                self.recorder_thread.stop_recording()
            if self.continuous.is_active():
                self._exit_continuous("手动停止录音")

    def on_recording_finished(self, filename):
        if self.record_timer.isActive():
            self.record_timer.stop()

        self.voice_button.setChecked(False)
        self.voice_button.setText("🎤 语音")
        self.input_field.setEnabled(True)

        self.chat_view.append_system(f"[录音完成] {filename}", color="#2ECC71")

        if self.continuous.is_active():
            self.continuous.set_state(ContinuousState.TRANSCRIBING)

        self.asr_thread = ASRTranscriptionThread(filename)
        self.asr_thread.transcribe_success.connect(
            lambda text: self.on_asr_success(text, filename)
        )
        self.asr_thread.transcribe_failed.connect(
            lambda err: self.on_asr_failed(err, filename)
        )
        self.asr_thread.start()

    def on_asr_success(self, text, filename):
        text = text.strip()

        if not text:
            self.chat_view.append_system(
                "语音识别结束，但好像您刚刚没有说话。", color="#FFA500"
            )
            self.cleanup_temp_file(filename)

            if self.continuous.is_active():
                if self.continuous.record_silent():
                    self._exit_continuous("连续静音")
                else:
                    QTimer.singleShot(500, self._start_listening)
            return

        if self.continuous.is_active():
            self.continuous.reset_silent()

        self.chat_view.append_system(f'🗣️ 识别结果：" {text} "', color="#4E79A7")
        self.input_field.setText(text)
        self.handle_send()
        self.cleanup_temp_file(filename)

    def on_asr_failed(self, error_str, filename):
        self.chat_view.append_system(f"[ASR 错误] {error_str}", color="#E03131")
        self.cleanup_temp_file(filename)

        if self.continuous.is_active():
            if self.continuous.record_silent():
                self._exit_continuous("识别连续失败")
            else:
                QTimer.singleShot(500, self._start_listening)

    def cleanup_temp_file(self, filename):
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"临时文件 {filename} 清理成功。")
        except Exception as e:
            print(f"清理文件失败: {e}")

    # ==========================================================================
    # 优雅退出
    # ==========================================================================
    def closeEvent(self, event):
        if self.record_timer.isActive():
            self.record_timer.stop()

        self._exit_continuous()
        self._stop_tts()

        for th in (self.thread, self.emotion_thread, self.asr_thread):
            if th and th.isRunning():
                th.requestInterruption()
                th.wait(2000)

        if self.recorder_thread and self.recorder_thread.isRunning():
            self.recorder_thread.stop_recording()
            self.recorder_thread.wait(2000)

        event.accept()