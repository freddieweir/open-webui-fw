#!/usr/bin/env python3
"""
OpenRouter Configuration Manager for Open WebUI
Interactive script to manage OpenRouter API settings
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the module_venv path for venv management
sys.path.insert(0, os.path.expanduser("~/py-utils"))

try:
    import module_venv
    # Setup virtual environment with auto-switching
    auto_venv = module_venv.AutoVirtualEnvironment(
        custom_name="openrouter-manager",
        auto_packages=["python-dotenv", "requests", "rich", "keyboard"]
    )
    auto_venv.auto_switch()
except ImportError:
    print("⚠️  Warning: module_venv not found. Installing dependencies globally...")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich.align import Align
    import keyboard
    from dotenv import load_dotenv, set_key, unset_key
    import requests
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv", "requests", "rich", "keyboard"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    from rich.align import Align
    import keyboard
    from dotenv import load_dotenv, set_key, unset_key
    import requests

console = Console()

class OpenRouterManager:
    def __init__(self):
        self.env_file = Path(".env")
        self.docker_compose_file = Path("docker-compose.yaml")
        self.current_selection = 0
        self.config = self.load_config()
        
        # Color scheme for ADHD-friendly UI
        self.colors = {
            'primary': 'bright_blue',
            'secondary': 'bright_green',
            'accent': 'bright_yellow',
            'warning': 'bright_red',
            'success': 'bright_green',
            'info': 'bright_cyan',
            'muted': 'dim white'
        }
        
        # Menu options
        self.main_menu_options = [
            ("🔧", "Configure OpenRouter API", "configure_api"),
            ("📊", "View Current Configuration", "view_config"),
            ("🧪", "Test OpenRouter Connection", "test_connection"),
            ("🔍", "Browse Available Models", "browse_models"),
            ("🐳", "Restart Docker Services", "restart_docker"),
            ("📝", "Generate .env Template", "generate_env"),
            ("❓", "Help & Documentation", "show_help"),
            ("🚪", "Exit", "exit")
        ]

    def load_config(self) -> Dict:
        """Load current configuration from environment"""
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        return {
            'ENABLE_OPENROUTER_API': os.getenv('ENABLE_OPENROUTER_API', 'true'),
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY', ''),
            'OPENROUTER_API_BASE_URL': os.getenv('OPENROUTER_API_BASE_URL', 'https://openrouter.ai/api/v1'),
        }

    def save_config(self):
        """Save configuration to .env file"""
        if not self.env_file.exists():
            self.env_file.touch()
        
        for key, value in self.config.items():
            if value:
                set_key(self.env_file, key, value)
            else:
                unset_key(self.env_file, key)

    def create_header(self) -> Panel:
        """Create the application header"""
        title = Text("🤖 OpenRouter Configuration Manager", style=f"bold {self.colors['primary']}")
        subtitle = Text("Secure LLM API Integration for Open WebUI", style=self.colors['muted'])
        
        header_content = Align.center(f"{title}\n{subtitle}")
        return Panel(header_content, border_style=self.colors['primary'])

    def create_status_panel(self) -> Panel:
        """Create status panel showing current configuration"""
        status_table = Table(show_header=False, box=None)
        status_table.add_column("Key", style=self.colors['info'])
        status_table.add_column("Value", style=self.colors['secondary'])
        
        # API Status
        api_enabled = self.config['ENABLE_OPENROUTER_API'].lower() == 'true'
        status_table.add_row("🔌 API Status", "✅ Enabled" if api_enabled else "❌ Disabled")
        
        # API Key Status
        has_key = bool(self.config['OPENROUTER_API_KEY'])
        status_table.add_row("🔑 API Key", "✅ Configured" if has_key else "❌ Missing")
        
        # Base URL
        status_table.add_row("🌐 Base URL", self.config['OPENROUTER_API_BASE_URL'] or "Default")
        
        return Panel(status_table, title="📊 Current Status", border_style=self.colors['info'])

    def create_menu(self) -> Panel:
        """Create the main menu with current selection highlighted"""
        menu_table = Table(show_header=False, box=None, padding=(0, 1))
        menu_table.add_column("Icon", width=3)
        menu_table.add_column("Option", min_width=30)
        
        for i, (icon, text, _) in enumerate(self.main_menu_options):
            if i == self.current_selection:
                style = f"bold {self.colors['accent']} on {self.colors['primary']}"
                icon_text = f"👉 {icon}"
            else:
                style = self.colors['secondary']
                icon_text = f"   {icon}"
            
            menu_table.add_row(icon_text, text, style=style)
        
        instructions = Text("\n🎮 Use ↑↓ arrows to navigate, Enter to select, Esc to exit", 
                          style=self.colors['muted'])
        
        return Panel(f"{menu_table}\n{instructions}", 
                    title="🎯 Main Menu", 
                    border_style=self.colors['secondary'])

    def display_main_screen(self):
        """Display the main screen layout"""
        layout = Layout()
        layout.split_column(
            Layout(self.create_header(), size=4),
            Layout().split_row(
                Layout(self.create_status_panel(), ratio=1),
                Layout(self.create_menu(), ratio=2)
            )
        )
        return layout

    def handle_navigation(self) -> str:
        """Handle keyboard navigation and return selected action"""
        with Live(self.display_main_screen(), refresh_per_second=10, screen=True) as live:
            while True:
                try:
                    event = keyboard.read_event()
                    if event.event_type == keyboard.KEY_DOWN:
                        if event.name == 'up':
                            self.current_selection = (self.current_selection - 1) % len(self.main_menu_options)
                            live.update(self.display_main_screen())
                        elif event.name == 'down':
                            self.current_selection = (self.current_selection + 1) % len(self.main_menu_options)
                            live.update(self.display_main_screen())
                        elif event.name == 'enter':
                            return self.main_menu_options[self.current_selection][2]
                        elif event.name == 'esc':
                            return 'exit'
                except KeyboardInterrupt:
                    return 'exit'

    def configure_api(self):
        """Configure OpenRouter API settings"""
        console.clear()
        console.print(Panel("🔧 OpenRouter API Configuration", style=f"bold {self.colors['primary']}"))
        
        # Enable/Disable API
        current_enabled = self.config['ENABLE_OPENROUTER_API'].lower() == 'true'
        enable_api = Confirm.ask(f"Enable OpenRouter API? (currently: {'✅ enabled' if current_enabled else '❌ disabled'})", 
                               default=current_enabled)
        self.config['ENABLE_OPENROUTER_API'] = 'true' if enable_api else 'false'
        
        if enable_api:
            # API Key
            console.print("\n🔑 API Key Configuration")
            current_key = self.config['OPENROUTER_API_KEY']
            if current_key:
                console.print(f"Current key: {current_key[:8]}...{current_key[-4:] if len(current_key) > 12 else current_key}")
                update_key = Confirm.ask("Update API key?", default=False)
            else:
                console.print("❌ No API key configured")
                update_key = True
            
            if update_key:
                new_key = Prompt.ask("Enter your OpenRouter API key", password=True)
                if new_key.strip():
                    self.config['OPENROUTER_API_KEY'] = new_key.strip()
                    console.print("✅ API key updated", style=self.colors['success'])
            
            # Base URL
            console.print("\n🌐 Base URL Configuration")
            current_url = self.config['OPENROUTER_API_BASE_URL']
            console.print(f"Current URL: {current_url}")
            
            if Confirm.ask("Use custom base URL?", default=False):
                new_url = Prompt.ask("Enter custom base URL", default=current_url)
                self.config['OPENROUTER_API_BASE_URL'] = new_url
        
        # Save configuration
        self.save_config()
        console.print("\n💾 Configuration saved!", style=self.colors['success'])
        console.input("\nPress Enter to continue...")

    def view_config(self):
        """Display current configuration"""
        console.clear()
        console.print(Panel("📊 Current OpenRouter Configuration", style=f"bold {self.colors['primary']}"))
        
        config_table = Table(title="Configuration Details")
        config_table.add_column("Setting", style=self.colors['info'])
        config_table.add_column("Value", style=self.colors['secondary'])
        config_table.add_column("Status", style=self.colors['accent'])
        
        # API Enabled
        enabled = self.config['ENABLE_OPENROUTER_API'].lower() == 'true'
        config_table.add_row(
            "API Enabled",
            self.config['ENABLE_OPENROUTER_API'],
            "✅ Active" if enabled else "❌ Inactive"
        )
        
        # API Key
        key = self.config['OPENROUTER_API_KEY']
        if key:
            masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key
            status = "✅ Configured"
        else:
            masked_key = "Not set"
            status = "❌ Missing"
        config_table.add_row("API Key", masked_key, status)
        
        # Base URL
        config_table.add_row(
            "Base URL",
            self.config['OPENROUTER_API_BASE_URL'],
            "✅ Set"
        )
        
        console.print(config_table)
        
        # Environment file status
        if self.env_file.exists():
            console.print(f"\n📁 Configuration file: {self.env_file.absolute()}", style=self.colors['info'])
        else:
            console.print("\n⚠️  No .env file found", style=self.colors['warning'])
        
        console.input("\nPress Enter to continue...")

    def test_connection(self):
        """Test OpenRouter API connection"""
        console.clear()
        console.print(Panel("🧪 Testing OpenRouter Connection", style=f"bold {self.colors['primary']}"))
        
        if not self.config['OPENROUTER_API_KEY']:
            console.print("❌ No API key configured. Please configure the API first.", style=self.colors['warning'])
            console.input("\nPress Enter to continue...")
            return
        
        try:
            with console.status("[bold green]Testing connection..."):
                headers = {
                    'Authorization': f"Bearer {self.config['OPENROUTER_API_KEY']}",
                    'Content-Type': 'application/json'
                }
                
                response = requests.get(
                    f"{self.config['OPENROUTER_API_BASE_URL']}/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get('data', []))
                    console.print(f"✅ Connection successful!", style=self.colors['success'])
                    console.print(f"📊 Found {model_count} available models", style=self.colors['info'])
                    
                    # Show a few example models
                    if model_count > 0:
                        console.print("\n🤖 Sample available models:")
                        for model in data['data'][:5]:
                            console.print(f"  • {model.get('id', 'Unknown')}", style=self.colors['muted'])
                        if model_count > 5:
                            console.print(f"  ... and {model_count - 5} more", style=self.colors['muted'])
                else:
                    console.print(f"❌ Connection failed: HTTP {response.status_code}", style=self.colors['warning'])
                    console.print(f"Response: {response.text[:200]}...", style=self.colors['muted'])
                    
        except requests.exceptions.RequestException as e:
            console.print(f"❌ Connection error: {str(e)}", style=self.colors['warning'])
        except Exception as e:
            console.print(f"❌ Unexpected error: {str(e)}", style=self.colors['warning'])
        
        console.input("\nPress Enter to continue...")

    def browse_models(self):
        """Browse available OpenRouter models"""
        console.clear()
        console.print(Panel("🔍 Browse OpenRouter Models", style=f"bold {self.colors['primary']}"))
        
        if not self.config['OPENROUTER_API_KEY']:
            console.print("❌ No API key configured. Please configure the API first.", style=self.colors['warning'])
            console.input("\nPress Enter to continue...")
            return
        
        try:
            with console.status("[bold green]Fetching models..."):
                headers = {
                    'Authorization': f"Bearer {self.config['OPENROUTER_API_KEY']}",
                    'Content-Type': 'application/json'
                }
                
                response = requests.get(
                    f"{self.config['OPENROUTER_API_BASE_URL']}/models",
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('data', [])
                    
                    if not models:
                        console.print("❌ No models found", style=self.colors['warning'])
                        console.input("\nPress Enter to continue...")
                        return
                    
                    # Create models table
                    models_table = Table(title=f"Available Models ({len(models)} total)")
                    models_table.add_column("Model ID", style=self.colors['info'])
                    models_table.add_column("Context", style=self.colors['secondary'])
                    models_table.add_column("Pricing", style=self.colors['accent'])
                    
                    # Sort models by name and show first 20
                    sorted_models = sorted(models, key=lambda x: x.get('id', ''))
                    for model in sorted_models[:20]:
                        model_id = model.get('id', 'Unknown')
                        context_length = model.get('context_length', 'Unknown')
                        pricing = model.get('pricing', {})
                        prompt_price = pricing.get('prompt', 'N/A')
                        
                        models_table.add_row(
                            model_id,
                            str(context_length),
                            f"${prompt_price}/1M tokens" if prompt_price != 'N/A' else 'N/A'
                        )
                    
                    console.print(models_table)
                    
                    if len(models) > 20:
                        console.print(f"\n... and {len(models) - 20} more models available", style=self.colors['muted'])
                    
                    # Highlight Perplexity models for search
                    perplexity_models = [m for m in models if 'perplexity' in m.get('id', '').lower()]
                    if perplexity_models:
                        console.print(f"\n🔍 Found {len(perplexity_models)} Perplexity models for search:", style=self.colors['info'])
                        for model in perplexity_models:
                            console.print(f"  • {model.get('id')}", style=self.colors['secondary'])
                else:
                    console.print(f"❌ Failed to fetch models: HTTP {response.status_code}", style=self.colors['warning'])
                    
        except requests.exceptions.RequestException as e:
            console.print(f"❌ Connection error: {str(e)}", style=self.colors['warning'])
        except Exception as e:
            console.print(f"❌ Unexpected error: {str(e)}", style=self.colors['warning'])
        
        console.input("\nPress Enter to continue...")

    def restart_docker(self):
        """Restart Docker services"""
        console.clear()
        console.print(Panel("🐳 Restart Docker Services", style=f"bold {self.colors['primary']}"))
        
        if not self.docker_compose_file.exists():
            console.print("❌ docker-compose.yaml not found", style=self.colors['warning'])
            console.input("\nPress Enter to continue...")
            return
        
        if Confirm.ask("Restart Open WebUI Docker services?"):
            try:
                with console.status("[bold green]Restarting services..."):
                    # Stop services
                    subprocess.run(['docker-compose', 'down'], check=True, capture_output=True)
                    # Start services
                    subprocess.run(['docker-compose', 'up', '-d'], check=True, capture_output=True)
                
                console.print("✅ Services restarted successfully!", style=self.colors['success'])
                console.print("🌐 Open WebUI should be available shortly", style=self.colors['info'])
                
            except subprocess.CalledProcessError as e:
                console.print(f"❌ Failed to restart services: {e}", style=self.colors['warning'])
            except FileNotFoundError:
                console.print("❌ Docker Compose not found. Please install Docker Compose.", style=self.colors['warning'])
        
        console.input("\nPress Enter to continue...")

    def generate_env(self):
        """Generate .env template"""
        console.clear()
        console.print(Panel("📝 Generate .env Template", style=f"bold {self.colors['primary']}"))
        
        template = """# OpenRouter Configuration for Open WebUI
