"""配置管理：集中读取 .env，提供全局 settings 单例。"""
import os

from dotenv import load_dotenv


class Settings:
    """全局配置。启动时调用 validate() 校验关键密钥非空。"""

    def __init__(self) -> None:
        load_dotenv()

        # ---- 密钥 ----
        self.DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
        self.DASHSCOPE_WORKSPACE_ID = os.getenv("DASHSCOPE_WORKSPACE_ID", "")
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

        # ---- 阿里百炼地址（华北2-北京）----
        self.ALI_HTTP_BASE = (
            f"https://{self.DASHSCOPE_WORKSPACE_ID}."
            f"cn-beijing.maas.aliyuncs.com/api/v1"
        )
        self.ALI_OPENAI_BASE = (
            f"https://{self.DASHSCOPE_WORKSPACE_ID}."
            f"cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
        )

        # ---- 模型 / 音色 ----
        self.ASR_MODEL = "qwen3-asr-flash"
        self.LLM_MODEL = "deepseek-v4-flash"
        self.TTS_MODEL = "qwen-audio-3.0-tts-flash"
        self.TTS_VOICE = "longanhuan_v3.6"
        self.TTS_SAMPLE_RATE = 24000

        # ---- LLM ----
        self.DEEPSEEK_BASE_URL = "https://api.deepseek.com"
        self.LLM_SYSTEM_PROMPT = (
            "你是一个语音助手。"
            "请使用自然、简洁、口语化的中文回答用户。"
            "因为回答会被转换为语音，所以不要使用 Markdown 表格、"
            "复杂符号或大量列表。"
        )
        # 对话记忆保留最近 N 条消息（user+assistant 算多条）
        self.MAX_HISTORY_MESSAGES = 20

        # ---- 音频限制 ----
        self.AUDIO_MAX_BYTES = 10 * 1024 * 1024  # 10MB
        self.AUDIO_ALLOWED_MIME = {
            "audio/wav", "audio/x-wav",
            "audio/mpeg", "audio/mp3",
            "audio/webm", "audio/x-webm",
            "audio/ogg",
        }

        # ---- 服务 ----
        self.HOST = "0.0.0.0"
        self.PORT = 8000

    def validate(self) -> None:
        """启动时校验密钥，缺了直接报错（沿用原 app.py 行为）。"""
        missing = [
            name for name, val in (
                ("DASHSCOPE_API_KEY", self.DASHSCOPE_API_KEY),
                ("DASHSCOPE_WORKSPACE_ID", self.DASHSCOPE_WORKSPACE_ID),
                ("DEEPSEEK_API_KEY", self.DEEPSEEK_API_KEY),
            ) if not val
        ]
        if missing:
            raise RuntimeError(
                f"缺少环境变量: {', '.join(missing)}（请在 .env 中配置）"
            )


settings = Settings()
settings.validate()
