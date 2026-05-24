"""
Voice Speaker Interface - Text-to-speech output
"""

import asyncio
from typing import Dict, Any, Optional
import os
import tempfile

class VoiceSpeaker:
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = False
        self.engine = None
        self.voice = config.get('voice', {}).get('speaker_voice', 'default')
        self.rate = config.get('voice', {}).get('speaking_rate', 175)
        self.volume = config.get('voice', {}).get('volume', 1.0)
    
    async def initialize(self):
        """Initialize text-to-speech engine"""
        engines = []
        
        # Try pyttsx3 (offline)
        try:
            import pyttsx3
            engine = await asyncio.to_thread(pyttsx3.init)
            
            # Configure voice
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[0].id)
            
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            engines.append(('pyttsx3', engine))
        except ImportError:
            pass
        
        # Try gTTS (online, better quality)
        try:
            from gtts import gTTS
            engines.append(('gtts', 'gtts'))
        except ImportError:
            pass
        
        if engines:
            self.engine = engines[0][1]
            self.engine_type = engines[0][0]
            self.enabled = True
            print(f"Voice speaker initialized ({self.engine_type})")
            return True
        else:
            print("No TTS engine available. Install: pip install pyttsx3 gTTS")
            return False
    
    async def speak(self, text: str, blocking: bool = False):
        """Convert text to speech"""
        if not self.enabled:
            print(f"🔊 {text[:100]}...")
            return
        
        # Clean text for speech
        clean_text = self._clean_for_speech(text)
        
        try:
            if self.engine_type == 'pyttsx3':
                await self._speak_pyttsx3(clean_text, blocking)
            elif self.engine_type == 'gtts':
                await self._speak_gtts(clean_text, blocking)
        except Exception as e:
            print(f"Speech error: {e}")
    
    def _clean_for_speech(self, text: str) -> str:
        """Clean text for better speech"""
        # Remove markdown formatting
        import re
        
        # Remove asterisks and other markdown
        text = re.sub(r'\*\*?(.*?)\*\*?', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Replace common symbols
        text = text.replace('&', ' and ')
        text = text.replace('#', ' hashtag ')
        text = text.replace('@', ' at ')
        
        # Limit length for speech
        if len(text) > 1000:
            text = text[:997] + "..."
        
        return text
    
    async def _speak_pyttsx3(self, text: str, blocking: bool):
        """Speak using pyttsx3"""
        import pyttsx3
        
        if blocking:
            await asyncio.to_thread(self.engine.say, text)
            await asyncio.to_thread(self.engine.runAndWait)
        else:
            await asyncio.to_thread(self.engine.say, text)
    
    async def _speak_gtts(self, text: str, blocking: bool):
        """Speak using gTTS"""
        from gtts import gTTS
        import tempfile
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            temp_path = f.name
        
        # Generate speech
        tts = gTTS(text=text, lang='en')
        await asyncio.to_thread(tts.save, temp_path)
        
        # Play audio
        try:
            # Try different audio players
            if os.name == 'nt':  # Windows
                os.system(f'start {temp_path}')
            elif os.name == 'posix':  # macOS/Linux
                if os.system('which afplay > /dev/null 2>&1') == 0:  # macOS
                    os.system(f'afplay {temp_path}')
                elif os.system('which mpg123 > /dev/null 2>&1') == 0:
                    os.system(f'mpg123 {temp_path} > /dev/null 2>&1')
                elif os.system('which play > /dev/null 2>&1') == 0:
                    os.system(f'play {temp_path} > /dev/null 2>&1')
                else:
                    print("Install mpg123 or sox for audio playback")
            
            if not blocking:
                await asyncio.sleep(1)  # Give time for playback to start
            else:
                # Estimate playback time (rough: ~150 words per minute)
                word_count = len(text.split())
                duration = (word_count / 150) * 60 + 1  # seconds
                await asyncio.sleep(duration)
                
        finally:
            # Cleanup temp file
            try:
                await asyncio.sleep(2)
                os.unlink(temp_path)
            except:
                pass
    
    async def stop_speaking(self):
        """Stop current speech"""
        if self.engine_type == 'pyttsx3':
            try:
                await asyncio.to_thread(self.engine.stop)
            except:
                pass
    
    async def set_voice(self, voice_id: str):
        """Change voice"""
        if self.engine_type == 'pyttsx3':
            voices = self.engine.getProperty('voices')
            if voice_id.isdigit() and int(voice_id) < len(voices):
                self.engine.setProperty('voice', voices[int(voice_id)].id)
    
    async def set_rate(self, rate: int):
        """Change speaking rate"""
        if self.engine_type == 'pyttsx3':
            self.rate = rate
            self.engine.setProperty('rate', rate)
    
    async def shutdown(self):
        """Cleanup"""
        if self.engine_type == 'pyttsx3':
            await self.stop_speaking()
        self.enabled = False
