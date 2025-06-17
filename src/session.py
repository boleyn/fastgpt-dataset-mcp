"""
会话管理模块

提供用户会话管理功能，包括会话创建、数据存储、生命周期管理等。
"""

import time
from typing import Dict, Optional, List, Any


class UserSession:
    """用户会话类"""
    
    def __init__(self, username: str, client_id: str):
        self.username = username
        self.client_id = client_id
        self.data: Dict[str, Any] = {}
        self.created_at = time.time()
        self.last_activity = time.time()
        self.active = True
    
    def get(self, key: str, default=None):
        """获取会话数据"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置会话数据"""
        self.data[key] = value
        self.last_activity = time.time()
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = time.time()
    
    def get_session_info(self) -> Dict:
        """获取会话信息"""
        return {
            "username": self.username,
            "client_id": self.client_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "session_age": time.time() - self.created_at,
            "idle_time": time.time() - self.last_activity,
            "active": self.active,
            "data_keys": list(self.data.keys())
        }
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "username": self.username,
            "client_id": self.client_id,
            "data": self.data,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "active": self.active
        }


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
    
    def create_session(self, client_id: str, username: str) -> UserSession:
        """创建新会话"""
        # 如果已存在会话，先清理
        if client_id in self.sessions:
            self.sessions[client_id].active = False
        
        session = UserSession(username, client_id)
        self.sessions[client_id] = session
        return session
    
    def get_session(self, client_id: str) -> Optional[UserSession]:
        """获取会话"""
        session = self.sessions.get(client_id)
        if session and session.active:
            session.update_activity()
            return session
        return None
    
    def get_session_by_username(self, username: str) -> Optional[UserSession]:
        """根据用户名获取会话"""
        for session in self.sessions.values():
            if session.username == username and session.active:
                session.update_activity()
                return session
        return None
    
    def update_session_data(self, client_id: str, key: str, value: Any) -> bool:
        """更新会话数据"""
        session = self.get_session(client_id)
        if session:
            session.set(key, value)
            return True
        return False
    
    def end_session(self, client_id: str) -> bool:
        """结束会话"""
        if client_id in self.sessions:
            self.sessions[client_id].active = False
            del self.sessions[client_id]
            return True
        return False
    
    def get_all_sessions(self) -> List[Dict]:
        """获取所有活跃会话信息"""
        return [session.get_session_info() for session in self.sessions.values() if session.active]
    
    def cleanup_expired_sessions(self, max_idle_time: int = 3600) -> int:
        """清理过期会话（默认1小时）"""
        current_time = time.time()
        expired_sessions = []
        
        for client_id, session in self.sessions.items():
            if current_time - session.last_activity > max_idle_time:
                expired_sessions.append(client_id)
        
        for client_id in expired_sessions:
            self.end_session(client_id)
        
        return len(expired_sessions)
    
    def get_session_stats(self) -> Dict:
        """获取会话统计信息"""
        active_sessions = [s for s in self.sessions.values() if s.active]
        
        if not active_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "average_session_age": 0,
                "average_idle_time": 0,
                "users": []
            }
        
        current_time = time.time()
        session_ages = [current_time - s.created_at for s in active_sessions]
        idle_times = [current_time - s.last_activity for s in active_sessions]
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active_sessions),
            "average_session_age": sum(session_ages) / len(session_ages),
            "average_idle_time": sum(idle_times) / len(idle_times),
            "users": [s.username for s in active_sessions]
        } 