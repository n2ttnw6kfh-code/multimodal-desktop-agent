# ==============================================================================
# 文件名: memory/chat_memory.py
# 职责: 对话记忆 + 上下文摘要的读写
#        - chat_memory：对话历史（每轮写入）
#        - chat_summary：上下文摘要（压缩产物，按 hash 存取）
# ==============================================================================
import datetime
import uuid


class ChatMemory:
    """
    对话记忆：
    - 每轮对话写入 chat_memory collection
    - 支持语义检索历史
    - 🆕 存储上下文压缩摘要（chat_summary collection）
    """

    def __init__(self, client, embedding_function):
        from .config import (
            CHAT_COLLECTION_NAME,
            SUMMARY_COLLECTION_NAME,
            HNSW_SPACE,
        )

        self.collection = client.get_or_create_collection(
            name=CHAT_COLLECTION_NAME,
            metadata={"hnsw:space": HNSW_SPACE},
            embedding_function=embedding_function,
        )

        # 🆕 摘要 collection（key-value 存取，不做向量检索）
        self.summary_collection = client.get_or_create_collection(
            name=SUMMARY_COLLECTION_NAME,
            metadata={"hnsw:space": HNSW_SPACE},
            embedding_function=embedding_function,
        )

    # ==========================================================================
    # 一、对话历史
    # ==========================================================================
    def add(self, role: str, content: str, extra: dict = None):
        """写入一条对话"""
        if not content or not content.strip():
            return

        now = datetime.datetime.now().isoformat()
        meta = {"role": role, "timestamp": now}
        if extra:
            for k, v in extra.items():
                meta[k] = str(v) if not isinstance(v, (str, int, float, bool)) else v

        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[content],
            metadatas=[meta],
        )

    def search(self, query: str, top_k: int = 5) -> str:
        """语义检索对话历史"""
        count = self.collection.count()
        if count == 0:
            return "（记忆库为空，这是你们的第一轮对话）"

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=max(1, min(top_k, count)),
            )
        except Exception as e:
            return f"（记忆检索失败: {e}）"

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not docs:
            return "（没有找到相关记忆）"

        lines = []
        for doc, meta, dist in zip(docs, metas, distances):
            role = meta.get("role", "?")
            ts = meta.get("timestamp", "")[:19]
            emotion = meta.get("emotion", "")
            emo_str = f" [情绪:{emotion}]" if emotion else ""
            sim = 1 - dist
            lines.append(f"- ({ts}) {role}{emo_str}: {doc}  [相似度 {sim:.2f}]")

        return "【相关历史记忆】\n" + "\n".join(lines)

    def count(self) -> int:
        return self.collection.count()

    def clear(self, client, embedding_function):
        """清空对话历史"""
        from .config import CHAT_COLLECTION_NAME, HNSW_SPACE
        client.delete_collection(CHAT_COLLECTION_NAME)
        self.collection = client.get_or_create_collection(
            name=CHAT_COLLECTION_NAME,
            metadata={"hnsw:space": HNSW_SPACE},
            embedding_function=embedding_function,
        )

    # ==========================================================================
    # 二、🆕 上下文摘要
    # ==========================================================================
    def get_summary(self, history_hash: str) -> str:
        """
        按 hash 取摘要。
        返回空字符串表示没有缓存。
        """
        if not history_hash:
            return ""
        try:
            res = self.summary_collection.get(ids=[history_hash])
            docs = res.get("documents", [])
            return docs[0] if docs else ""
        except Exception as e:
            print(f"[摘要] 读取失败: {e}")
            return ""

    def save_summary(self, history_hash: str, summary: str):
        """
        按 hash 存摘要。
        - 幂等：已存在则先删后写
        - 空摘要不写
        """
        if not summary or not history_hash:
            return

        try:
            # 先删旧的（避免重复 id 报错）
            try:
                self.summary_collection.delete(ids=[history_hash])
            except Exception:
                pass

            self.summary_collection.add(
                ids=[history_hash],
                documents=[summary],
                metadatas=[{
                    "type": "summary",
                    "created_at": datetime.datetime.now().isoformat(),
                }],
            )
        except Exception as e:
            print(f"[摘要] 保存失败: {e}")

    def summary_count(self) -> int:
        return self.summary_collection.count()

    def clear_summaries(self, client, embedding_function):
        """清空所有摘要"""
        from .config import SUMMARY_COLLECTION_NAME, HNSW_SPACE
        client.delete_collection(SUMMARY_COLLECTION_NAME)
        self.summary_collection = client.get_or_create_collection(
            name=SUMMARY_COLLECTION_NAME,
            metadata={"hnsw:space": HNSW_SPACE},
            embedding_function=embedding_function,
        )

    def list_summaries(self, limit: int = 20) -> list:
        """列出摘要（调试用）"""
        try:
            res = self.summary_collection.get()
            ids = res.get("ids", [])
            docs = res.get("documents", [])
            return list(zip(ids[:limit], docs[:limit]))
        except Exception:
            return []