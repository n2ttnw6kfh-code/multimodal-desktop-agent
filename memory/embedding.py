# ==============================================================================
# 文件名: memory/embedding.py
# 职责: 自定义本地 EmbeddingFunction（绕开 sentence-transformers 版本坑）
# ==============================================================================
import threading
from typing import List

from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

from .config import EMBEDDING_MODEL_DIR, MAX_SEQ_LENGTH


class LocalTransformerEF(EmbeddingFunction):
    """
    用 transformers + torch 直接加载本地模型的 EmbeddingFunction。

    ChromaDB 新版要求实现：
    - __call__(input)        ：通用入口
    - embed_query(input)     ：查询时调用
    - embed_documents(input) ：写入时调用
    - name()                 ：唯一标识（用于持久化配置对比）
    """

    def __init__(self, model_dir: str):
        import torch
        from transformers import AutoTokenizer, AutoModel

        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModel.from_pretrained(model_dir)
        self.model.eval()
        self._model_dir = model_dir

    # ---- 核心编码 ----
    def _encode(self, input) -> List[List[float]]:
        if isinstance(input, str):
            input = [input]

        inputs = self.tokenizer(
            list(input),
            padding=True,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            return_tensors="pt",
        )
        with self._torch.no_grad():
            outputs = self.model(**inputs)
            mask = inputs["attention_mask"].unsqueeze(-1).expand(
                outputs.last_hidden_state.size()
            ).float()
            summed = self._torch.sum(outputs.last_hidden_state * mask, 1)
            counts = self._torch.clamp(mask.sum(1), min=1e-9)
            embeddings = (summed / counts).numpy()

        # L2 归一化
        norms = (embeddings ** 2).sum(axis=1, keepdims=True) ** 0.5
        embeddings = embeddings / (norms + 1e-9)
        return embeddings.tolist()

    # ---- 三个入口 ----
    def __call__(self, input) -> List[List[float]]:
        return self._encode(input)

    def embed_query(self, input) -> List[List[float]]:
        return self._encode(input)

    def embed_documents(self, input) -> List[List[float]]:
        return self._encode(input)

    @staticmethod
    def name() -> str:
        return "local-transformer"


# ==============================================================================
# 全局单例（双检锁）
# ==============================================================================
_ef_instance = None
_ef_lock = threading.Lock()


def get_embedding_function():
    global _ef_instance
    if _ef_instance is not None:
        return _ef_instance

    with _ef_lock:
        if _ef_instance is not None:
            return _ef_instance

        if (EMBEDDING_MODEL_DIR / "config.json").exists():
            _ef_instance = LocalTransformerEF(str(EMBEDDING_MODEL_DIR))
            print(f"[记忆] ✅ 使用自定义本地 embedding: {EMBEDDING_MODEL_DIR}")
        else:
            from chromadb.utils import embedding_functions
            _ef_instance = embedding_functions.DefaultEmbeddingFunction()
            print(
                f"[记忆] ⚠️ 未找到本地模型 {EMBEDDING_MODEL_DIR}，"
                f"回退默认 embedding（中文效果差）"
            )

        return _ef_instance