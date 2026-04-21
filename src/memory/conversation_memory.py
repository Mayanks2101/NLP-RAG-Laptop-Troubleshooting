# src/memory/conversation_memory.py
"""
In-memory conversation history store.

Manages per-session chat history so the LLM can see past messages.
Each session is identified by a `session_id` string (UUID sent by the client).

Design decisions:
- Pure Python dict → zero dependencies, instant reads/writes.
- Sliding window: once a session exceeds MAX_HISTORY_TURNS pairs,
  the oldest (user, assistant) pair is dropped automatically.
- Thread-safe enough for single-process FastAPI (uvicorn default).
  For multi-worker deployments, swap the dict for Redis.

Message format stored per turn:
    {"role": "user",      "content": "<question>"}
    {"role": "assistant", "content": "<answer>"}
"""

from collections import defaultdict, deque
from typing import List, Dict
from threading import Lock

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """
    Per-session sliding-window message history.

    Usage:
        memory = ConversationMemory()
        memory.add_turn(session_id, user_msg="...", assistant_msg="...")
        history = memory.get_history(session_id)   # list of {role, content}
        memory.clear(session_id)
    """

    def __init__(self, max_turns: int = None):
        # max_turns = number of (user, assistant) PAIRS to retain
        self._max_turns: int = max_turns or settings.MAX_HISTORY_TURNS
        # Each session stores a deque of message dicts (2 messages per turn)
        self._store: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self._max_turns * 2)
        )
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_turn(
        self,
        session_id: str,
        user_msg: str,
        assistant_msg: str,
    ) -> None:
        """
        Append a completed (user, assistant) turn to the session history.
        Oldest turn is evicted automatically when the window is full.

        Args:
            session_id:    Unique session identifier (UUID from client).
            user_msg:      The user's question for this turn.
            assistant_msg: The assistant's answer for this turn.
        """
        with self._lock:
            session = self._store[session_id]
            session.append({"role": "user",      "content": user_msg})
            session.append({"role": "assistant", "content": assistant_msg})

        logger.debug(
            "💬 Session '{}' | history size: {} messages ({} turns)",
            session_id[:8],
            len(self._store[session_id]),
            len(self._store[session_id]) // 2,
        )

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Return the full message list for a session in OpenAI chat format.

        Returns:
            List of {"role": "user"|"assistant", "content": str} dicts,
            oldest first. Empty list if session doesn't exist yet.
        """
        with self._lock:
            return list(self._store.get(session_id, []))

    def format_history_for_prompt(self, session_id: str) -> str:
        """
        Return conversation history as a human-readable block for injection
        into a text prompt (used by the query generator and final synthesizer).

        Example output:
            [Turn 1]
            User: My laptop screen is flickering.
            Assistant: This is usually caused by a loose display cable...

            [Turn 2]
            User: I checked the cable, still flickering.
            Assistant: Next, try updating your GPU drivers...
        """
        history = self.get_history(session_id)
        if not history:
            return ""

        lines = []
        turn_num = 1
        for i in range(0, len(history), 2):
            user_part = history[i]["content"]
            asst_part = history[i + 1]["content"] if i + 1 < len(history) else ""
            lines.append(f"[Turn {turn_num}]")
            lines.append(f"User: {user_part}")
            if asst_part:
                lines.append(f"Assistant: {asst_part}")
            lines.append("")
            turn_num += 1

        return "\n".join(lines).strip()

    def clear(self, session_id: str) -> bool:
        """
        Delete all history for a session.

        Returns:
            True if session existed and was cleared, False if it didn't exist.
        """
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]
                logger.info("🗑️ Cleared history for session '{}'", session_id[:8])
                return True
            return False

    def session_count(self) -> int:
        """Return total number of active sessions (useful for monitoring)."""
        with self._lock:
            return len(self._store)

    def get_turn_count(self, session_id: str) -> int:
        """Return number of completed turns for a session."""
        with self._lock:
            return len(self._store.get(session_id, [])) // 2


# === Global singleton — import this everywhere ===
memory_store = ConversationMemory()
