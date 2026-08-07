"""对话记忆服务（内存版）：session_id -> 历史消息。

线程安全。预留了替换为 Redis / DB 的扩展点。
"""
import threading

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationStore:
    """内存对话存储。生产环境可换成 Redis/DB 后端。"""

    def __init__(self, max_messages: int = settings.MAX_HISTORY_MESSAGES) -> None:
        self._store: dict[str, list[dict]] = {}
        self._lock = threading.Lock()
        self._max = max_messages

    def get_messages(self, session_id: str) -> list[dict]:
        """返回历史消息（user/assistant，不含 system）的拷贝。"""
        with self._lock:
            return list(self._store.get(session_id, []))

    def add_user(self, session_id: str, text: str) -> None:
        self._append(session_id, {"role": "user", "content": text})

    def add_assistant(self, session_id: str, text: str) -> None:
        self._append(session_id, {"role": "assistant", "content": text})

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def _append(self, session_id: str, message: dict) -> None:
        with self._lock:
            if session_id not in self._store:
                logger.info("新建会话: %s", session_id)
            history = self._store.setdefault(session_id, [])
            history.append(message)
            # 保留最近 N 条，避免上下文无限增长
            if len(history) > self._max:
                del history[: len(history) - self._max]


# 模块级单例
conversation = ConversationStore()
