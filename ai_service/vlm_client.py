# ==============================================================================
# 文件名: ai_service/vlm_client.py
# 职责: 调用通义千问 VL 理解图片（图片 → 文字描述）
# ==============================================================================
import base64
import os
from pathlib import Path

from openai import OpenAI


# 阿里云百炼 OpenAI 兼容接口
VLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
VLM_MODEL = "qwen-vl-max"


def _compress_image(image_path: str, max_size: int = 1024) -> str:
    """
    压缩图片，避免超过 API 大小限制。
    返回压缩后的路径（如果原图小，直接返回原路径）。
    """
    try:
        from PIL import Image
    except ImportError:
        return image_path

    img = Image.open(image_path)

    # 转 RGB（处理 RGBA / P 模式）
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # 超过 max_size 就缩放
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        new_path = str(Path(image_path).with_suffix(".compressed.jpg"))
        img.save(new_path, "JPEG", quality=85)
        return new_path

    return image_path


def describe_image(image_path: str, question: str = "") -> str:
    """
    用 VLM 理解图片。

    Args:
        image_path: 图片路径
        question:   用户对图片的问题（可为空，默认"描述这张图片"）

    Returns:
        图片描述或问题答案

    Raises:
        FileNotFoundError: 图片不存在
        RuntimeError: API Key 缺失或调用失败
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY，请在 .env 中配置")

    # 压缩图片
    compressed = _compress_image(image_path)

    # 转 base64
    with open(compressed, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    # 猜 MIME
    ext = Path(compressed).suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")

    client = OpenAI(api_key=api_key, base_url=VLM_BASE_URL)

    prompt = question or "请详细描述这张图片的内容，包括主要物体、文字、场景。"

    messages = [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            },
            {"type": "text", "text": prompt},
        ],
    }]

    try:
        resp = client.chat.completions.create(
            model=VLM_MODEL,
            messages=messages,
            timeout=60,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"VLM 调用失败: {e}")