# ==============================================================================
# 文件名: scripts/parse_report.py
# 职责: 把 Word 报告解析成结构化 JSON
# 用法: python -m scripts.parse_report
# ==============================================================================
import json
from pathlib import Path
from docx import Document

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCX_PATH = PROJECT_ROOT / "data" / "车载语音情感分析报告_200条记录.docx"
JSON_PATH = PROJECT_ROOT / "data" / "driving_emotion.json"


def parse():
    doc = Document(DOCX_PATH)
    records = []

    # 遍历所有表格
    for table in doc.tables:
        rows = table.rows
        for row in rows[1:]:   # 跳过表头
            cells = [c.text.strip() for c in row.cells]
            if len(cells) < 12 or not cells[0]:
                continue
            records.append({
                "id": cells[0],
                "content": cells[1],
                "emotion_type": cells[2],
                "intensity": cells[3],
                "speed": cells[4],
                "tone": cells[5],
                "volume": cells[6],
                "voice_feature": cells[7],
                "scene": cells[8],
                "time": cells[9],
                "confidence": cells[10],
                "conclusion": cells[11],
            })

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✅ 解析完成，写入 {len(records)} 条到 {JSON_PATH}")


if __name__ == "__main__":
    parse()