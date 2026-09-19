# 🤖 多模态智能体桌面助手

> **Multimodal Desktop Agent with Agentic RAG & Context Compression**

一个多模态桌面智能体，实现 **语音 / 文字 / 图片输入 → 情感识别 → ReAct Agent → 上下文压缩 → 流式输出 → 语音播报** 的完整闭环。

集成 **19 个 Agent 工具**（5 类）、**Agentic RAG 私有知识库**、**高德地图 MCP**、**三级上下文 + 三级缓存**、**LangSmith 全链路可观测**。

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![LangSmith](https://img.shields.io/badge/Observability-LangSmith-purple)](https://smith.langchain.com/)

---

## ✨ 功能特性

### 🎤 多模态输入
- **文字**：直接对话
- **语音**：本地 **Faster-Whisper** 识别（16kHz，中文优化，模型全局缓存）
- **图片**：**通义千问 VL** 理解（UI 层前置处理为文字描述）

### 🔊 多模态输出
- **流式文字**：逐 chunk 渲染，打字机效果
- **语音播报**：**Edge-TTS**（微软免费服务），5 种中文音色，可一键开关
- **文生图**：**通义万相**，注册为 Agent 工具，生成后自动打开

### 🧠 情感识别
- 本地中文情感分类模型（Transformers）
- 7 类情感标签：`positive / negative / neutral / angry / sad / anxious / happy`
- 识别结果注入提示词，让 AI 根据用户情绪调整语气

### 🤖 自研 ReAct Agent
- 基于 **DeepSeek 原生 `tool_calls`** 实现流式推理与工具调用
- 解决 `delta.tool_calls` **跨 chunk 分片传输**的累积合并问题
- 支持**真流式输出**与**用户随时中断**
- 通过 `AgentCallbacks` 回调抽象，**逻辑层完全不依赖 PyQt**，可单独测试

### 🛠️ 5 类共 19 个 Agent 工具
| 类别 | 工具 |
|---|---|
| **信息获取** | `search_tavily`（联网）、`get_weather`（天气） |
| **计算与逻辑** | `calculate`（AST 安全计算）、`get_current_time` |
| **记忆与知识** | `memory_search`（对话检索）、`search_driving_emotion`（RAG 知识库） |
| **地图服务** | **高德地图 MCP**（12 个工具：搜索 / 路线 / 地理编码 / 天气等） |
| **多模态生成** | `generate_image`（文生图） |

### 📚 Agentic RAG 私有知识库
- **把知识库检索注册为 Agent 工具**，由 Agent 自主决定是否调用
- 自研 `EmbeddingFunction`（`transformers + torch`），绕开 `sentence-transformers` 版本坑
- 中文专用模型 `BAAI/bge-small-zh-v1.5`，检索准确率显著提升
- **三重防幻觉约束**（工具描述 + 系统提示 + 返回末尾警告）
- 已导入 200 条车载语音情感分析报告

### 🔄 三级上下文 + 三级缓存
- **三级上下文**：最近 N 条原样保留 + 中间历史 LLM 压缩成摘要 + 更早历史存向量库按需召回
- **三级缓存**：ChromaDB 持久化 + 进程内存 + 重新生成兜底
- 摘要用**历史 MD5 hash** 做 key，相同历史只压缩一次
- **长对话 token 成本恒定**

### 📊 LangSmith 全链路可观测
- `wrap_openai` 自动追踪所有 LLM 调用
- `@traceable` 追踪 Agent 循环、工具执行、摘要生成
- 可视化每次对话的完整调用链，**性能瓶颈一目了然**

### 🎨 现代化 UI
- QSS 样式表 + 聊天气泡（用户蓝 / AI 绿 / 系统灰）
- 输入框聚焦发光（`QGraphicsDropShadowEffect`）
- 语音按钮脉冲呼吸（`QPropertyAnimation`）
- **流式渲染防崩**：流式期间纯文本通道 + 结束后重绘 HTML 气泡

### 🔄 连续对话模式
- AI 播报完自动开麦，不用按键
- 状态机管理（IDLE / LISTENING / TRANSCRIBING / THINKING / SPEAKING）
- 连续 2 次静音自动退出

---


## 📁 项目结构

```
AI语音助手/
├── main.py # 🎯 程序唯一入口
├── requirements.txt
├── README.md
├── .env # API Key 配置（不入库）
├── .gitignore
│
├── ai_service/ # ① AI 服务层
│ ├── init.py
│ ├── config.py # API Key / 模型参数 / 压缩参数
│ ├── llm_client.py # DeepSeek client + 三级上下文管理
│ ├── agent_loop.py # ReAct 循环（纯逻辑）
│ ├── thread_adapter.py # QThread 适配层
│ ├── asr_service.py # Whisper 语音识别
│ ├── vlm_client.py # 通义千问 VL 图片理解
│ └── image_gen.py # 通义万相文生图
│
├── audio/ # ② 音频输入输出
│ ├── init.py
│ ├── config.py
│ ├── recorder.py # PyAudio 录音
│ ├── tts.py # Edge-TTS 语音合成
│ └── continuous.py # 连续对话状态机
│
├── emotion/ # ③ 情感识别
│ ├── init.py
│ ├── config.py
│ ├── label_utils.py # 标签归一化（纯函数）
│ ├── model_loader.py # 线程安全模型缓存
│ ├── recognizer.py # 识别纯逻辑
│ └── thread.py
│
├── memory/ # ④ 记忆层（3 个 collection）
│ ├── init.py
│ ├── config.py
│ ├── embedding.py # 自定义 EmbeddingFunction
│ ├── chat_memory.py # 对话历史 + 摘要存取
│ ├── knowledge_base.py # 知识库（RAG）
│ └── service.py # 单例门面
│
├── prompt/ # ⑤ 提示词管理
│ ├── init.py
│ └── manager.py
│
├── tools/ # ⑥ Agent 工具集（19 个）
│ ├── init.py
│ ├── base.py # 注册中心 + ToolExecutor
│ ├── web_search.py
│ ├── weather.py
│ ├── calculator.py
│ ├── time_tool.py
│ ├── memory_tool.py
│ ├── emotion_kb.py # RAG 知识库检索
│ ├── mcp_map.py # 高德地图 MCP（12 个工具）
│ └── image_gen_tool.py # 文生图
│
├── ui/ # ⑦ UI 层
│ ├── init.py
│ ├── main_window.py # 主窗口（含 VLM 前置处理）
│ ├── styles.py
│ ├── widgets.py
│ └── chat_view.py
│
├── scripts/ # ⑧ 离线批处理
│ ├── init.py
│ ├── parse_report.py # Word → JSON
│ ├── ingest_report.py # JSON → ChromaDB
│ ├── preview_summary.py
│ └── list_mcp_tools.py
│
├── data/ # 原始数据（不入库）
├── models/ # 本地 embedding 模型（不入库）
├── emotion_model/ # 情感模型（不入库）
├── whisper_tiny_local/ # Whisper 模型（不入库）
├── generated_images/ # 文生图输出（不入库）
└── chroma_memory/ # ChromaDB 持久化（不入库）
```

---

## 🚀 快速开始

### 1. 环境要求
- Python ≥ 3.10
- Windows / macOS / Linux
- 麦克风（语音功能需要）

### 2. 安装依赖

```bash
pip install -r requirements.txt

```bash
pip install PyQt6 PyQt6-Multimedia openai python-dotenv requests
pip install pyaudio faster-whisper edge-tts
pip install transformers torch
pip install chromadb python-docx
pip install mcp dashscope pillow langsmith
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

#### `models/bge-small-zh-v1.5/` — 

任选一个中文情感模型（如 `BAAI/bge-small-zh-v1.5`）：

```bash
huggingface-cli download BAAI/bge-small-zh-v1.5 --local-dir models/bge-small-zh-v1.5
```

> 💡 **提示**：模型目录里应有 `config.json`、`pytorch_model.bin`（或 `model.safetensors`）、`vocab.txt` 等文件。

### 4. 配置 API Key

在项目根目录创建 `.env` 文件：

```env
# ===== 必填 =====
DEEPSEEK_API_KEY=sk-xxxxxxxx
TAVILY_API_KEY=tvly-xxxxxxxx
DASHSCOPE_API_KEY=sk-xxxxxxxx

# ===== 可选 =====
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=60.0
DEFAULT_TEMPERATURE=0.5

MAX_AGENT_ITERATIONS=5

HISTORY_MAX_LEN=6
HISTORY_KEEP_LEN=4
HISTORY_SUMMARY_MAX_TOKENS=300

EMOTION_MIN_CONFIDENCE=0.6
EMOTION_MAX_LENGTH=128

AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_CHUNK=1024
CONTINUOUS_RECORD_SECONDS=5

AMAP_KEY=xxxxxxxx

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxx
LANGCHAIN_PROJECT=multimodal-desktop-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**获取 API Key**：
- DeepSeek：https://platform.deepseek.com/
- Tavily：https://tavily.com/
获取 API Key：DeepSeek 平台、Tavily、阿里云百炼、LangSmith。
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
| **图片理解** | 点"📎"选择图片，输入问题后发送` |
| **连续对话** | 点"🔄 连续对话"，AI 播报完自动开麦` |
| **语音播报** |点"🔊"开关 TTS |

### 典型对话示例

```
用户：北京今天天气怎么样？
AI：[调用 get_weather] 北京今天晴，18~26°C...

用户：帮我算一下 (25 + 37) * 3
AI：[调用 calculate] 计算结果：(25 + 37) * 3 = 186

用户：上次有人堵车时很愤怒，系统建议了什么？
AI：[调用 search_driving_emotion] 根据知识库，建议播放舒缓音乐...

用户：画一只赛博朋克风格的猫
AI：[调用 generate_image] 图片已生成：generated_images/xxx.png

用户：天安门附近有什么餐厅？
AI：[调用 map_search_places] 找到 5 家餐厅...
```

---

## 🏗️ 架构设计

### 分层原则

```
┌─────────────────────────────────────────────┐
│  ui/          ← 界面与交互                   │
├─────────────────────────────────────────────┤
│  ai_service/  ← AI 逻辑（纯逻辑，不依赖 PyQt）│
│  audio/       ← 音频输入输出                  │
│  emotion/     ← 情感识别（纯逻辑）            │
│  memory/      ← 长期记忆 + RAG + 摘要          │
│  prompt/      ← 提示词管理                    │
│  tools/       ← Agent 工具集（19 个）          │
└─────────────────────────────────────────────┘
```

核心设计：
纯逻辑层不依赖 PyQt：agent_loop.py / recognizer.py / memory service 都是纯 Python，可单独 pytest，可复用到 CLI / Web / 批处理
回调抽象：AgentCallbacks 让 Agent 逻辑与 UI 完全解耦
QThread 适配层单独放置：只负责信号发射
工具自动注册：@register_tool 装饰器 + tools/__init__.py 显式导入，新增工具零侵入

### 数据流

```
用户输入（文字 / 语音 / 图片）
        │
        ▼
   [图片前置处理] ──→ 通义千问 VL → 文字描述
        │
        ▼
   [情感识别线程] ──→ 情绪标签 + 置信度
        │
        ▼
   [构建消息] ──→ 注入情感提示 + 动态时间 + 三级上下文压缩
        │
        ▼
   [ReAct Agent 循环]
        │
        ├─→ 流式输出 chunk ──→ UI 打字机
        │
        └─→ 工具调用 ──→ 19 个工具（含 RAG + 地图 MCP）
                │
                ▼
           结果拼回 messages，继续下一轮
        │
        ▼
   最终回复 → 写入 ChromaDB（对话 + 摘要）
        │
        ▼
   [TTS 播报] ──→ Edge-TTS → 扬声器
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
✅ 真正的多模态：文字 / 语音 / 图片三种输入，文字 / 语音 / 图像三种输出

✅ 自研 ReAct 循环：不到 200 行，完全可控

✅ Agentic RAG：RAG 工具化，Agent 自主决策

✅ 三级上下文 + 三级缓存：长对话 token 成本恒定

✅ 纯逻辑与 UI 完全解耦：核心逻辑可单独 pytest

✅ 流式渲染防崩：纯文本插入 + 结束后重绘气泡

✅ 三重防幻觉：工具描述 + 系统提示 + 返回末尾警告

✅ LangSmith 全链路可观测：可视化完整调用链

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
- DeepSeek — LLM 服务
- Edge-TTS — 语音合成
- 通义千问 VL — 图片理解
- 通义万相 — 文生图
- 高德地图 MCP — 地图服务
- LangSmith — LLM 应用可观测
