# ==============================================================================
# 文件名: tools/time_tool.py
# ==============================================================================
import datetime

from .base import register_tool


@register_tool(
    name="get_current_time",
    description="获取当前的日期和时间。",
    parameters={"type": "object", "properties": {}},
)
def get_current_time() -> str:
# def get_current_time(**_kwargs) -> str:
    now = datetime.datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return (
        f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')} "
        f"（{weekdays[now.weekday()]}）"
    )