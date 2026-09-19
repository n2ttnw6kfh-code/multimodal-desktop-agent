# ==============================================================================
# 文件名: scripts/preview_json.py
# 职责: 预览解析后的 JSON 前几条，验证字段是否正确
# 用法: python -m scripts.preview_json
# ==============================================================================
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = PROJECT_ROOT / "data" / "driving_emotion.json"


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"总数: {len(data)}\n")

    for r in data[:3]:
        print("=" * 50)
        for k, v in r.items():
            print(f"{k:15s}: {v}")
        print()


if __name__ == "__main__":
    main()