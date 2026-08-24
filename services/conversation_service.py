"""对话记忆服务（内存版）：session_id -> 历史消息。

线程安全。带 TTL 和会话总数上限，避免内存无限增长。
预留了替换为 Redis / DB 的扩展点。
"""
import threading
import time

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationStore:
    """内存对话存储。生产环境可换成 Redis/DB 后端。"""

    def __init__(
        self,
        max_messages: int = settings.MAX_HISTORY_MESSAGES,
        session_ttl_seconds: int = settings.SESSION_TTL_SECONDS,
        max_sessions: int = settings.MAX_SESSIONS,
    ) -> None:
        self._store: dict[str, list[dict]] = {}
        self._last_access: dict[str, float] = {}
        self._lock = threading.Lock()
        self._max = max_messages
        self._ttl = session_ttl_seconds
        self._max_sessions = max_sessions

    def get_messages(self, session_id: str) -> list[dict]:
        """返回历史消息（user/assistant，不含 system）的拷贝。"""
        with self._lock:
            self._touch(session_id)
            return list(self._store.get(session_id, []))

    def add_user(self, session_id: str, text: str) -> None:
        self._append(session_id, {"role": "user", "content": text})

    def add_assistant(self, session_id: str, text: str) -> None:
        self._append(session_id, {"role": "assistant", "content": text})

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)
            self._last_access.pop(session_id, None)

    def _append(self, session_id: str, message: dict) -> None:
        with self._lock:
            self._touch(session_id)
            if session_id not in self._store:
                logger.info("新建会话: %s", session_id)
            history = self._store.setdefault(session_id, [])
            history.append(message)
            # 保留最近 N 条，避免上下文无限增长
            if len(history) > self._max:
                del history[: len(history) - self._max]

    def _touch(self, session_id: str) -> None:
        """更新访问时间并顺手做过期清理（调用方需已持锁）。"""
        now = time.monotonic()
        # 会话总数超限时，先淘汰最久未访问的
        if session_id not in self._store and len(self._store) >= self._max_sessions:
            evicted = sorted(self._last_access, key=self._last_access.get)[:1]
            for sid in evicted:
                logger.info("会话数达上限，淘汰最久未访问会话: %s", sid)
                self._store.pop(sid, None)
                self._last_access.pop(sid, None)
        # 过期清理：摊销式，每次访问最多清一个过期会话，避免全表扫描
        expired = next(
            (sid for sid, ts in self._last_access.items() if now - ts > self._ttl),
            None,
        )
        if expired is not None:
            self._store.pop(expired, None)
            self._last_access.pop(expired, None)
        self._last_access[session_id] = now


# 模块级单例
conversation = ConversationStore()
