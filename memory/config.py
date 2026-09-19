# ==============================================================================
# 文件名: memory/config.py
# 职责: 记忆模块的路径与常量集中管理
# ==============================================================================
import os
from pathlib import Path

# ---- 项目根目录（memory 的上一级）----
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---- ChromaDB 持久化目录 ----
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_memory"

# ---- 本地 embedding 模型目录 ----
# 中文语义检索质量高（英文模型 all-MiniLM-L6-v2 不要用于中文）
EMBEDDING_MODEL_DIR = Path(r"D:\python\models\bge-small-zh-v1.5")

# ---- collection 名称 ----
CHAT_COLLECTION_NAME = "chat_memory"
KNOWLEDGE_COLLECTION_NAME = "knowledge_base"
SUMMARY_COLLECTION_NAME = "chat_summary"       # 🆕 上下文摘要专用

# ---- 相似度空间 ----
HNSW_SPACE = "cosine"

# ---- 文本截断长度（防止长文本撑爆显存/内存）----
MAX_SEQ_LENGTH = 256

# ---- ChromaDB 遥测开关 ----
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "False")