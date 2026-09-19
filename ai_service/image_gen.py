# ==============================================================================
# 文件名: ai_service/image_gen.py
# 职责: 调用通义万相生成图片（文字 → 图片）
# ==============================================================================
import os
import time
import uuid
from pathlib import Path

import requests


API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
GEN_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

# 生成的图片保存目录
IMAGE_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "generated_images"


def generate_image(prompt: str, size: str = "1024*1024") -> str:
    """
    文生图。

    Args:
        prompt: 图片描述
        size:   尺寸，如 "1024*1024"

    Returns:
        本地图片路径

    Raises:
        RuntimeError: 生成失败
    """
    if not API_KEY:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY")

    # 1. 提交任务
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": "wanx-v1",
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": 1},
    }

    resp = requests.post(GEN_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"提交失败: {resp.text}")

    task_id = resp.json().get("output", {}).get("task_id")
    if not task_id:
        raise RuntimeError(f"未拿到 task_id: {resp.text}")

    # 2. 轮询结果
    for _ in range(60):   # 最多等 60 秒
        time.sleep(2)
        r = requests.get(TASK_URL.format(task_id=task_id), headers=headers, timeout=10)
        data = r.json()
        status = data.get("output", {}).get("task_status")

        if status == "SUCCEEDED":
            results = data["output"].get("results", [])
            if not results:
                raise RuntimeError("任务成功但无结果")
            image_url = results[0]["url"]

            # 3. 下载到本地
            IMAGE_OUTPUT_DIR.mkdir(exist_ok=True)
            local_path = IMAGE_OUTPUT_DIR / f"{uuid.uuid4().hex[:8]}.png"
            img_resp = requests.get(image_url, timeout=60)
            local_path.write_bytes(img_resp.content)
            return str(local_path)

        if status == "FAILED":
            raise RuntimeError(f"生成失败: {data}")

    raise RuntimeError("生成超时")