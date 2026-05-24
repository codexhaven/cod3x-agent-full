"""
Voice Listener Interface - Speech-to-text input
"""

import asyncio
from typing import Dict, Any, Optional
import os
import sys
from datetime import datetime

class VoiceInterface:
    def __init__(self, cod3x, config: Dict):
        self.cod3x = cod3x
        self.config = config
        self.logger = cod3x.logger
        self.running = False
        self.user_id = "voice_user"
        self.speech_enabled = False
        self.speaker = None
        
        # Voice configuration
        self.wake_word = config.get('voice', {}).get('wake_word', 'hey cod3x')
        self.language = config.get('voice', {}).get('language', 'en-US')
    
    async def initialize(self):
        """Initialize voice interface"""
        try:
            # Try to import speech recognition
            try:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.speech_enabled = True
                self.logger.info("Speech recognition initialized")
            except ImportError:
                self.logger.warning("speech_recognition not installed. Install with: pip install SpeechRecognition")
                self.speech_enabled = False
            
            # Try to import text-to-speech
            try:
                from interface.voice_speaker import VoiceSpeaker
                self.speaker = VoiceSpeaker(config)
                await self.speaker.initialize()
                self.logger.info("Voice speaker initialized")
            except:
                self.logger.warning("Voice speaker not available")
            
            self.running = True
            return True
        except Exception as e:
            self.logger.error(f"Voice init error: {e}")
            return False
    
    async def run(self):
        """Run voice interface"""
        if not await self.initialize():
            self.logger.error("Failed to initialize voice interface")
            print("Voice interface unavailable. Install SpeechRecognition: pip install SpeechRecognition")
            return
        
        print("\n🎤 Voice Interface Active")
        print(f"Wake word: '{self.wake_word}'")
        print("Listening... (Press Ctrl+C to stop)\n")
        
        try:
            while self.running:
                try:
                    # Listen for wake word or command
                    text = await self._listen()
                    
                    if not text:
                        continue
                    
                    print(f"\n🗣️  Heard: {text}")
                    
                    # Check for wake word
                    if self.wake_word.lower() in text.lower():
                        # Remove wake word
                        command = text.lower().replace(self.wake_word.lower(), '').strip()
                        
                        if command:
                            print(f"💭 Processing: {command}")
                            response = await self.cod3x.process_request(command, self.user_id)
                            print(f"🤖 Response: {response[:200]}...")
                            
                            # Speak response
                            if self.speaker:
                                await self.speaker.speak(response)
                        else:
                            response = "Yes? How can I help you?"
                            print(f"🤖 {response}")
                            if self.speaker:
                                await self.speaker.speak(response)
                    else:
                        # Process directly
                        response = await self.cod3x.process_request(text, self.user_id)
                        print(f"🤖 Response: {response[:200]}...")
                        
                        if self.speaker:
                            await self.speaker.speak(response[:500])  # Limit spoken response
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Voice loop error: {e}")
                    await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            print("\n")
        finally:
            self.running = False
    
    async def _listen(self) -> Optional[str]:
        """Listen for speech input"""
        if not self.speech_enabled:
            # Fallback to text input
            return await self._text_input()
        
        try:
            import speech_recognition as sr
            
            with self.microphone as source:
                print("🎤 Listening...", end='\r')
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                try:
                    audio = await asyncio.to_thread(
                        self.recognizer.listen, source, timeout=5, phrase_time_limit=10
                    )
                    
                    print("🔍 Recognizing...", end='\r')
                    
                    text = await asyncio.to_thread(
                        self.recognizer.recognize_google, audio, language=self.language
                    )
                    
                    return text
                    
                except sr.WaitTimeoutError:
                    return None
                except sr.UnknownValueError:
                    print("❓ Didn't catch that...", end='\r')
                    return None
                except sr.RequestError as e:
                    self.logger.error(f"Recognition service error: {e}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Listen error: {e}")
            return None
    
    async def _text_input(self) -> Optional[str]:
        """Fallback text input"""
        try:
            text = await asyncio.to_thread(input, "You (text)> ")
            return text
        except:
            return None
    
    async def shutdown(self):
        """Cleanup"""
        self.running = False
        if self.speaker:
            await self.speaker.shutdown()