# Get your API key from: https://openrouter.ai/keys

# Enable/disable OpenRouter API integration
ENABLE_OPENROUTER_API=true

# Your OpenRouter API key
OPENROUTER_API_KEY=your_api_key_here

# OpenRouter API base URL (default is fine for most users)
OPENROUTER_API_BASE_URL=https://openrouter.ai/api/v1

# Other API configurations (optional)
WEBUI_SECRET_KEY=your_secret_key_here
OPENAI_API_KEY=your_openai_key_here
CLAUDE_API_KEY=your_claude_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here

# Docker configuration
WEBUI_DOCKER_TAG=main
"""
        
        if self.env_file.exists():
            if not Confirm.ask(f".env file already exists. Overwrite?"):
                console.input("\nPress Enter to continue...")
                return
        
        with open(self.env_file, 'w') as f:
            f.write(template)
        
        console.print(f"✅ Template generated: {self.env_file.absolute()}", style=self.colors['success'])
        console.print("\n📝 Please edit the file and add your actual API keys", style=self.colors['info'])
        
        console.input("\nPress Enter to continue...")

    def show_help(self):
        """Show help and documentation"""
        console.clear()
        console.print(Panel("❓ Help & Documentation", style=f"bold {self.colors['primary']}"))
        
        help_content = """
