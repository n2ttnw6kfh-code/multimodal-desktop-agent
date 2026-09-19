# ==============================================================================
# 文件名: ui/widgets.py
# 职责: 自定义 Qt 控件（聚焦发光输入框、脉冲呼吸按钮）
# ==============================================================================
from PyQt6.QtWidgets import QLineEdit, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty


class GlowLineEdit(QLineEdit):
    """
    带聚焦发光效果的输入框。
    用 QGraphicsDropShadowEffect + QPropertyAnimation 实现，
    替代 Qt QSS 不支持的 box-shadow。
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setOffset(0, 0)
        self._glow.setBlurRadius(0)
        self._glow.setColor(QColor(78, 121, 167, 0))
        self.setGraphicsEffect(self._glow)

        self._anim = QPropertyAnimation(self._glow, b"blurRadius", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _animate_glow(self, target_radius: int, target_alpha: int):
        self._glow.setColor(QColor(78, 121, 167, target_alpha))
        self._anim.stop()
        self._anim.setStartValue(self._glow.blurRadius())
        self._anim.setEndValue(target_radius)
        self._anim.start()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._animate_glow(target_radius=12, target_alpha=90)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._animate_glow(target_radius=0, target_alpha=0)


class PulsingButton(QPushButton):
    """
    带脉冲呼吸动画的按钮。
    checked=True 时循环呼吸（背景色在亮绿↔暗绿之间），
    checked=False 时停止并回落 QSS 默认样式。
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)

        self._pulse_value = 0.0
        self._pulse_anim = QPropertyAnimation(self, b"pulseValue", self)
        self._pulse_anim.setDuration(1200)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)

        self.toggled.connect(self._on_toggled)

    def _get_pulse_value(self):
        return self._pulse_value

    def _set_pulse_value(self, v):
        self._pulse_value = v
        self._apply_pulse_style()

    pulseValue = pyqtProperty(float, _get_pulse_value, _set_pulse_value)

    def _apply_pulse_style(self):
        v = self._pulse_value
        base = (46, 204, 113)
        dark = (20, 130, 70)

        r = int(base[0] + (dark[0] - base[0]) * v)
        g = int(base[1] + (dark[1] - base[1]) * v)
        b = int(base[2] + (dark[2] - base[2]) * v)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r}, {g}, {b});
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 10pt;
                font-weight: bold;
            }}
        """)

    def _on_toggled(self, checked):
        if checked:
            self._pulse_anim.start()
        else:
            self._pulse_anim.stop()
            self._pulse_value = 0.0
            self.setStyleSheet("")