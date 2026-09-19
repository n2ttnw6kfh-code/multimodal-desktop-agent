# 🤖 AI 语音助手

一个基于 **PyQt6 + DeepSeek + 本地 Whisper + 情感识别 + ChromaDB 长期记忆** 的桌面智能助手。

支持 **语音输入 → 情感识别 → Agent 工具调用 → 流式输出** 的完整链路，具备联网搜索、天气查询、数学计算、记忆检索等能力。

---

## ✨ 功能特性

### 🎤 语音交互
- 本地 **Faster-Whisper** 语音识别（16kHz，中文优化）
- 无需联网，模型加载后全局缓存
- 录音按钮带呼吸动画，状态一目了然

### 🧠 情感识别
- 本地中文情感分类模型（Transformers）
- 7 类情感标签：`positive / negative / neutral / angry / sad / anxious / happy`
- 自动注入情感提示词，让 AI 根据用户情绪调整语气

### 🛠️ Agent 工具调用（ReAct 循环）
- **联网搜索**（Tavily）：实时新闻、比赛、股价、事件
- **天气查询**（wttr.in）：实时天气 + 未来三天预报
- **数学计算**（AST 安全求值，防注入）
- **时间查询**：当前日期、时间、星期
- **记忆检索**：从长期记忆中找回相关历史

### 💾 长期记忆
- 基于 **ChromaDB** 向量数据库持久化
- 每轮对话自动写入，支持语义检索
- 独立存储目录 `chroma_memory/`

### 🎨 现代化 UI
- QSS 样式表 + 聊天气泡（用户蓝 / AI 绿 / 系统灰）
- 输入框聚焦发光（`QGraphicsDropShadowEffect`）
- 语音按钮脉冲呼吸（`QPropertyAnimation`）
- 流式打字机效果

### ⚡ 流式输出
- 逐 chunk 渲染，无需等待完整回复
- 支持中途打断（`requestInterruption`）

---

## 📁 项目结构

```
AI语音助手/
├── main.py                     # 🎯 程序唯一入口
├── .env                        # 🔑 API Key 配置（需自建）
│
├── ai_service/                 # AI 服务层
│   ├── __init__.py
│   ├── config.py               # API Key / 模型参数集中管理
│   ├── llm_client.py           # DeepSeek client、历史裁剪
│   ├── agent_loop.py           # ReAct 循环 + 流式解析
│   ├── thread_adapter.py       # QThread 适配层
│   └── asr_service.py          # Whisper 语音识别（模型缓存）
│
├── audio/                      # 音频采集
│   ├── __init__.py
│   ├── config.py               # 采样率 / 声道 / 缓冲区
│   └── recorder.py             # PyAudio 录音线程
│
├── emotion/                    # 情感识别
│   ├── __init__.py
│   ├── config.py               # 标签映射 / 模型路径 / 阈值
│   ├── label_utils.py          # 标签归一化（纯函数）
│   ├── model_loader.py         # 线程安全模型缓存
│   ├── recognizer.py           # 识别纯逻辑
│   └── thread.py               # QThread 适配层
│
├── memory/                     # 长期记忆
│   ├── __init__.py
│   └── service.py              # ChromaDB 存储与检索
│
├── prompt/                     # 提示词管理
│   ├── __init__.py
│   └── manager.py              # 动态系统提示词 / 情感提示
│
├── tools/                      # Agent 工具集
│   ├── __init__.py             # 触发 @register_tool
│   ├── base.py                 # 注册中心 + ToolExecutor
│   ├── web_search.py           # 联网搜索
│   ├── weather.py              # 天气查询
│   ├── calculator.py           # 数学计算
│   ├── time_tool.py            # 时间查询
│   └── memory_tool.py          # 记忆检索
│
├── ui/                         # UI 层
│   ├── __init__.py
│   ├── main_window.py          # 主窗口
│   ├── styles.py               # QSS 样式表
│   ├── widgets.py              # 自定义控件
│   └── chat_view.py            # 聊天气泡渲染
│
├── emotion_model/              # 情感模型目录（需自行放置）
├── whisper_tiny_local/         # Whisper 模型目录（需自行放置）
└── chroma_memory/              # 长期记忆数据库（自动生成）
```

---