🤖 OpenRouter Integration Guide

OpenRouter provides access to multiple AI models through a single API, including:
• Perplexity Sonar models for web search
• Claude, GPT-4, and other premium models
• Cost-effective model routing

📋 Setup Steps:
1. Get API key from https://openrouter.ai/keys
2. Configure API key using this tool
3. Restart Docker services
4. Access models through Open WebUI

🔍 For Perplexity Search:
• Use models like 'perplexity/llama-3.1-sonar-large-128k-online'
• These models can search the web in real-time
• Perfect for current information and research

🔗 Useful Links:
• OpenRouter Dashboard: https://openrouter.ai/
• Model Documentation: https://openrouter.ai/docs
• Open WebUI Docs: https://docs.openwebui.com/

💡 Tips:
• Test connection after configuration
• Browse models to see what's available
• Use environment variables for security
"""
        
        console.print(help_content, style=self.colors['info'])
        console.input("\nPress Enter to continue...")

    def run(self):
        """Main application loop"""
        try:
            while True:
                console.clear()
                action = self.handle_navigation()
                
                if action == 'exit':
                    console.clear()
                    console.print("👋 Goodbye! OpenRouter configuration saved.", style=self.colors['success'])
                    break
                elif action == 'configure_api':
                    self.configure_api()
                elif action == 'view_config':
                    self.view_config()
                elif action == 'test_connection':
                    self.test_connection()
                elif action == 'browse_models':
                    self.browse_models()
                elif action == 'restart_docker':
                    self.restart_docker()
                elif action == 'generate_env':
                    self.generate_env()
                elif action == 'show_help':
                    self.show_help()
                
                # Reload config after any changes
                self.config = self.load_config()
                
        except KeyboardInterrupt:
            console.clear()
            console.print("\n👋 Goodbye! Configuration saved.", style=self.colors['success'])

if __name__ == "__main__":
    try:
        manager = OpenRouterManager()
        manager.run()
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1) 