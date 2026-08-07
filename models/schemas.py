"""请求/响应数据模型（Pydantic）。"""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class VoiceChatResponse(BaseModel):
    """语音问答返回：识别文本 + AI 回答 + 回复音频(base64)。"""
    asr_text: str
    answer: str
    audio: str  # base64 编码的 wav


class ChatResponse(BaseModel):
    """纯文本问答返回（GET /chat 用，方便快速测 LLM）。"""
    answer: str


class ErrorResponse(BaseModel):
    detail: str
