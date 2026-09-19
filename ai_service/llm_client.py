# ==============================================================================
# 文件名: ai_service/llm_client.py
# 职责: 构造 DeepSeek client、三级上下文管理、情感提示注入
# 变更: 🆕 摘要持久化到 ChromaDB（三级缓存：ChromaDB → 内存 → 重生成）
# ==============================================================================
import hashlib
from langsmith import traceable
from openai import OpenAI

from .config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT,
    HISTORY_MAX_LEN,
    HISTORY_KEEP_LEN,
    HISTORY_SUMMARY_MAX_TOKENS,
)
from prompt import update_history_with_time


def build_client() -> OpenAI:
    """构造 DeepSeek client（OpenAI 兼容接口）"""
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        timeout=DEEPSEEK_TIMEOUT,
    )
    return wrap_openai(client)


# ==============================================================================
# 摘要缓存（进程内，避免重复压缩相同历史）
# ==============================================================================
_summary_cache: dict = {}


def _history_hash(messages: list) -> str:
    """对消息列表算 hash，用作摘要缓存 key"""
    text = "|".join(
        f"{m.get('role')}:{m.get('content', '')}"
        for m in messages
    )
    return hashlib.md5(text.encode("utf-8")).hexdigest()

@traceable(name="summarize_history", run_type="llm")
def _summarize_history(messages: list) -> str:
    """
    用 LLM 把历史对话压缩成摘要。
    三级缓存：ChromaDB（持久）→ 内存（快）→ 重新生成。
    """
    if not messages:
        return ""

    key = _history_hash(messages)

    # ---- 1. 先查 ChromaDB（持久化缓存）----
    try:
        from memory import MemoryService
        cached = MemoryService().get_summary(key)
        if cached:
            print(f"[上下文] 摘要命中持久化缓存（hash={key[:8]}...）")
            _summary_cache[key] = cached        # 同步到内存缓存
            return cached
    except Exception as e:
        print(f"[上下文] 读取持久化缓存失败: {e}")

    # ---- 2. 查内存缓存 ----
    if key in _summary_cache:
        print(f"[上下文] 摘要命中内存缓存（hash={key[:8]}...）")
        return _summary_cache[key]

    # ---- 3. 生成新摘要 ----
    text = "\n".join(
        f"{m.get('role', '?')}: {m.get('content', '')[:200]}"
        for m in messages
        if m.get("content")
    )

    prompt = (
        "请把下面的对话历史压缩成简洁摘要，保留关键信息"
        "（人物、时间、地点、数据、结论、用户偏好）：\n\n"
        f"{text}\n\n"
        "摘要（不超过 200 字）："
    )

    try:
        client = build_client()
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=HISTORY_SUMMARY_MAX_TOKENS,
        )
        summary = (resp.choices[0].message.content or "").strip()
        print(f"[上下文] 生成新摘要（hash={key[:8]}...）")

        # ---- 4. 双重写缓存 ----
        _summary_cache[key] = summary
        try:
            from memory import MemoryService
            MemoryService().save_summary(key, summary)
        except Exception as e:
            print(f"[上下文] 摘要持久化失败: {e}")

        return summary
    except Exception as e:
        print(f"[上下文] 摘要生成失败: {e}")
        return ""


def trim_history(chat_history_list: list) -> list:
    """
    三级上下文管理：
    1. system prompt（动态时间 + 规则）
    2. 【历史摘要】（中间部分压缩）
    3. 最近 HISTORY_KEEP_LEN 条原始消息

    更早的历史已存 ChromaDB，由 memory_search 工具按需召回（方案 D）。
    """
    if len(chat_history_list) <= HISTORY_MAX_LEN:
        return chat_history_list

    # 拆出 system
    system_prompt = None
    start = 0
    if chat_history_list and chat_history_list[0].get("role") == "system":
        system_prompt = chat_history_list[0]
        start = 1

    # 最近 N 条：原样保留
    recent = chat_history_list[-HISTORY_KEEP_LEN:]

    # 中间部分：压缩成摘要
    middle_end = len(chat_history_list) - HISTORY_KEEP_LEN
    middle = chat_history_list[start:middle_end] if middle_end > start else []

    result = []
    if system_prompt:
        result.append(system_prompt)

    if middle:
        summary = _summarize_history(middle)
        if summary:
            result.append({
                "role": "system",
                "content": f"【历史对话摘要】\n{summary}",
            })

    result.extend(recent)
    return result


def prepare_messages(chat_history_list: list, emotion_hint: str = "") -> list:
    """
    准备发送给模型的消息列表：
    1. 三级上下文管理（滑动窗口 + 摘要压缩）
    2. 刷新 System Prompt 的时间信息
    3. 注入情感提示到最新一条 user 消息
    """
    messages = trim_history(chat_history_list)
    messages = update_history_with_time(messages)

    if emotion_hint and messages and messages[-1].get("role") == "user":
        last = dict(messages[-1])
        last["content"] = last["content"] + emotion_hint
        messages = messages[:-1] + [last]

    return messages


__all__ = [
    "build_client", "trim_history", "prepare_messages", "DEEPSEEK_MODEL",
]