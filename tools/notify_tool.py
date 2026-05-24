"""
Notify Tool - Desktop and mobile notifications
"""

import asyncio
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

class NotifyTool:
    def __init__(self, config: Dict):
        self.config = config
        self.notification_method = config.get('notifications', {}).get('method', 'desktop')
        self.sound_enabled = config.get('notifications', {}).get('sound', True)
        self.initialized = False
    
    async def initialize(self):
        """Initialize notification system"""
        try:
            if self.notification_method == 'desktop':
                # Try multiple desktop notification libraries
                try:
                    import plyer
                    self.backend = 'plyer'
                except ImportError:
                    try:
                        import notify2
                        notify2.init('Cod3x Agent')
                        self.backend = 'notify2'
                    except ImportError:
                        print("No desktop notification library found")
                        self.backend = 'console'
            elif self.notification_method == 'telegram':
                self.backend = 'telegram'
            else:
                self.backend = 'console'
            
            self.initialized = True
        except Exception as e:
            print(f"Notify init error: {e}")
            self.backend = 'console'
            self.initialized = True
    
    async def send_notification(self, title: str, message: str, urgency: str = 'normal', 
                               icon: str = None, timeout: int = 5) -> Dict:
        """Send a notification"""
        if not self.initialized:
            await self.initialize()
        
        try:
            if self.backend == 'plyer':
                from plyer import notification
                await asyncio.to_thread(
                    notification.notify,
                    title=title,
                    message=message,
                    app_name='Cod3x Agent',
                    timeout=timeout
                )
            elif self.backend == 'notify2':
                import notify2
                notif = notify2.Notification(title, message)
                if icon:
                    notif.set_icon_from_file(icon)
                await asyncio.to_thread(notif.show)
            elif self.backend == 'telegram':
                # Send via Telegram if configured
                telegram_tool = self.config.get('_telegram_tool')
                if telegram_tool:
                    await telegram_tool.send_message(text=f"🔔 *{title}*\n{message}")
            else:
                # Console fallback
                print(f"\n🔔 {title}")
                print(f"   {message}\n")
            
            return {"status": "sent", "method": self.backend}
        except Exception as e:
            print(f"Notification error: {e}")
            print(f"🔔 {title}: {message}")
            return {"status": "console_fallback"}
    
    async def send_alert(self, message: str) -> Dict:
        """Send high-priority alert"""
        return await self.send_notification("⚠️ Alert", message, urgency='critical', timeout=10)
    
    async def send_reminder(self, title: str, message: str, delay_seconds: int = 0) -> Dict:
        """Send a reminder after delay"""
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        
        return await self.send_notification(f"⏰ Reminder: {title}", message)
    
    async def send_progress(self, title: str, current: int, total: int) -> Dict:
        """Send progress notification"""
        percentage = int((current / total) * 100) if total > 0 else 0
        message = f"Progress: {current}/{total} ({percentage}%)"
        return await self.send_notification(title, message)
    
    async def send_batch(self, notifications: list) -> Dict:
        """Send multiple notifications"""
        results = []
        for notif in notifications:
            result = await self.send_notification(
                title=notif.get('title', 'Notification'),
                message=notif.get('message', ''),
                urgency=notif.get('urgency', 'normal')
            )
            results.append(result)
        
        return {"status": "batch_sent", "count": len(results)}
    
    async def shutdown(self):
        """Cleanup"""
        if self.backend == 'notify2':
            try:
                import notify2
                notify2.uninit()
            except:
                pass
        self.initialized = False
