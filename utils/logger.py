"""日志配置：控制台 + logs/app.log（按天滚动，保留 7 天）。"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

# logs 目录放在项目根下
_LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
)
os.makedirs(_LOG_DIR, exist_ok=True)

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """配置根 logger。重复调用不会重复添加 handler。"""
    root = logging.getLogger()

    if getattr(root, "_voice_configured", False):
        return root

    root.setLevel(level)
    formatter = logging.Formatter(_FORMAT)

    # 控制台
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    # 文件（按天滚动）
    file_handler = TimedRotatingFileHandler(
        os.path.join(_LOG_DIR, "app.log"),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    root._voice_configured = True  # type: ignore[attr-defined]
    return root


def get_logger(name: str) -> logging.Logger:
    """各模块用 get_logger(__name__) 取 logger。"""
    return logging.getLogger(name)
