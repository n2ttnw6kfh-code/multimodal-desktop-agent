# ==============================================================================
# 文件名: ui/styles.py
# 职责: 集中管理全局 QSS 样式表
# ==============================================================================

APP_QSS = """
/* ===== 主窗口背景 ===== */
QMainWindow {
    background-color: #F0F2F5;
}

/* ===== 聊天区域 ===== */
QTextEdit#chatHistory {
    background-color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 11pt;
    line-height: 1.6;
    color: #1A1A2E;
}

QTextEdit#chatHistory::selection {
    background-color: #4E79A7;
    color: #FFFFFF;
}

/* ===== 输入框 ===== */
QLineEdit {
    background-color: #FFFFFF;
    border: 2px solid #DEE2E6;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 11pt;
    color: #1A1A2E;
    outline: none;
}

QLineEdit:focus {
    border-color: #4E79A7;
}

QLineEdit[placeholderText] {
    color: #ADB5BD;
}

/* ===== 发送按钮 ===== */
QPushButton#sendButton {
    background-color: #4E79A7;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 6px 20px;
    font-size: 11pt;
    font-weight: bold;
    min-width: 70px;
}

QPushButton#sendButton:hover {
    background-color: #3a5f8a;
}

QPushButton#sendButton:pressed {
    background-color: #2d4a7a;
}

QPushButton#sendButton:disabled {
    background-color: #ADB5BD;
}

/* ===== 语音按钮 ===== */
QPushButton#voiceButton {
    background-color: #FF6B6B;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 6px 12px;
    font-size: 10pt;
    font-weight: bold;
}

QPushButton#voiceButton:hover {
    background-color: #ee5a5a;
}

QPushButton#voiceButton:pressed {
    background-color: #d43d3d;
}

QPushButton#voiceButton[checked="true"] {
    background-color: #2ECC71;
}

/* ===== 语音播报按钮 ===== */
QPushButton#ttsButton {
    background-color: #FFFFFF;
    border: 2px solid #DEE2E6;
    border-radius: 10px;
    padding: 4px;
    font-size: 14pt;
}

QPushButton#ttsButton:hover {
    border-color: #4E79A7;
    background-color: #F0F4F8;
}

QPushButton#ttsButton:checked {
    background-color: #E7F3FF;
    border-color: #4E79A7;
}

/* ===== 连续对话按钮 ===== */
QPushButton#continuousButton {
    background-color: #FFFFFF;
    border: 2px solid #DEE2E6;
    border-radius: 10px;
    padding: 6px 12px;
    font-size: 10pt;
    font-weight: bold;
    color: #4E79A7;
    min-width: 100px;
}

QPushButton#continuousButton:hover {
    border-color: #4E79A7;
    background-color: #F0F4F8;
}

QPushButton#continuousButton:checked {
    background-color: #4E79A7;
    color: #FFFFFF;
    border-color: #4E79A7;
}

/* ===== 图片上传按钮 ===== */
QPushButton#attachButton {
    background-color: #FFFFFF;
    border: 2px solid #DEE2E6;
    border-radius: 10px;
    padding: 4px;
    font-size: 14pt;
}

QPushButton#attachButton:hover {
    border-color: #4E79A7;
    background-color: #F0F4F8;
}

/* ===== 标题标签 ===== */
QLabel#appTitle {
    color: #4E79A7;
    font-size: 16pt;
    font-weight: bold;
    background-color: transparent;
}

/* ===== 状态栏 ===== */
QStatusBar QLabel {
    color: #6C757D;
    font-size: 9pt;
    padding: 2px 8px;
}

QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #DEE2E6;
}
"""