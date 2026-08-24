"""语音接口：POST /voice-chat 主流程 + GET / 健康检查 + GET /chat 纯文本测试。

接口用同步 def：服务层（ASR/LLM/TTS）都是同步 SDK，FastAPI 会把同步
路由放进线程池执行，不会阻塞事件循环。
"""
import base64
import secrets
import uuid

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from config import settings
from models.schemas import ChatResponse, HealthResponse, VoiceChatResponse
from services import asr_service, llm_service, tts_service
from services.conversation_service import conversation
from utils.audio_utils import normalize_mime, validate_audio
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

_ERROR_RESPONSES = {
    400: {"description": "请求参数错误（如音频为空/过大）"},
    401: {"description": "缺少或错误的 X-API-Key"},
    500: {"description": "服务内部错误"},
}


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """API Key 鉴权：配置了 APP_API_KEY 时校验请求头，未配置则放行（本地开发）。"""
    expected = settings.APP_API_KEY
    if expected and not secrets.compare_digest(
        x_api_key.encode(), expected.encode()
    ):
        # encode 成字节再比：header 经 latin-1 解码可能含非 ASCII，
        # 直接比 str 会抛 TypeError 变成 500
        raise HTTPException(status_code=401, detail="无效的 API Key")


def _validate_session_id(session_id: str) -> str:
    sid = session_id.strip()
    if len(sid) > 64:
        raise ValueError("session_id 过长（上限 64 字符）")
    return sid or str(uuid.uuid4())


@router.get("/", response_model=HealthResponse)
def index() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/voice-chat",
    response_model=VoiceChatResponse,
    responses=_ERROR_RESPONSES,
    dependencies=[Depends(require_api_key)],
)
def voice_chat(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
) -> VoiceChatResponse:
    """语音问答主接口：音频 -> ASR -> 大模型 -> TTS -> 返回(JSON)。"""
    # 没传 session_id 就临时生成一个（本次无多轮记忆）
    try:
        sid = _validate_session_id(session_id)
        audio_bytes = file.file.read()
        mime_type = normalize_mime(file.content_type)

        # 1. 校验音频
        validate_audio(len(audio_bytes), file.content_type)

        # 2. ASR：语音 -> 文字
        asr_text = asr_service.speech_to_text(audio_bytes, mime_type)

        # 3. 拼 system + 历史 + 本条提问，调大模型
        messages = [{"role": "system", "content": settings.LLM_SYSTEM_PROMPT}]
        messages += conversation.get_messages(sid)
        messages.append({"role": "user", "content": asr_text})
        answer = llm_service.chat(messages)

        # 4. TTS：文字 -> 语音
        audio = tts_service.text_to_speech(answer)

        # 5. 全链路成功后才写入历史（TTS 失败时用户没听到回答，
        #    不记忆本次问答，重试才不会产生重复上下文）
        conversation.add_user(sid, asr_text)
        conversation.add_assistant(sid, answer)

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
    except Exception:
        # 不把内部异常原文回显给客户端，详细信息看日志
        logger.exception("voice-chat 处理失败")
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后重试")


@router.get(
    "/chat",
    response_model=ChatResponse,
    responses=_ERROR_RESPONSES,
    dependencies=[Depends(require_api_key)],
)
def chat(text: str, session_id: str = "") -> ChatResponse:
    """纯文本问答（不用音频，方便快速测 LLM 和多轮记忆）。"""
    if not text.strip():
        raise HTTPException(status_code=400, detail="text 不能为空")
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail="text 过长（上限 2000 字符）")
    try:
        sid = _validate_session_id(session_id)
        messages = [{"role": "system", "content": settings.LLM_SYSTEM_PROMPT}]
        messages += conversation.get_messages(sid)
        messages.append({"role": "user", "content": text})
        answer = llm_service.chat(messages)
        conversation.add_user(sid, text)
        conversation.add_assistant(sid, answer)
        return ChatResponse(answer=answer)
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("请求参数错误: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("chat 处理失败")
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后重试")
