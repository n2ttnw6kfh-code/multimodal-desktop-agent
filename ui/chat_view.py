# ==============================================================================
# 文件名: ui/chat_view.py
# 职责: 聊天气泡 HTML 渲染（用户 / AI / 系统消息）
# ==============================================================================
from PyQt6.QtWidgets import QTextEdit


class ChatView:
    """
    包装 QTextEdit，提供 append_user / append_ai / append_system 三类气泡。
    """

    def __init__(self, text_edit: QTextEdit):
        self._view = text_edit

    # ---- 对外接口 ----
    def append_user(self, text: str):
        html = (
            '<div style="background-color: #E7F3FF; '
            'border-left: 4px solid #4E79A7; '
            'padding: 10px 14px; '
            'margin: 6px 0 6px 20px; '
            'border-radius: 0 8px 8px 0;">'
            '<span style="color: #4E79A7; font-weight: bold; font-size: 10pt;">你</span>'
            f'<p style="margin-top: 4px; color: #1A1A2E;">{self._escape(text)}</p>'
            '</div>'
        )
        self._view.append(html)

    def append_ai(self, text: str):
        # 🆕 先转义 HTML 特殊字符，再把换行变 <br>
        #    顺序很重要：必须"先转义，后替换 \n → <br>"
        #    否则会把 \n 引入的 <br> 也一起转义掉
        escaped = self._escape(text)
        formatted = escaped.replace('\n', '<br>')

        html = (
            '<div style="background-color: #F8F9FA; '
            'border-left: 4px solid #2ECC71; '
            'padding: 10px 14px; '
            'margin: 6px 20px 6px 0; '
            'border-radius: 0 8px 8px 0;">'
            '<span style="color: #2ECC71; font-weight: bold; font-size: 10pt;">AI</span>'
            f'<p style="margin-top: 4px; color: #1A1A2E; line-height: 1.6;">{formatted}</p>'
            '</div>'
        )
        self._view.append(html)

    # ui/chat_view.py
    def append_image(self, image_path: str):
        """在聊天区插入图片"""
        from PyQt6.QtCore import QUrl

        html = (
            '<div style="background-color: #F8F9FA; '
            'border-left: 4px solid #9B59B6; '
            'padding: 10px 14px; '
            'margin: 6px 20px 6px 0; '
            'border-radius: 0 8px 8px 0;">'
            '<span style="color: #9B59B6; font-weight: bold;">🎨 生成的图片</span>'
            f'<p><img src="{image_path}" width="400"></p>'
            '</div>'
        )
        self._view.append(html)

    def append_system(self, text: str, color: str = "#6C757D"):
        # 🆕 system 消息也可能含特殊字符，一并转义
        html = (
            f'<div style="color: {color}; '
            'font-size: 9pt; '
            'font-style: italic; '
            'margin: 4px 20px; '
            'padding: 4px 8px;">'
            f'{self._escape(text)}</div>'
        )
        self._view.append(html)

    # ---- 内部 ----
    @staticmethod
    def _escape(text: str) -> str:
        """转义 HTML 特殊字符，防止 QTextDocument 解析畸形标签而崩溃"""
        if text is None:
            return ""
        text = text.replace('&', '&amp;')     # ⚠️ 必须先转义 &
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        return text

