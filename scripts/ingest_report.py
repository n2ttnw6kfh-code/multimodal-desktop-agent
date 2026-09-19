# ==============================================================================
# 文件名: scripts/ingest_report.py
# 职责: 把解析后的车载语音情感报告写入 ChromaDB 知识库
# 用法: python -m scripts.ingest_report
# ==============================================================================
import json
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，方便直接 import memory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from memory import MemoryService


# ---- 路径配置 ----
JSON_PATH = PROJECT_ROOT / "data" / "driving_emotion.json"


def record_to_text(r: dict) -> str:
    """把一条结构化记录拼成一段自然语言（RAG 的检索单元）"""
    return (
        f"场景：{r.get('scene', '未知')}（{r.get('time', '')}）\n"
        f"用户说：{r.get('content', '')}\n"
        f"情绪：{r.get('emotion_type', '')}，强度 {r.get('intensity', '')}/10\n"
        f"声学特征：语速{r.get('speed', '')}，"
        f"语调{r.get('tone', '')}，音量{r.get('volume', '')}\n"
        f"声音特征：{r.get('voice_feature', '')}\n"
        f"分析结论：{r.get('conclusion', '')}"
    )


def ingest():
    if not JSON_PATH.exists():
        print(f"❌ 找不到 {JSON_PATH}，请先运行 parse_report.py")
        return

    records = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"📦 读到 {len(records)} 条记录")

    memory = MemoryService()

    # 🆕 关键：写入知识库前，先清空旧的（避免重复导入）
    # 如果你不想清空，注释掉下面这两行
    # memory.clear_knowledge()
    # print("🧹 已清空旧知识库")

    success = 0
    for r in records:
        try:
            text = record_to_text(r)
            memory.add_document(
                content=text,
                source=f"driving_emotion#{r.get('id', '')}",
                extra={
                    "emotion": r.get("emotion_type", ""),
                    "intensity": _safe_int(r.get("intensity")),
                    "scene": r.get("scene", ""),
                },
            )
            success += 1
        except Exception as e:
            print(f"⚠️ 第 {r.get('id')} 条写入失败: {e}")

    print(f"✅ 成功写入 {success}/{len(records)} 条")
    print(f"📊 知识库当前总条数: {memory.knowledge_count()}")


def _safe_int(v) -> int:
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


if __name__ == "__main__":
    ingest()