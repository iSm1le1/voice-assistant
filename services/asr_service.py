"""ASR 服务：阿里百炼 qwen3-asr-flash，语音 -> 文字（搬自原 app.py §3/§5）。"""
import base64

from openai import BadRequestError, OpenAI

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# 百炼支持 OpenAI 兼容接口
# 默认超时高达 600s，显式收紧并允许少量重试，防止上游挂起占满线程池
_client = OpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.ALI_OPENAI_BASE,
    timeout=60,
    max_retries=2,
)


def speech_to_text(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """音频字节 -> 文字。"""
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{audio_base64}"

    logger.info("ASR 识别中（%s, %d 字节）", mime_type, len(audio_bytes))

    try:
        response = _client.chat.completions.create(
            model=settings.ASR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {"data": data_uri},
                        }
                    ],
                }
            ],
            stream=False,
            extra_body={
                "asr_options": {
                    "language": "zh",    # 已知用户说中文
                    "enable_itn": True,  # 数字等文本规范化
                }
            },
        )
    except BadRequestError as e:
        # 上游 400 均为音频内容问题（空音频、损坏、不支持等），
        # 翻译成业务错误让 API 层映射为 400 而非 500
        if "empty" in str(e).lower():
            raise ValueError("录音太短或没有听清声音，请再试一次") from e
        raise ValueError("无法识别该音频，请重新录制或更换格式") from e

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("ASR 未识别到文字")

    logger.info("ASR 结果: %s", text)
    return text.strip()
