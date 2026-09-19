# ==============================================================================
# 文件名: scripts/test_search.py
# 职责: 测试知识库检索效果
# ==============================================================================
from memory import MemoryService

m = MemoryService()

queries = [
    "堵车 愤怒",
    "疲劳 深夜开车",
    "商务出差 焦虑",
    "情绪强度最高的情况",
    "节假日出行 烦躁",
]

for q in queries:
    print("=" * 70)
    print(f"🔍 查询: {q}")
    print("=" * 70)
    print(m.search_documents(q, top_k=2))
    print()