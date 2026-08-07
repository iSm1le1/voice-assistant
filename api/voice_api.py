"""语音接口：POST /voice-chat 主流程 + GET / 健康检查 + GET /chat 纯文本测试。"""
import base64
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from config import settings
from models.schemas import ChatResponse, HealthResponse, VoiceChatResponse
from services import asr_service, llm_service, tts_service
from services.conversation_service import conversation
from utils.audio_utils import normalize_mime, validate_audio
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=HealthResponse)
def index() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
) -> VoiceChatResponse:
    """语音问答主接口：音频 -> ASR -> 大模型 -> TTS -> 返回(JSON)。"""
    # 没传 session_id 就临时生成一个（本次无多轮记忆）
    sid = session_id.strip() or str(uuid.uuid4())

    try:
        audio_bytes = await file.read()
        mime_type = normalize_mime(file.content_type)

        # 1. 校验音频
        validate_audio(len(audio_bytes), file.content_type)

        # 2. ASR：语音 -> 文字
        asr_text = asr_service.speech_to_text(audio_bytes, mime_type)

        # 3. 记住用户说的
        conversation.add_user(sid, asr_text)

        # 4. 拼 system + 历史，调大模型
        messages = [{"role": "system", "content": settings.LLM_SYSTEM_PROMPT}]
        messages += conversation.get_messages(sid)
        answer = llm_service.chat(messages)

        # 5. 记住 AI 回答
        conversation.add_assistant(sid, answer)

        # 6. TTS：文字 -> 语音
        audio = tts_service.text_to_speech(answer)

        return VoiceChatResponse(
            asr_text=asr_text,
            answer=answer,
            audio=base64.b64encode(audio).decode("utf-8"),
        )

    except HTTPException:
        raise
    except ValueError as e:
        # 音频校验类错误 -> 400
        logger.warning("请求参数错误: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("voice-chat 处理失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat", response_model=ChatResponse)
def chat(text: str, session_id: str = "") -> ChatResponse:
    """纯文本问答（不用音频，方便快速测 LLM 和多轮记忆）。"""
    sid = session_id.strip() or str(uuid.uuid4())

    try:
        conversation.add_user(sid, text)
        messages = [{"role": "system", "content": settings.LLM_SYSTEM_PROMPT}]
        messages += conversation.get_messages(sid)
        answer = llm_service.chat(messages)
        conversation.add_assistant(sid, answer)
        return ChatResponse(answer=answer)
    except Exception as e:
        logger.exception("chat 处理失败")
        raise HTTPException(status_code=500, detail=str(e))
