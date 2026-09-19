# scripts/preview_summary.py
from memory import MemoryService

m = MemoryService()
summaries = m.list_summaries(limit=10)
print(f"共 {len(summaries)} 条摘要\n")

for i, (sid, content) in enumerate(summaries, 1):
    print(f"--- 摘要 {i} ---")
    print(f"hash: {sid[:16]}...")
    print(f"内容: {content}")
    print()