"""会话管理器"""
from typing import Dict, List, Any, Optional
from app.config import settings


class SessionManager:
    """会话管理器，管理多轮对话上下文"""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """获取或创建会话"""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": [],
                "context": {},
                "reset_done": False  # 标记是否已重置房源数据
            }
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话历史"""
        session = self.get_or_create_session(session_id)
        session["messages"].append({"role": role, "content": content})

        # 限制历史消息数量
        if len(session["messages"]) > settings.MAX_HISTORY_TURNS * 2:
            session["messages"] = session["messages"][-settings.MAX_HISTORY_TURNS * 2:]

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """获取会话历史消息"""
        session = self.get_or_create_session(session_id)
        return session["messages"]

    def set_context(self, session_id: str, key: str, value: Any):
        """设置会话上下文"""
        session = self.get_or_create_session(session_id)
        session["context"][key] = value

    def get_context(self, session_id: str, key: str) -> Optional[Any]:
        """获取会话上下文"""
        session = self.get_or_create_session(session_id)
        return session["context"].get(key)

    def is_reset_done(self, session_id: str) -> bool:
        """检查是否已重置房源数据"""
        session = self.get_or_create_session(session_id)
        return session["reset_done"]

    def set_reset_done(self, session_id: str, done: bool = True):
        """设置重置状态"""
        session = self.get_or_create_session(session_id)
        session["reset_done"] = done

    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]


# 全局会话管理器
session_manager = SessionManager()