# ==============================================================================
# 文件名: ai_service/agent_loop.py
# 职责: ReAct 循环 + 原生流式解析 + 工具调用累积
# 说明: 纯逻辑，不依赖 PyQt；通过 callbacks 与 ui 层通信
# ==============================================================================
from typing import Callable, Optional

from .config import DEEPSEEK_MODEL, DEFAULT_TEMPERATURE, MAX_AGENT_ITERATIONS
from tools import build_tools_schema, ToolExecutor
from langsmith import traceable

class AgentCallbacks:
    """ui 层注入的回调集合（替代 pyqtSignal，让本模块保持纯逻辑）"""
    def __init__(
        self,
        on_stream_started: Optional[Callable[[], None]] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_stream_finished: Optional[Callable[[], None]] = None,
        is_interrupted: Optional[Callable[[], bool]] = None,
    ):
        self.on_stream_started = on_stream_started or (lambda: None)
        self.on_chunk = on_chunk or (lambda _: None)
        self.on_stream_finished = on_stream_finished or (lambda: None)
        self.is_interrupted = is_interrupted or (lambda: False)


def _accumulate_tool_calls(accumulated: dict, delta_tool_calls):
    """把跨 chunk 的 tool_calls 增量合并进 accumulated"""
    for tc in delta_tool_calls:
        idx = tc.index
        if idx not in accumulated:
            accumulated[idx] = {
                "id": tc.id or "",
                "function": {"name": "", "arguments": ""},
            }
        if tc.id:
            accumulated[idx]["id"] = tc.id
        if tc.function:
            if tc.function.name:
                accumulated[idx]["function"]["name"] += tc.function.name
            if tc.function.arguments:
                accumulated[idx]["function"]["arguments"] += tc.function.arguments


def _to_tool_calls_list(accumulated: dict) -> list:
    """把 dict 形式的累积结果转成 OpenAI 格式的 list"""
    result = []
    for idx in sorted(accumulated.keys()):
        tc = accumulated[idx]
        result.append({
            "id": tc["id"],
            "type": "function",
            "function": {
                "name": tc["function"]["name"],
                "arguments": tc["function"]["arguments"],
            },
        })
    return result

@traceable(name="agent_loop", run_type="chain")
def run_agent_loop(
    client,
    messages: list,
    tool_executor: ToolExecutor,
    callbacks: AgentCallbacks,
) -> str:
    """
    ReAct 循环（真流式）：
    - stream=True 逐 chunk 发射 content
    - 累积 tool_calls，执行后拼回 messages
    - 直到模型不再调用工具，返回最终文本
    """
    tools_schema = build_tools_schema()
    callbacks.on_stream_started()

    try:
        for iteration in range(MAX_AGENT_ITERATIONS):
            if callbacks.is_interrupted():
                print("[Agent] 用户请求中断")
                return ""

            print(f"[Agent] 第 {iteration + 1} 轮推理")

            stream = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto",
                temperature=DEFAULT_TEMPERATURE,
                stream=True,
            )

            accumulated_content = []
            accumulated_tool_calls = {}

            for chunk in stream:
                if callbacks.is_interrupted():
                    return ""

                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if delta.content:
                    accumulated_content.append(delta.content)
                    callbacks.on_chunk(delta.content)

                if delta.tool_calls:
                    _accumulate_tool_calls(accumulated_tool_calls, delta.tool_calls)

            # ---- 有工具调用 → 执行后继续下一轮 ----
            if accumulated_tool_calls:
                tool_calls_list = _to_tool_calls_list(accumulated_tool_calls)

                messages.append({
                    "role": "assistant",
                    "content": "".join(accumulated_content),
                    "tool_calls": tool_calls_list,
                })

                print(f"[Agent] 本轮调用 {len(tool_calls_list)} 个工具")
                for tc in tool_calls_list:
                    # 🆕 中断时不再 break，而是补齐一条 tool 响应
                    if callbacks.is_interrupted():
                        messages.append({
                            "tool_call_id": tc["id"],
                            "role": "tool",
                            "name": tc["function"]["name"],
                            "content": "（用户中断，未执行）",
                        })
                        continue

                    try:
                        result = tool_executor.execute(
                            tc["function"]["name"], tc["function"]["arguments"]
                        )
                    except Exception as e:
                        result = f"工具执行异常: {e}"

                    # 🆕 兜底：确保 content 一定是 str
                    if not isinstance(result, str):
                        result = str(result)

                    messages.append({
                        "tool_call_id": tc["id"],
                        "role": "tool",
                        "name": tc["function"]["name"],
                        "content": result,
                    })
                continue

            # ---- 无工具调用 → 结束 ----
            full_reply = "".join(accumulated_content)
            print("[Agent] 无工具调用，输出最终回答")
            messages.append({"role": "assistant", "content": full_reply})
            return full_reply

        # ---- 达到最大轮数兜底 ----
        print(f"[Agent] 达到最大轮数 {MAX_AGENT_ITERATIONS}，强制输出")
        try:
            final = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                temperature=DEFAULT_TEMPERATURE,
            )
            full_reply = final.choices[0].message.content or ""
            if full_reply:
                callbacks.on_chunk(full_reply)
            messages.append({"role": "assistant", "content": full_reply})
            return full_reply
        except Exception as e:
            return f"（Agent 循环达到上限，且兜底请求失败：{e}）"

    except Exception as e:
        print(f"[Agent] 循环异常: {e}")
        return f"（Agent 循环异常: {e}）"
    finally:
        callbacks.on_stream_finished()