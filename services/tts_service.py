"""TTS 服务：阿里百炼 qwen-audio-3.0-tts-flash，文字 -> 语音（搬自原 app.py §7）。"""
import dashscope
from dashscope.audio.http_tts.http_speech_synthesizer import HttpSpeechSynthesizer

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# DashScope TTS 需要设置 api_key 与 base url
dashscope.api_key = settings.DASHSCOPE_API_KEY
dashscope.base_http_api_url = settings.ALI_HTTP_BASE


def text_to_speech(text: str) -> bytes:
    """文字 -> wav 字节。"""
    logger.info("TTS 合成中（%d 字）", len(text))

    result = HttpSpeechSynthesizer.call(
        model=settings.TTS_MODEL,
        text=text,
        voice=settings.TTS_VOICE,
        audio_format="wav",  # SDK 形参名是 audio_format，勿写 format（会被 kwargs 吞掉）
        sample_rate=settings.TTS_SAMPLE_RATE,
        stream=True,
        api_key=settings.DASHSCOPE_API_KEY,
    )

    audio_chunks = []
    for chunk in result:
        # 依赖的 SDK 语义（dashscope 1.26.5 已核对源码）：
        # - sentence 事件产出增量 chunk（audio_url=None）
        # - finish 块的 audio_data 是全部增量的拼接，且当前必带 audio_url
        # 若某天 SDK 升级后 stop 块不再返回 audio_url，此处会把整段音频重复
        # 拼接一遍，升级 SDK 时需重点回归（不能简单按"块长==累计长"去重）
        if not chunk.audio_url and chunk.audio_data:
            audio_chunks.append(chunk.audio_data)

    if not audio_chunks:
        raise RuntimeError("TTS 未生成音频")

    logger.info("TTS 完成（%d 字节）", sum(len(c) for c in audio_chunks))
    return b"".join(audio_chunks)
