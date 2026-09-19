# ==============================================================================
# 文件名: memory/knowledge_base.py
# 职责: 知识库的读写（knowledge_base collection），用于 RAG
# ==============================================================================
import uuid


class KnowledgeBase:
    """外部知识库：存放文档，支持语义检索，用于 RAG。"""

    def __init__(self, client, embedding_function):
        from .config import KNOWLEDGE_COLLECTION_NAME, HNSW_SPACE

        self.collection = client.get_or_create_collection(
            name=KNOWLEDGE_COLLECTION_NAME,
            metadata={"hnsw:space": HNSW_SPACE},
            embedding_function=embedding_function,
        )

    # ---- 写入 ----
    def add(self, content: str, source: str = "", extra: dict = None):
        if not content or not content.strip():
            return

        meta = {"source": source, "type": "document"}
        if extra:
            for k, v in extra.items():
                meta[k] = str(v) if not isinstance(v, (str, int, float, bool)) else v

        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[content],
            metadatas=[meta],
        )

    # ---- 检索 ----
    def search(self, query: str, top_k: int = 5) -> str:
        count = self.collection.count()
        if count == 0:
            return "（知识库为空，请先运行 scripts/ingest_report.py 导入数据）"

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=max(1, min(top_k, count)),
            )
        except Exception as e:
            return f"（知识库检索失败: {e}）"

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not docs:
            return "（没有找到相关记录）"

        lines = []
        for doc, meta, dist in zip(docs, metas, distances):
            sim = 1 - dist
            source = meta.get("source", "")
            lines.append(f"- [{source}]（相似度 {sim:.2f}）\n{doc}")

        # 🆕 末尾加约束，让模型看到"不许编"
        footer = (
            "\n\n【重要】以上为知识库全部返回结果，"
            "回答时必须严格引用，禁止编造任何未出现的记录。"
        )
        return "【知识库检索结果】\n\n" + "\n\n".join(lines) + footer

    # ---- 计数 ----
    def count(self) -> int:
        return self.collection.count()

    # ---- 清空 ----
    def clear(self, client, embedding_function):
        from .config import KNOWLEDGE_COLLECTION_NAME, HNSW_SPACE

        client.delete_collection(KNOWLEDGE_COLLECTION_NAME)
        self.collection = client.get_or_create_collection(
            name=KNOWLEDGE_COLLECTION_NAME,
            metadata={"hnsw:space": HNSW_SPACE},
            embedding_function=embedding_function,
        )