## 🚀 快速开始

### 1. 环境要求

- **Python** ≥ 3.10
- **操作系统**：Windows / macOS / Linux
- **麦克风**（语音功能需要）

### 2. 安装依赖

```bash
pip install PyQt6 openai python-dotenv requests pyaudio
pip install faster-whisper transformers torch
pip install chromadb tavily-python
```

或使用 `requirements.txt`：

```bash
pip install -r requirements.txt
```

### 3. 准备本地模型

在项目根目录创建以下目录并放置模型文件：

#### `whisper_tiny_local/` — Whisper 语音识别模型

从 HuggingFace 下载 `Systran/faster-whisper-tiny` 的全部文件放入该目录：

```bash
# 方式一：huggingface-cli
huggingface-cli download Systran/faster-whisper-tiny --local-dir whisper_tiny_local

# 方式二：git clone（需 git-lfs）
git clone https://huggingface.co/Systran/faster-whisper-tiny whisper_tiny_local
```

#### `emotion_model/` — 中文情感分类模型

任选一个中文情感模型（如 `uer/roberta-base-finetuned-jd-binary-chinese`）：

```bash
huggingface-cli download uer/roberta-base-finetuned-jd-binary-chinese --local-dir emotion_model
```

> 💡 **提示**：模型目录里应有 `config.json`、`pytorch_model.bin`（或 `model.safetensors`）、`vocab.txt` 等文件。

### 4. 配置 API Key

在项目根目录创建 `.env` 文件：

```env
# ===== 必填 =====
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxx

# ===== 可选（有默认值）=====
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60.0
DEFAULT_TEMPERATURE=0.5

MAX_AGENT_ITERATIONS=5
HISTORY_MAX_LEN=12
HISTORY_KEEP_LEN=10

EMOTION_MIN_CONFIDENCE=0.6
EMOTION_MAX_LENGTH=128

AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK=1024
```

**获取 API Key**：
- DeepSeek：https://platform.deepseek.com/
- Tavily：https://tavily.com/

### 5. 启动

```bash
python main.py
```

---

## 💡 使用说明

| 操作 | 说明 |
|---|---|
| **文字输入** | 在输入框输入问题，按回车或点击"发送" |
| **语音输入** | 点击"🎤 语音"开始录音，再点一次停止，自动识别并发送 |
| **中断回复** | 关闭窗口会自动中断所有后台线程 |
| **查看情绪** | 聊天区会显示 `[情绪识别] 😊 positive（置信度 85%）` |

### 典型对话示例

```
用户：马鞍山今天天气怎么样？
AI：[调用 get_weather] 马鞍山今天晴，18~26°C...

用户：帮我算一下 (25 + 37) * 3
AI：[调用 calculate] 计算结果：(25 + 37) * 3 = 186

用户：我上次说想去哪旅游？
AI：[调用 memory_search] 根据历史记忆，你之前提到过想去云南...
```

---

## 🏗️ 架构设计

### 分层原则

```
┌─────────────────────────────────────┐
│  ui/          ← 界面与交互          │
├─────────────────────────────────────┤
│  ai_service/  ← AI 逻辑（纯逻辑）   │
│  audio/       ← 音频采集            │
│  emotion/     ← 情感识别（纯逻辑）  │
│  memory/      ← 长期记忆            │
│  prompt/      ← 提示词管理          │
│  tools/       ← Agent 工具          │
└─────────────────────────────────────┘
```

**核心设计**：
- **纯逻辑层不依赖 PyQt**：`agent_loop.py`、`recognizer.py`、`service.py` 都是纯 Python，可单独测试、可复用
- **QThread 适配层单独放置**：`thread_adapter.py`、`emotion/thread.py`、`audio/recorder.py` 只负责信号发射
- **工具自动注册**：`@register_tool` 装饰器 + `tools/__init__.py` 显式导入，新增工具零侵入

### 数据流

```
用户输入（文字 / 语音）
        │
        ▼
   [情感识别线程] ──→ 情绪标签 + 置信度
        │
        ▼
   [构建消息] ──→ 注入情感提示 + 动态时间
        │
        ▼
   [Agent 线程]
        │
        ├─→ 流式输出 chunk ──→ UI 打字机
        │
        └─→ 工具调用 ──→ 搜索 / 天气 / 计算 / 记忆
                │
                ▼
           结果拼回 messages，继续下一轮
        │
        ▼
   最终回复 → 写入 ChromaDB 长期记忆
```

