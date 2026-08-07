# 🎤 语音 AI 助手

一个语音交互的 AI 助手：用户说话 → 阿里百炼 ASR 转文字 → DeepSeek 大模型回答 → 阿里百炼 TTS 转语音 → 播放回复。

```
🎤 用户语音 ──► ASR 识别 ──► DeepSeek 回答 ──► TTS 合成 ──► 🔊 语音回复
   (qwen3-asr-flash)    (deepseek-v4-flash)   (qwen-audio-3.0-tts-flash)
```

## ✨ 功能特性

- **语音问答**：录音 / 上传音频，端到端返回语音回复
- **多轮对话记忆**：基于 session_id 的上下文记忆（内存存储，可扩展 Redis）
- **文本接口**：不用音频也能快速测大模型
- **前端测试页**：浏览器里按住说话，显示识别文本 + 播放回复
- **分层架构**：api / services / utils / models，职责清晰

## 🧰 技术栈

| 模块 | 技术 |
|---|---|
| 后端 | Python 3.10+ · FastAPI · Uvicorn |
| ASR | 阿里百炼 `qwen3-asr-flash`（OpenAI 兼容接口） |
| LLM | DeepSeek `deepseek-v4-flash` |
| TTS | 阿里百炼 `qwen-audio-3.0-tts-flash`（dashscope） |
| 前端 | 原生 HTML/JS（MediaRecorder API） |

## 📁 项目结构

```
voice-assistant/
├── app.py                  # 入口：建 app、挂路由/静态页、启动
├── config.py               # 配置集中管理（读 .env）
├── requirements.txt
├── .env / .env.example     # 密钥（自己填）/ 模板
│
├── api/voice_api.py        # 路由 + 主流程编排
├── services/
│   ├── asr_service.py          # 语音 → 文字
│   ├── llm_service.py          # 大模型问答（支持多轮）
│   ├── tts_service.py          # 文字 → 语音
│   └── conversation_service.py # 内存对话记忆
├── utils/
│   ├── logger.py               # 日志（控制台 + logs/app.log）
│   └── audio_utils.py          # 音频校验
├── models/schemas.py       # Pydantic 请求/响应模型
├── static/index.html       # 前端测试页
├── logs/                   # 运行日志
└── docs/                   # 需求 / 实施计划 / API 文档
```

## 🚀 快速开始

### 1. 环境要求
- Python 3.10+
- 阿里百炼、DeepSeek 的 API Key

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置密钥
```bash
cp .env.example .env
```
编辑 `.env`，填入三个 key：
```
DASHSCOPE_API_KEY=你的阿里百炼key
DASHSCOPE_WORKSPACE_ID=你的百炼workspace id
DEEPSEEK_API_KEY=你的deepseek key
```

### 4. 运行
```bash
python app.py
```
服务启动在 `http://localhost:8000`。

### 5. 使用
- **网页**：浏览器打开 `http://localhost:8000/static/index.html`，按住按钮说话
- **命令行测文本**：`curl "http://localhost:8000/chat?text=你好"`

## 📖 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/voice-chat` | 语音问答（上传音频，返回识别文本+回答+base64音频） |
| `GET` | `/chat?text=&session_id=` | 纯文本问答（快速测大模型/多轮） |
| `GET` | `/` | 健康检查 |

详细字段、示例见 [`docs/API文档.md`](docs/API文档.md)。

## ⚙️ 配置

所有可调参数集中在 `config.py`：模型名、音色（`longanhuan_v3.6`）、采样率、音频大小上限（10MB）、对话记忆长度（最近 20 条）等。改完重启生效。

## ❓ 常见问题

- **启动报「缺少环境变量」**：`.env` 没填或没填全三个 key。
- **网页无法录音**：浏览器要授权麦克风；本地用 `localhost` 才能调麦克风（`http://ip` 可能被拦）。
- **某一步失败**：看终端日志，会依次打印 `ASR 识别中` → `DeepSeek 调用中` → `TTS 合成中`，卡在哪步一目了然。
- **音频格式**：支持 wav / mp3 / webm / ogg，浏览器录音默认 webm。

## 📚 更多文档

- [需求文档](docs/语音AI助手系统需求文档.md)
- [实施计划](docs/语音AI助手系统实施计划.md)
- [API 文档](docs/API文档.md)
