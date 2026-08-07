"""LLM 服务：DeepSeek（deepseek-v4-flash），支持多轮历史（搬自原 app.py §4/§6）。"""
from openai import OpenAI

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)


def chat(messages: list[dict]) -> str:
    """传入完整 messages（含 system + 历史），返回回答文本。

    语音助手追求响应速度，关闭思考模式。
    """
    logger.info("DeepSeek 调用中（%d 条消息）", len(messages))

    response = _client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )

    answer = response.choices[0].message.content
    if not answer:
        raise RuntimeError("DeepSeek 未返回回答")

    logger.info("DeepSeek 回答: %s", answer)
    return answer.strip()
