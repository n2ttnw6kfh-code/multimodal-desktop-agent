# ==============================================================================
# 文件名: ai_service/config.py
# 职责: 加载 .env、集中管理 API Key 与模型参数
# ==============================================================================
import os
from pathlib import Path
from dotenv import load_dotenv

# ---- 定位项目根目录 ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

if not ENV_FILE_PATH.exists():
    raise FileNotFoundError(f"❌ 找不到 .env 文件: {ENV_FILE_PATH}")

load_dotenv(dotenv_path=str(ENV_FILE_PATH), override=True)

# ---- API Keys ----
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not DEEPSEEK_API_KEY:
    raise ValueError("❌ .env 文件中未找到 DEEPSEEK_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("❌ .env 文件中未找到 TAVILY_API_KEY")

# ---- 模型参数 ----
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", "60.0"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.5"))

# ---- Agent 参数 ----
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "5"))

# ===== 上下文管理 =====
HISTORY_MAX_LEN = int(os.getenv("HISTORY_MAX_LEN", "12"))         # 超过就触发压缩
HISTORY_KEEP_LEN = int(os.getenv("HISTORY_KEEP_LEN", "6"))       # 最近保留原始条数
HISTORY_SUMMARY_MAX_TOKENS = int(os.getenv("HISTORY_SUMMARY_MAX_TOKENS", "300"))

# ---- 本地模型路径 ----
WHISPER_MODEL_DIR = PROJECT_ROOT / "whisper_tiny_local"