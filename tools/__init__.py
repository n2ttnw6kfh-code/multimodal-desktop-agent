# ==============================================================================
# 文件名: tools/__init__.py
# 职责: 导入所有工具模块，让 @register_tool 装饰器生效
# ==============================================================================
from .base import register_tool, build_tools_schema, ToolExecutor

# ⚠️ 必须导入每个工具模块，否则装饰器不会执行
from . import web_search     # noqa: F401
from . import weather        # noqa: F401
from . import calculator     # noqa: F401
from . import time_tool      # noqa: F401
from . import memory_tool         # noqa: F401
from . import read_url
from . import stock
from . import translate   # noqa: F401
from . import mcp_map
from . import emotion_kb   # noqa: F401
from . import mcp_fetch   # noqa: F401
from . import image_gen_tool   # noqa: F401

__all__ = ["register_tool", "build_tools_schema", "ToolExecutor"]