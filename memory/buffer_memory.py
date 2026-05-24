"""
Buffer Memory - Short-term conversation context
"""

import asyncio
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

class BufferMemory:
    def __init__(self, config: Dict):
        self.config = config
        self.max_size = config.get('buffer_size', 100)
        self.ttl_minutes = config.get('buffer_ttl', 60)  # Time to live
        self.buffers = defaultdict(lambda: deque(maxlen=self.max_size))
        self.timestamps = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize buffer memory"""
        self.initialized = True
        print(f"Buffer Memory initialized (size: {self.max_size}, TTL: {self.ttl_minutes}min)")
    
    async def add(self, user_id: str, role: str, content: str) -> None:
        """Add message to buffer"""
        if not user_id:
            user_id = 'default'
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        self.buffers[user_id].append(message)
        self._cleanup_expired(user_id)
    
    async def get_context(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation context"""
        if not user_id or user_id not in self.buffers:
            return []
        
        self._cleanup_expired(user_id)
        
        buffer = self.buffers[user_id]
        return list(buffer)[-limit:]
    
    async def get_last_n(self, user_id: str, n: int = 5) -> List[Dict]:
        """Get last N messages"""
        return await self.get_context(user_id, n)
    
    async def clear(self, user_id: str = None) -> None:
        """Clear buffer for user or all"""
        if user_id:
            if user_id in self.buffers:
                self.buffers[user_id].clear()
        else:
            self.buffers.clear()
    
    async def get_conversation_summary(self, user_id: str) -> str:
        """Get conversation summary"""
        context = await self.get_context(user_id, 20)
        
        if not context:
            return "No recent conversation"
        
        topics = set()
        for msg in context:
            # Extract potential topics (simple keyword extraction)
            words = msg['content'].lower().split()
            topics.update([w for w in words if len(w) > 5][:3])
        
        user_msgs = sum(1 for m in context if m['role'] == 'user')
        assistant_msgs = sum(1 for m in context if m['role'] == 'assistant')
        
        return f"Conversation: {user_msgs} user messages, {assistant_msgs} responses. Topics: {', '.join(list(topics)[:5])}"
    
    async def search_memory(self, user_id: str, query: str) -> List[Dict]:
        """Search through buffer memory"""
        context = await self.get_context(user_id)
        
        results = []
        query_lower = query.lower()
        
        for msg in context:
            if query_lower in msg['content'].lower():
                results.append(msg)
        
        return results[-10:]  # Return last 10 matches
    
    def _cleanup_expired(self, user_id: str) -> None:
        """Remove expired messages"""
        if user_id not in self.buffers:
            return
        
        cutoff = datetime.now() - timedelta(minutes=self.ttl_minutes)
        buffer = self.buffers[user_id]
        
        # Keep only messages newer than cutoff
        new_buffer = deque(maxlen=self.max_size)
        for msg in buffer:
            try:
                msg_time = datetime.fromisoformat(msg['timestamp'])
                if msg_time > cutoff:
                    new_buffer.append(msg)
            except:
                new_buffer.append(msg)
        
        self.buffers[user_id] = new_buffer
    
    async def get_stats(self) -> Dict:
        """Get memory statistics"""
        total_messages = sum(len(buf) for buf in self.buffers.values())
        active_users = len([uid for uid, buf in self.buffers.items() if len(buf) > 0])
        
        return {
            "total_messages": total_messages,
            "active_users": active_users,
            "max_size": self.max_size,
            "ttl_minutes": self.ttl_minutes
        }
    
    async def shutdown(self):
        """Cleanup"""
        self.buffers.clear()
        self.initialized = False
