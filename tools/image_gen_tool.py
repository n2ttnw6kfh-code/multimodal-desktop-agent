# ==============================================================================
# 文件名: tools/image_gen_tool.py
# 职责: 把"文生图"注册为 Agent 工具
# ==============================================================================
from .base import register_tool


@register_tool(
    name="generate_image",
    description=(
        "根据文字描述生成图片。"
        "当用户要求'画一张'、'生成图片'、'帮我做个图'时使用。"
        "返回图片保存的本地路径。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "详细的图片描述，越具体越好。建议中英文混合，包含主体、风格、色调。",
            },
        },
        "required": ["prompt"],
    },
)
def generate_image(prompt: str) -> str:
    from ai_service.image_gen import generate_image as _gen
    try:
        path = _gen(prompt)
        return f"图片已生成：{path}\n\n【提示】图片已保存到本地，可以打开查看。"
    except Exception as e:
        return f"图片生成失败: {e}"