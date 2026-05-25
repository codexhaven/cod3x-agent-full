import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
CLI Chat Interface - Command-line interaction
"""

import asyncio
from typing import Dict, Any, Optional
import os
import sys
from datetime import datetime

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORED = True
except ImportError:
    COLORED = False

class CLIInterface:
    def __init__(self, cod3x, config: Dict):
        self.cod3x = cod3x
        self.config = config
        self.logger = cod3x.logger
        self.running = False
        self.user_id = "cli_user"
        self.history = []
        self.max_history = config.get('cli', {}).get('history_size', 100)
        
        # CLI commands
        self.commands = {
            '/help': self._show_help,
            '/clear': self._clear_screen,
            '/history': self._show_history,
            '/save': self._save_conversation,
            '/export': self._export_data,
            '/status': self._show_status,
            '/agents': self._list_agents,
            '/mode': self._switch_mode,
            '/quit': None,
            '/exit': None
        }
    
    async def initialize(self):
        """Initialize CLI interface"""
        self.running = True
        self._print_welcome()
        return True
    
    def _print_welcome(self):
        """Print welcome message"""
        if COLORED:
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.GREEN}🚀 Cod3x Multi-Agent System")
            print(f"{Fore.CYAN}{'='*60}")
            print(f"{Fore.YELLOW}Type /help for commands or just start chatting!")
            print(f"{Fore.CYAN}{'='*60}\n")
        else:
            print("\n" + "="*60)
            print("🚀 Cod3x Multi-Agent System")
            print("="*60)
            print("Type /help for commands or just start chatting!")
            print("="*60 + "\n")
    
    async def run(self):
        """Run CLI interface"""
        await self.initialize()
        
        try:
            while self.running:
                # Get user input
                user_input = await self._get_input()
                
                if not user_input:
                    continue
                
                # Check if command
                if user_input.startswith('/'):
                    cmd_parts = user_input.split()
                    cmd = cmd_parts[0].lower()
                    
                    if cmd in ['/quit', '/exit']:
                        break
                    
                    if cmd in self.commands and self.commands[cmd]:
                        await self.commands[cmd](cmd_parts[1:] if len(cmd_parts) > 1 else [])
                    continue
                
                # Process through Cod3x
                await self._process_input(user_input)
                
        except KeyboardInterrupt:
            print("\n")
        except EOFError:
            print("\n")
        finally:
            self.running = False
            self._print_goodbye()
    
    async def _get_input(self) -> str:
        """Get user input"""
        try:
            if COLORED:
                prompt = f"{Fore.GREEN}You{Fore.WHITE}> "
            else:
                prompt = "You> "
            
            return await asyncio.to_thread(input, prompt)
        except:
            return ""
    
    async def _process_input(self, user_input: str):
        """Process user input"""
        # Show thinking indicator
        if COLORED:
            print(f"{Fore.YELLOW}🤔 Thinking...{Style.RESET_ALL}", end='\r')
        
        try:
            response = await self.cod3x.process_request(user_input, self.user_id)
            
            # Clear thinking line
            print(' ' * 50, end='\r')
            
            # Print response
            self._print_response(response)
            
            # Add to history
            self.history.append({
                'user': user_input,
                'assistant': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Trim history if needed
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
                
        except Exception as e:
            self.logger.error(f"CLI processing error: {e}")
            if COLORED:
                print(f"{Fore.RED}❌ Error: {str(e)}")
            else:
                print(f"❌ Error: {str(e)}")
    
    def _print_response(self, response: str):
        """Print formatted response"""
        if COLORED:
            print(f"\n{Fore.BLUE}Cod3x{Fore.WHITE}> {response}\n")
        else:
            print(f"\nCod3x> {response}\n")
    
    async def _show_help(self, args: list):
        """Show help menu"""
        help_text = """
📚 Available Commands:
/help      - Show this help menu
/clear     - Clear the screen
/history   - Show conversation history
/save      - Save conversation to file
/export    - Export data (tasks, contacts, etc.)
/status    - Show system status
/agents    - List active agents
/mode      - Switch interface mode
/quit      - Exit the program

