# ==============================================================================
# 文件名: prompt/manager.py
# 职责: 自动化管理与刷新模型的 System Prompt，隔离复杂的时空规则字符串
# ==============================================================================
import datetime


def get_dynamic_system_prompt():
    """获取附带当前计算机绝对物理时间的动态提示词"""
    now = datetime.datetime.now()
    today = now.date()
    tomorrow = today + datetime.timedelta(days=1)
    day_after = today + datetime.timedelta(days=2)

    return {
        "role": "system",
        "content": (
            f"你是一个高度严谨的实时联网AI助手。\n\n"

            f"【当前真实世界时间】\n"
            f"今天：{today.strftime('%Y年%m月%d日')}\n"
            f"当前时间：{now.strftime('%H时%M分')}\n\n"

            f"【日期映射】\n"
            f"今天 = {today.strftime('%Y年%m月%d日')}\n"
            f"明天 = {tomorrow.strftime('%Y年%m月%d日')}\n"
            f"后天 = {day_after.strftime('%Y年%m月%d日')}\n\n"

            f"【规则】\n"
            f"系统时间永远高于网页内容。\n"
            f"网页中的『今天』『明天』『后天』可能对应网页发布时间，"
            f"回答时必须结合上述系统时间理解，不得直接照搬网页日期。\n\n"

            # 🆕 防幻觉约束
            f"【工具结果使用规则（最高优先级）】\n"
            f"1. 调用 search_driving_emotion 后，回答必须100%基于返回的记录\n"
            f"2. 严禁编造场景名、语音内容、情绪强度、分析结论\n"
            f"3. 引用记录时逐字对应，不要改写\n"
            f"4. 如果返回结果里没有用户问的，明确说'知识库里没有相关记录'\n"
            f"5. 不要为了凑数补充'类似案例'，返回了几条就说几条\n"
            f"6. 不要添加个人评论、闲聊或反问\n\n"

            f"【回答风格】\n"
            f"- 简洁、直接、基于事实\n"
            f"- 不要猜测用户心情\n"
            f"- 不要在末尾加多余的反问或感叹\n"
        )
    }


def update_history_with_time(chat_history_list):
    """确保动态时间提示词永远保持在聊天历史的第一条（索引 0）"""
    dynamic_prompt = get_dynamic_system_prompt()

    if not chat_history_list or chat_history_list[0]["role"] != "system":
        chat_history_list.insert(0, dynamic_prompt)
    else:
        chat_history_list[0] = dynamic_prompt

    return chat_history_list


def build_emotion_hint(emotion_label: str, confidence: float = 1.0) -> str:
    """根据情感标签生成给大模型的提示语"""
    readable = {
        "positive": "积极/高兴",
        "negative": "消极/低落",
        "neutral":  "中性/平静",
        "angry":    "愤怒",
        "sad":      "悲伤",
        "anxious":  "焦虑",
        "happy":    "开心",
    }.get(emotion_label, "未知")

    return (
        f"\n【用户当前情绪】\n"
        f"- 识别结果：{readable}（置信度 {confidence:.0%}）\n"
        f"- 请根据用户情绪调整语气：\n"
        f"- 若用户消极/悲伤/焦虑 → 先共情安抚，再给建议\n"
        f"- 若用户愤怒 → 冷静克制，不要激化\n"
        f"- 若用户积极/开心 → 可以热情互动\n"
        f"- 若中性 → 保持专业客观\n"
    )