"""音频处理：大小校验、mime 兜底。"""
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def normalize_mime(content_type: str | None) -> str:
    """返回有效 mime，缺省时兜底 audio/wav。"""
    return content_type or "audio/wav"


def validate_audio(size: int, content_type: str | None) -> None:
    """校验音频大小；格式仅警告不拦截（浏览器 mime 多变，交给 ASR 判断）。

    不通过抛 ValueError，由 API 层转成 HTTP 4xx。
    """
    if size <= 0:
        raise ValueError("音频文件为空")

    if size > settings.AUDIO_MAX_BYTES:
        raise ValueError(
            f"音频过大（{size} 字节），上限 "
            f"{settings.AUDIO_MAX_BYTES // (1024 * 1024)}MB"
        )

    if content_type and content_type not in settings.AUDIO_ALLOWED_MIME:
        logger.warning("非白名单音频格式 %s，仍交给 ASR 尝试", content_type)
