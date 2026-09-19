# ==============================================================================
# 文件名: memory/service.py
# 职责: MemoryService 单例门面，组合 ChatMemory + KnowledgeBase
#        - 对话记忆（含上下文摘要）
#        - 知识库（RAG）
# ==============================================================================
from .config import CHROMA_DB_DIR
from .embedding import get_embedding_function
from .chat_memory import ChatMemory
from .knowledge_base import KnowledgeBase


class MemoryService:
    """
    单例式的长期记忆服务。

    三个 collection：
    - chat_memory：对话历史
    - chat_summary：上下文压缩摘要（🆕）
    - knowledge_base：外部知识（RAG）
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = None):
        if getattr(self, "_initialized", False):
            return

        import chromadb
        from chromadb.config import Settings

        if db_path is None:
            db_path = str(CHROMA_DB_DIR)

        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False),
        )

        ef = get_embedding_function()

        self.chat_memory = ChatMemory(self.client, ef)
        self.knowledge_base = KnowledgeBase(self.client, ef)

        self._initialized = True
        print(
            f"[记忆] ChromaDB 已就绪，"
            f"对话 {self.chat_memory.count()} 条，"
            f"摘要 {self.chat_memory.summary_count()} 条，"      # 🆕
            f"知识库 {self.knowledge_base.count()} 条"
        )

    # ==========================================================================
    # 一、对话记忆
    # ==========================================================================
    def add_memory(self, role: str, content: str, extra: dict = None):
        self.chat_memory.add(role, content, extra)

    def search_memory(self, query: str, top_k: int = 5) -> str:
        return self.chat_memory.search(query, top_k)

    def memory_search_tool(self, query: str) -> str:
        return self.chat_memory.search(query, top_k=5)

    def clear_all(self):
        ef = get_embedding_function()
        self.chat_memory.clear(self.client, ef)
        print("[记忆] 对话历史已清空")

    # ==========================================================================
    # 🆕 二、上下文摘要
    # ==========================================================================
    def get_summary(self, history_hash: str) -> str:
        return self.chat_memory.get_summary(history_hash)

    def save_summary(self, history_hash: str, summary: str):
        self.chat_memory.save_summary(history_hash, summary)

    def summary_count(self) -> int:
        return self.chat_memory.summary_count()

    def clear_summaries(self):
        ef = get_embedding_function()
        self.chat_memory.clear_summaries(self.client, ef)
        print("[摘要] 已清空")

    def list_summaries(self, limit: int = 20) -> list:
        return self.chat_memory.list_summaries(limit)

    # ==========================================================================
    # 三、知识库（RAG）
    # ==========================================================================
    def add_document(self, content: str, source: str = "", extra: dict = None):
        self.knowledge_base.add(content, source, extra)

    def search_documents(self, query: str, top_k: int = 5) -> str:
        return self.knowledge_base.search(query, top_k)

    def clear_knowledge(self):
        ef = get_embedding_function()
        self.knowledge_base.clear(self.client, ef)
        print("[知识库] 已清空")

    def knowledge_count(self) -> int:
        return self.knowledge_base.count()