---

## 🔧 扩展指南

### 新增一个 Agent 工具

在 `tools/` 下新建文件，例如 `tools/translate.py`：

```python
from .base import register_tool


@register_tool(
    name="translate",
    description="把文本翻译成指定语言。",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "要翻译的文本"},
            "target": {"type": "string", "description": "目标语言"},
        },
        "required": ["text", "target"],
    },
)
def translate(text: str, target: str) -> str:
    # 实现翻译逻辑
    return f"翻译结果：..."
```

然后在 `tools/__init__.py` 里加一行：

```python
from . import translate   # noqa: F401
```

**完成**，Agent 会自动发现这个工具。

### 📚 私有知识库（RAG）
- 基于 ChromaDB + 本地中文 embedding（BAAI/bge-small-zh-v1.5）
- 支持导入 Word/文档，自动切分并向量化
- Agent 可主动检索知识库，严格引用原文
- 当前已导入：200 条车载语音情感分析报告


### 更换 LLM

修改 `.env`：

```env
DEEPSEEK_BASE_URL=https://api.openai.com/v1
DEEPSEEK_MODEL=gpt-4o-mini
DEEPSEEK_API_KEY=sk-xxx
```

因为用的是 OpenAI 兼容接口，理论上任何兼容 OpenAI 协议的服务都能直接换。

---

## ⚠️ 常见问题

### 1. `ModuleNotFoundError: No module named 'memory'`

包改名后 import 未同步。检查所有 `from memory_service import ...` 是否改成了 `from memory import ...`。

### 2. `找不到 .env 文件`

在项目根目录创建 `.env` 并填入 `DEEPSEEK_API_KEY` 和 `TAVILY_API_KEY`。

### 3. `找不到 Whisper 模型目录`

确认 `whisper_tiny_local/` 在项目根目录，且里面有 `model.bin`、`config.json`、`tokenizer.json` 等文件。

### 4. `找不到本地模型目录: emotion_model`

确认 `emotion_model/` 在项目根目录，且包含 `config.json`、`pytorch_model.bin` 等。

### 5. 录音没声音 / 报错

- 检查麦克风权限
- Windows 下可能需要以管理员运行
- 确认 `pyaudio` 已正确安装（`pip install pyaudio`，若失败尝试 `pipwin install pyaudio`）

### 6. 情感识别总是返回 `neutral`

- 检查 `EMOTION_MIN_CONFIDENCE`（默认 0.6），可调低到 0.5
- 检查模型 `id2label` 是否正确（见 `emotion/label_utils.py`）

### 7. 记忆库清空

```python
from memory import MemoryService
MemoryService().clear_all()
```

或直接删除 `chroma_memory/` 目录。

---

## 📦 依赖清单

| 包 | 用途 |
|---|---|
| `PyQt6` | GUI 框架 |
| `openai` | DeepSeek API 客户端（OpenAI 兼容） |
| `python-dotenv` | `.env` 加载 |
| `requests` | HTTP 请求（天气、搜索） |
| `pyaudio` | 麦克风采集 |
| `faster-whisper` | 语音识别 |
| `transformers` + `torch` | 情感识别模型 |
| `chromadb` | 向量数据库 |
| `tavily-python`（可选） | 联网搜索 |

---

## 🎯 设计亮点

- ✅ **纯逻辑层无 PyQt 依赖**，可单测、可复用
- ✅ **模型全局缓存 + 双检锁**，避免重复加载
- ✅ **流式输出 + 中断支持**，用户体验流畅
- ✅ **工具自动注册机制**，新增工具零侵入
- ✅ **情感识别 + 长期记忆**，让 AI 更"懂你"
- ✅ **QSS + QPropertyAnimation** 实现现代化 UI，绕过 QSS 局限

---

## 📄 License

MIT License

---

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) — LLM 服务
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) — 语音识别
- [ChromaDB](https://www.trychroma.com/) — 向量数据库
- [Tavily](https://tavily.com/) — 联网搜索
- [wttr.in](https://wttr.in/) — 天气数据
