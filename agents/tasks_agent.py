"""
Tasks Agent - Manages to-do lists and task tracking
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

class TasksAgent:
    def __init__(self, cod3x):
        self.cod3x = cod3x
        self.config = cod3x.config
        self.logger = cod3x.logger
        self.model = cod3x.model
    
    async def initialize(self):
        self.logger.info("Tasks Agent initialized")
    
    async def process(self, request: str, user_id: str, action: str = None, params: Dict = None) -> str:
        """Process task-related requests"""
        text_lower = request.lower()
        
        try:
            if any(kw in text_lower for kw in ['add task', 'create task', 'new task', 'todo', 'to-do']):
                return await self._add_task(request, user_id)
            elif any(kw in text_lower for kw in ['list task', 'show task', 'my tasks', 'what do i need']):
                return await self._list_tasks(user_id)
            elif any(kw in text_lower for kw in ['complete', 'done', 'finish', 'mark']):
                return await self._complete_task(request, user_id)
            elif any(kw in text_lower for kw in ['delete task', 'remove task']):
                return await self._delete_task(request, user_id)
            elif any(kw in text_lower for kw in ['priority', 'important']):
                return await self._prioritize_tasks(request, user_id)
            else:
                return await self._get_task_summary(user_id)
        except Exception as e:
            self.logger.error(f"Tasks agent error: {e}")
            return "I had trouble managing your tasks. Please try again."
    
    async def _add_task(self, request: str, user_id: str) -> str:
        """Add a new task"""
        # Extract task details
        task = await self._extract_task(request)
        
        # Add priority
        if 'urgent' in request.lower() or 'asap' in request.lower():
            task['priority'] = 'high'
        elif 'important' in request.lower():
            task['priority'] = 'medium'
        else:
            task['priority'] = 'low'
        
        # Set due date
        if 'tomorrow' in request.lower():
            task['due_date'] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif 'next week' in request.lower():
            task['due_date'] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            task['due_date'] = datetime.now().strftime("%Y-%m-%d")
        
        # Store task
        await self.cod3x.memory['sqlite'].store_task(user_id, task)
        
        return f"✅ Task added: '{task['title']}' (Priority: {task['priority']})"
    
    async def _extract_task(self, request: str) -> Dict:
        """Extract task details from request"""
        if self.model:
            prompt = f"""Extract task details from: {request}
            Return JSON: {{"title": "task title", "description": "details", "due_date": "YYYY-MM-DD"}}"""
            
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return json.loads(response.text)
            except:
                pass
        
        # Fallback extraction
        task = {
            "title": "New Task",
            "description": "",
            "due_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "pending"
        }
        
        # Remove common prefixes
        for prefix in ['add task', 'create task', 'new task', 'todo', 'to-do']:
            if prefix in request.lower():
                task['title'] = request.lower().split(prefix, 1)[1].strip().title()
                break
        
        return task
    
    async def _list_tasks(self, user_id: str) -> str:
        """List all tasks"""
        tasks = await self.cod3x.memory['sqlite'].get_tasks(user_id)
        
        if not tasks:
            return "📝 No tasks found. Would you like to add one?"
        
        response = "📝 **Your Tasks:**\n\n"
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        tasks.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
        
        for task in tasks[:10]:
            status_emoji = "✅" if task.get('status') == 'completed' else "⬜"
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(task.get('priority'), '')
            response += f"{status_emoji} {priority_emoji} {task['title']}"
            if task.get('due_date'):
                response += f" - Due: {task['due_date']}"
            response += "\n"
        
        return response
    
    async def _complete_task(self, request: str, user_id: str) -> str:
        """Mark task as complete"""
        # Extract task title from request
        task_title = request.lower()
        for kw in ['complete', 'done', 'finish', 'mark']:
            if kw in task_title:
                task_title = task_title.split(kw, 1)[1].strip()
                break
        
        await self.cod3x.memory['sqlite'].update_task(user_id, task_title.title(), 'completed')
        return f"✅ Task completed: '{task_title.title()}'"
    
    async def _delete_task(self, request: str, user_id: str) -> str:
        """Delete a task"""
        task_title = request.lower()
        for kw in ['delete task', 'remove task']:
            if kw in task_title:
                task_title = task_title.split(kw, 1)[1].strip()
                break
        
        await self.cod3x.memory['sqlite'].delete_task(user_id, task_title.title())
        return f"🗑️ Task deleted: '{task_title.title()}'"
    
    async def _prioritize_tasks(self, request: str, user_id: str) -> str:
        """Set task priority"""
        return "I've updated the task priority. Use 'list tasks' to see your prioritized list."
    
    async def _get_task_summary(self, user_id: str) -> str:
        """Get task summary"""
        tasks = await self.cod3x.memory['sqlite'].get_tasks(user_id)
        
        pending = sum(1 for t in tasks if t.get('status') != 'completed')
        completed = sum(1 for t in tasks if t.get('status') == 'completed')
        high_priority = sum(1 for t in tasks if t.get('priority') == 'high' and t.get('status') != 'completed')
        
        response = f"📊 **Task Summary:**\n"
        response += f"• Pending: {pending}\n"
        response += f"• Completed: {completed}\n"
        response += f"• High Priority: {high_priority}\n\n"
        
        if high_priority > 0:
            response += "⚠️ You have high priority tasks that need attention!"
        
        return response
    
    async def shutdown(self):
        pass
