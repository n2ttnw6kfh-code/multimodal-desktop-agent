# ==============================================================================
# 文件名: prompt/__init__.py
# 职责: prompt 软件包对外出口
# ==============================================================================
from .manager import (
    get_dynamic_system_prompt,
    update_history_with_time,
    build_emotion_hint,
)

__all__ = [
    "get_dynamic_system_prompt",
    "update_history_with_time",
    "build_emotion_hint",
]