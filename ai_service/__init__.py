# ==============================================================================
# 文件名: ai_service/__init__.py
# 职责: 软件包对外出口，保持与原 ai_service.py 相同的公开接口
# ==============================================================================
from .thread_adapter import FetchAIResponseThread, ASRTranscriptionThread
from .llm_client import build_client, prepare_messages, trim_history
from .agent_loop import run_agent_loop, AgentCallbacks
from .asr_service import transcribe

__all__ = [
    "FetchAIResponseThread",
    "ASRTranscriptionThread",
    "build_client",
    "prepare_messages",
    "trim_history",
    "run_agent_loop",
    "AgentCallbacks",
    "transcribe",
]