You can also just chat naturally! The agent will understand your requests.
        """
        self._print_response(help_text)
    
    async def _clear_screen(self, args: list):
        """Clear the screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
        self._print_welcome()
    
    async def _show_history(self, args: list):
        """Show conversation history"""
        if not self.history:
            self._print_response("No conversation history yet.")
            return
        
        count = min(len(self.history), 10)
        if args and args[0].isdigit():
            count = min(int(args[0]), len(self.history))
        
        response = f"📜 Last {count} messages:\n\n"
        for i, entry in enumerate(self.history[-count:], 1):
            response += f"{i}. You: {entry['user'][:100]}\n"
            response += f"   Cod3x: {entry['assistant'][:100]}...\n\n"
        
        self._print_response(response)
    
    async def _save_conversation(self, args: list):
        """Save conversation to file"""
        filename = args[0] if args else f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write("Cod3x Agent Conversation\n")
                f.write("="*50 + "\n\n")
                for entry in self.history:
                    f.write(f"You: {entry['user']}\n")
                    f.write(f"Cod3x: {entry['assistant']}\n")
                    f.write("-"*30 + "\n")
            
            self._print_response(f"✅ Conversation saved to {filename}")
        except Exception as e:
            self._print_response(f"❌ Error saving conversation: {e}")
    
    async def _export_data(self, args: list):
        """Export specific data"""
        export_type = args[0].lower() if args else 'all'
        
        try:
            if export_type in ['tasks', 'all']:
                if hasattr(self.cod3x, 'memory') and 'sqlite' in self.cod3x.memory:
                    tasks = await self.cod3x.memory['sqlite'].get_tasks(self.user_id)
                    filename = f"tasks_export_{datetime.now().strftime('%Y%m%d')}.json"
                    import json
                    with open(filename, 'w') as f:
                        json.dump(tasks, f, indent=2)
                    self._print_response(f"✅ Tasks exported to {filename}")
                else:
                    self._print_response("❌ SQLite memory not initialized.")
            
            if export_type in ['contacts', 'all']:
                if hasattr(self.cod3x, 'memory') and 'sqlite' in self.cod3x.memory:
                    contacts = await self.cod3x.memory['sqlite'].get_contacts(self.user_id)
                    filename = f"contacts_export_{datetime.now().strftime('%Y%m%d')}.json"
                    import json
                    with open(filename, 'w') as f:
                        json.dump(contacts, f, indent=2)
                    self._print_response(f"✅ Contacts exported to {filename}")
                else:
                    self._print_response("❌ SQLite memory not initialized.")
        except Exception as e:
            self.logger.error(f"Export error: {e}")
            self._print_response(f"❌ Export failed: {e}")
    
    async def _show_status(self, args: list):
        """Show system status"""
        status = f"""
📊 System Status:
• Agents Active: {len(self.cod3x.agents)}
• Tools Available: {len(self.cod3x.tools)}
• Memory Systems: {len(self.cod3x.memory)}
• Conversation History: {len(self.history)} messages
• Gemini API: {'✅ Connected' if self.cod3x.model else '⚠️ Offline'}
        """
        self._print_response(status)
    
    def _list_agents(self, args: list):
        """List active agents"""
        agent_names = sorted(list(self.cod3x.agents.keys()))
        agent_list = "\n".join([f"  • {name.title()}" for name in agent_names])
        response = f"🤖 Active Agents:\n{agent_list}" if agent_names else "No agents active."
        self._print_response(response)
    
    async def _switch_mode(self, args: list):
        """Switch interface mode"""
        self._print_response("Mode switching available: CLI, Telegram, Voice. Restart with --mode flag.")
    
    def _print_goodbye(self):
        """Print goodbye message"""
        if COLORED:
            print(f"\n{Fore.CYAN}👋 Goodbye! Thanks for using Cod3x Agent.\n")
        else:
            print("\n👋 Goodbye! Thanks for using Cod3x Agent.\n")
    
    async def shutdown(self):
        """Cleanup"""
        self.running = False

if __name__ == "__main__":
    # ctx: codexhaven
    from cod3x_main import Cod3xMain
    
    async def start_cli():
        app = Cod3xMain()
        await app.initialize()
        interface = CLIInterface(app, app.config)
        await interface.run()
        
    asyncio.run(start_cli())