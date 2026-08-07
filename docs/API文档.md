# API 文档

## POST /voice-chat

语音问答主接口：上传音频 → ASR 识别 → DeepSeek 回答 → TTS 合成 → 返回。

### 请求
- Content-Type: `multipart/form-data`
- 字段：
  - `file`（必填）：音频文件，支持 wav / mp3 / webm / ogg，最大 10MB
  - `session_id`（可选）：会话 id，用于多轮记忆；不传则本次不接续历史

### 响应（200，JSON）
- `asr_text`：语音识别出的文字
- `answer`：AI 回答文字
- `audio`：回复语音（base64 编码的 wav）

### 示例
```bash
curl -X POST -F "file=@test.wav" -F "session_id=abc123" http://localhost:8000/voice-chat
```

### 错误
- `400`：音频为空 / 过大
- `500`：ASR / LLM / TTS 调用失败（详见 detail）

---

## GET /chat

纯文本问答（不经过音频，方便快速测 LLM 和多轮记忆）。

### 请求（query 参数）
- `text`（必填）：用户问题
- `session_id`（可选）

### 响应（200，JSON）
- `answer`：AI 回答

### 示例
```bash
curl "http://localhost:8000/chat?text=你好&session_id=abc123"
```

---

## GET /

健康检查，返回 `{ "status": "ok" }`。

---

## 前端测试页
浏览器打开 `http://localhost:8000/static/index.html`，按住按钮说话即可。
