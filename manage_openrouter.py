#!/usr/bin/env python3
"""
OpenRouter Backend Configuration Manager for Open WebUI

🎯 PURPOSE: Configure the BACKEND authentication and API settings for OpenRouter
   - This script sets up the Docker environment variables needed for authentication
   - After running this, you still need to manually add specific models in the Open WebUI interface
   - Think of this as "setting up your internet connection" before "choosing which apps to install"

📋 WORKFLOW:
   1. Run this script to configure backend API authentication
   2. Restart Docker to load the new environment variables  
   3. Manually add specific models in Open WebUI Admin Panel → Connections
   4. Models will then appear in your model selector dropdown

🔑 WHY BOTH ARE NEEDED:
   - This script: Provides the API key so Docker can authenticate with OpenRouter
   - Manual UI: Tells Open WebUI which specific models you want to use
   - Without this script: Manual UI model addition will fail with authentication errors
   - Without manual UI: You have authentication but no models registered
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add the module_venv path for venv management
sys.path.insert(0, os.path.expanduser("~/py-utils"))

try:
    import module_venv
    # Setup virtual environment with auto-switching
    auto_venv = module_venv.AutoVirtualEnvironment(
        custom_name="openrouter-manager",
        auto_packages=["python-dotenv", "requests", "rich"]
    )
    auto_venv.auto_switch()
except ImportError:
    print("⚠️  Warning: module_venv not found. Installing dependencies globally...")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.columns import Columns
    from dotenv import load_dotenv, set_key, unset_key
    import requests
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Installing required packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv", "requests", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.columns import Columns
    from dotenv import load_dotenv, set_key, unset_key
    import requests

console = Console()

class OpenRouterManager:
    def __init__(self):
        self.env_file = Path(".env")
        self.docker_compose_file = Path("docker-compose.yaml")
        self.config = self.load_config()
        self.model_queue = []  # Queue for models to be added manually

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

    def show_header(self):
        """Display the application header"""
        console.clear()
        header = Panel(
            "🔧 OpenRouter Backend Configuration Manager\n" +
            "🎯 Purpose: Configure API authentication for Docker container\n" +
            "📋 Next Step: Manually add specific models in Open WebUI interface",
            style="bold bright_blue"
        )
        console.print(header)

    def show_workflow_info(self):
        """Display the workflow information"""
        workflow = Panel(
            "📋 Complete Workflow:\n" +
            "1. 🔧 Configure API key (this script)\n" +
            "2. 🐳 Restart Docker services (this script)\n" +
            "3. 🖥️  Add specific models in UI (Admin Panel → Connections)\n" +
            "4. ✅ Models appear in Open WebUI dropdown",
            title="How OpenRouter Integration Works",
            style="bright_cyan"
        )
        console.print(workflow)

    def show_status(self):
        """Display current configuration status"""
        status_table = Table(title="📊 Backend Configuration Status")
        status_table.add_column("Setting", style="bright_cyan")
        status_table.add_column("Value", style="bright_green")
        status_table.add_column("Status", style="bright_yellow")
        
        # API Status
        api_enabled = self.config['ENABLE_OPENROUTER_API'].lower() == 'true'
        status_table.add_row("🔌 API Enabled", self.config['ENABLE_OPENROUTER_API'], "✅ Ready" if api_enabled else "❌ Disabled")
        
        # API Key Status
        key = self.config['OPENROUTER_API_KEY']
        if key:
            masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key
            status = "✅ Configured"
        else:
            masked_key = "Not set"
            status = "❌ Missing"
        status_table.add_row("🔑 API Key", masked_key, status)
        
        # Base URL
        status_table.add_row("🌐 Base URL", self.config['OPENROUTER_API_BASE_URL'], "✅ Set")
        
        # Next steps
        if key and api_enabled:
            next_step = "✅ Ready for UI model addition"
        else:
            next_step = "⚠️  Configure API key first"
        status_table.add_row("📋 Next Step", "Add models in UI", next_step)
        
        console.print(status_table)

    def show_menu(self):
        """Display the main menu"""
        console.print("\n🎯 Backend Configuration Menu:")
        console.print("1. 🔧 Configure OpenRouter API Authentication")
        console.print("2. 📊 View Current Backend Configuration")
        console.print("3. 🧪 Test OpenRouter API Connection")
        console.print("4. 🔍 Discover & Queue Models for UI Addition")
        console.print("5. 📋 View Queued Models & Copy Instructions")
        console.print("6. 🐳 Restart Docker Services")
        console.print("7. 📝 Generate .env Template")
        console.print("8. ❓ Help & UI Addition Guide")
        console.print("9. 🚪 Exit")

    def configure_api(self):
        """Configure OpenRouter API settings"""
        console.clear()
        console.print(Panel("🔧 OpenRouter Backend API Configuration", style="bold bright_blue"))
        
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
                    console.print("✅ API key updated", style="bright_green")
            
            # Base URL
            console.print("\n🌐 Base URL Configuration")
            current_url = self.config['OPENROUTER_API_BASE_URL']
            console.print(f"Current URL: {current_url}")
            
            if Confirm.ask("Use custom base URL?", default=False):
                new_url = Prompt.ask("Enter custom base URL", default=current_url)
                self.config['OPENROUTER_API_BASE_URL'] = new_url
        
        # Save configuration
        self.save_config()
        console.print("\n💾 Backend configuration saved!", style="bright_green")
        console.print("📋 Next step: Restart Docker and add models in UI", style="bright_cyan")
        input("\nPress Enter to continue...")

    def view_config(self):
        """Display current configuration"""
        console.clear()
        console.print(Panel("📊 Current OpenRouter Backend Configuration", style="bold bright_blue"))
        
        config_table = Table(title="Backend Configuration Details")
        config_table.add_column("Setting", style="bright_cyan")
        config_table.add_column("Value", style="bright_green")
        config_table.add_column("Status", style="bright_yellow")
        
        # API Enabled
        enabled = self.config['ENABLE_OPENROUTER_API'].lower() == 'true'
        config_table.add_row("API Enabled", self.config['ENABLE_OPENROUTER_API'], "✅ Ready" if enabled else "❌ Disabled")
        
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
        config_table.add_row("Base URL", self.config['OPENROUTER_API_BASE_URL'], "✅ Set")
        
        console.print(config_table)
        
        # Environment file status
        if self.env_file.exists():
            console.print(f"\n📁 Configuration file: {self.env_file.absolute()}", style="bright_cyan")
        else:
            console.print("\n⚠️  No .env file found", style="bright_red")
        
        # Next steps
        if key and enabled:
            console.print("\n✅ Backend ready! Next: Add models in Open WebUI interface", style="bright_green")
        else:
            console.print("\n⚠️  Configure API key to proceed", style="bright_yellow")
        
        input("\nPress Enter to continue...")

    def test_connection(self):
        """Test OpenRouter API connection"""
        console.clear()
        console.print(Panel("🧪 Testing OpenRouter Backend Connection", style="bold bright_blue"))
        
        if not self.config['OPENROUTER_API_KEY']:
            console.print("❌ No API key configured. Please configure the API first.", style="bright_red")
            input("\nPress Enter to continue...")
            return
        
        try:
            console.print("🔄 Testing backend authentication...", style="bright_yellow")
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
                console.print(f"✅ Backend connection successful!", style="bright_green")
                console.print(f"📊 API authenticated with access to {model_count} models", style="bright_cyan")
                console.print("🎯 Ready for UI model addition!", style="bright_green")
                
                # Show a few example models for reference
                if model_count > 0:
                    console.print("\n🤖 Sample models available:")
                    for model in data['data'][:3]:
                        console.print(f"  • {model.get('id', 'Unknown')}", style="dim white")
                    console.print(f"  ... and {model_count - 3} more", style="dim white")
            else:
                console.print(f"❌ Backend authentication failed: HTTP {response.status_code}", style="bright_red")
                console.print(f"Response: {response.text[:200]}...", style="dim white")
                console.print("💡 Check your API key configuration", style="bright_yellow")
                
        except requests.exceptions.RequestException as e:
            console.print(f"❌ Connection error: {str(e)}", style="bright_red")
        except Exception as e:
            console.print(f"❌ Unexpected error: {str(e)}", style="bright_red")
        
        input("\nPress Enter to continue...")

    def restart_docker(self):
        """Restart Docker services"""
        console.clear()
        console.print(Panel("🐳 Restart Docker Services", style="bold bright_blue"))
        
        if not self.docker_compose_file.exists():
            console.print("❌ docker-compose.yaml not found", style="bright_red")
            input("\nPress Enter to continue...")
            return
        
        console.print("🎯 This will restart Open WebUI with your new OpenRouter configuration", style="bright_cyan")
        
        if Confirm.ask("Restart Open WebUI Docker services?"):
            try:
                console.print("🔄 Stopping services...", style="bright_yellow")
                # Stop services
                subprocess.run(['docker-compose', 'down'], check=True, capture_output=True)
                console.print("🔄 Starting services with new configuration...", style="bright_yellow")
                # Start services
                subprocess.run(['docker-compose', 'up', '-d'], check=True, capture_output=True)
                
                console.print("✅ Services restarted successfully!", style="bright_green")
                console.print("🌐 Open WebUI available at: http://localhost", style="bright_cyan")
                console.print("📋 Next: Add specific models in Admin Panel → Connections", style="bright_yellow")
                
            except subprocess.CalledProcessError as e:
                console.print(f"❌ Failed to restart services: {e}", style="bright_red")
            except FileNotFoundError:
                console.print("❌ Docker Compose not found. Please install Docker Compose.", style="bright_red")
        
        input("\nPress Enter to continue...")

    def generate_env(self):
        """Generate .env template"""
        console.clear()
        console.print(Panel("📝 Generate .env Template", style="bold bright_blue"))
        
        template = """# OpenRouter Backend Configuration for Open WebUI
# Get your API key from: https://openrouter.ai/keys

# Enable/disable OpenRouter API integration (backend authentication)
ENABLE_OPENROUTER_API=true

# Your OpenRouter API key (required for Docker container authentication)
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

# NOTE: After configuring this file:
# 1. Restart Docker services to load the environment variables
# 2. Manually add specific models in Open WebUI Admin Panel → Connections
"""
        
        if self.env_file.exists():
            if not Confirm.ask(f".env file already exists. Overwrite?"):
                input("\nPress Enter to continue...")
                return
        
        with open(self.env_file, 'w') as f:
            f.write(template)
        
        console.print(f"✅ Template generated: {self.env_file.absolute()}", style="bright_green")
        console.print("\n📝 Please edit the file and add your actual API keys", style="bright_cyan")
        console.print("📋 Remember: This is only the backend configuration", style="bright_yellow")
        
        input("\nPress Enter to continue...")

    def discover_and_queue_models(self):
        """Enhanced model discovery with queuing and better descriptions"""
        console.clear()
        console.print(Panel("🔍 Discover Models & Queue for UI Addition", style="bold bright_blue"))
        
        if not self.config['OPENROUTER_API_KEY']:
            console.print("❌ No API key configured. Please configure the API first.", style="bright_red")
            input("\nPress Enter to continue...")
            return
        
        try:
            console.print("🔄 Fetching models with detailed information...", style="bright_yellow")
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
                    console.print("❌ No models found", style="bright_red")
                    input("\nPress Enter to continue...")
                    return
                
                # Categorize models by provider/purpose
                categorized_models = self.categorize_models(models)
                
                # Show categories
                console.print("\n📂 Available Model Categories:")
                for i, (category, model_list) in enumerate(categorized_models.items(), 1):
                    console.print(f"{i}. {category} ({len(model_list)} models)")
                
                # Let user select category
                category_choice = Prompt.ask(
                    "\nSelect category to explore", 
                    choices=[str(i) for i in range(1, len(categorized_models) + 1)]
                )
                
                selected_category = list(categorized_models.keys())[int(category_choice) - 1]
                selected_models = categorized_models[selected_category]
                
                # Show models in selected category
                self.show_category_models(selected_category, selected_models)
                
            else:
                console.print(f"❌ Failed to fetch models: HTTP {response.status_code}", style="bright_red")
                
        except requests.exceptions.RequestException as e:
            console.print(f"❌ Connection error: {str(e)}", style="bright_red")
        except Exception as e:
            console.print(f"❌ Unexpected error: {str(e)}", style="bright_red")
        
        input("\nPress Enter to continue...")

    def categorize_models(self, models: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize models by provider and purpose"""
        categories = {
            "🔍 Web Search & Real-time Info": [],
            "💬 Conversational AI (GPT-style)": [],
            "🧠 Advanced Reasoning (Claude)": [],
            "🚀 Open Source (Llama, Mistral)": [],
            "💰 Budget-friendly": [],
            "🎨 Creative & Content": [],
            "⚡ Fast & Efficient": [],
            "🔬 Specialized (Code, Math, etc.)": []
        }
        
        for model in models:
            model_id = model.get('id', '').lower()
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '999')) if pricing.get('prompt') else 999
            
            # Enhanced model with purpose description
            enhanced_model = {
                **model,
                'purpose_description': self.get_model_purpose(model_id),
                'price_per_1m': prompt_price * 1000000 if prompt_price < 999 else None
            }
            
            # Categorize based on model ID and characteristics
            if 'perplexity' in model_id or 'search' in model_id:
                categories["�� Web Search & Real-time Info"].append(enhanced_model)
            elif 'gpt' in model_id or 'openai' in model_id:
                categories["💬 Conversational AI (GPT-style)"].append(enhanced_model)
            elif 'claude' in model_id or 'anthropic' in model_id:
                categories["🧠 Advanced Reasoning (Claude)"].append(enhanced_model)
            elif any(x in model_id for x in ['llama', 'mistral', 'qwen', 'gemma', 'phi']):
                categories["🚀 Open Source (Llama, Mistral)"].append(enhanced_model)
            elif prompt_price < 0.001:  # Less than $1 per 1M tokens
                categories["💰 Budget-friendly"].append(enhanced_model)
            elif any(x in model_id for x in ['creative', 'story', 'novel']):
                categories["🎨 Creative & Content"].append(enhanced_model)
            elif any(x in model_id for x in ['fast', 'turbo', 'instant']):
                categories["⚡ Fast & Efficient"].append(enhanced_model)
            elif any(x in model_id for x in ['code', 'math', 'science']):
                categories["🔬 Specialized (Code, Math, etc.)"].append(enhanced_model)
            else:
                categories["💬 Conversational AI (GPT-style)"].append(enhanced_model)
        
        # Remove empty categories and sort models by price
        return {k: sorted(v, key=lambda x: x.get('price_per_1m', 999)) 
                for k, v in categories.items() if v}

    def get_model_purpose(self, model_id: str) -> str:
        """Get purpose description for a model"""
        model_id = model_id.lower()
        
        purpose_map = {
            # Perplexity models
            'perplexity/llama-3.1-sonar-large-128k-online': 'Real-time web search with large context',
            'perplexity/llama-3.1-sonar-huge-128k-online': 'Most powerful web search model',
            'perplexity/llama-3.1-sonar-small-128k-online': 'Fast, cost-effective web search',
            
            # OpenAI models
            'openai/gpt-4o': 'Latest GPT-4 with vision and multimodal capabilities',
            'openai/gpt-4o-mini': 'Smaller, faster version of GPT-4o',
            'openai/gpt-4-turbo': 'High-performance GPT-4 for complex tasks',
            
            # Claude models
            'anthropic/claude-3.5-sonnet': 'Best Claude model for reasoning and analysis',
            'anthropic/claude-3-haiku': 'Fast Claude model for simple tasks',
            'anthropic/claude-3-opus': 'Most powerful Claude model',
            
            # Llama models
            'meta-llama/llama-3.1-405b-instruct': 'Largest open-source model, exceptional capabilities',
            'meta-llama/llama-3.1-70b-instruct': 'Balanced open-source model',
            'meta-llama/llama-3.1-8b-instruct': 'Fast, efficient open-source model',
        }
        
        # Check for exact matches first
        if model_id in purpose_map:
            return purpose_map[model_id]
        
        # Check for partial matches
        if 'perplexity' in model_id and 'online' in model_id:
            return 'Real-time web search and current information'
        elif 'gpt-4' in model_id:
            return 'Advanced conversational AI with strong reasoning'
        elif 'claude' in model_id:
            return 'Anthropic\'s AI with excellent reasoning and safety'
        elif 'llama' in model_id:
            return 'Meta\'s open-source AI model'
        elif 'mistral' in model_id:
            return 'Mistral\'s efficient open-source AI'
        elif 'code' in model_id:
            return 'Specialized for programming and code generation'
        elif 'math' in model_id:
            return 'Optimized for mathematical reasoning'
        else:
            return 'General-purpose AI model'

    def show_category_models(self, category: str, models: List[Dict]):
        """Show models in a category and allow queuing"""
        console.clear()
        console.print(Panel(f"📂 {category}", style="bold bright_blue"))
        
        # Create detailed table
        table = Table(title=f"Models in {category} (sorted by price)")
        table.add_column("ID", style="bright_cyan", no_wrap=True)
        table.add_column("Purpose", style="bright_green")
        table.add_column("Context", style="bright_yellow")
        table.add_column("Price/1M", style="bright_red")
        table.add_column("Queue", style="bright_magenta")
        
        for i, model in enumerate(models[:20], 1):  # Show first 20
            model_id = model.get('id', 'Unknown')
            purpose = model.get('purpose_description', 'General AI model')
            context = str(model.get('context_length', 'Unknown'))
            
            price_per_1m = model.get('price_per_1m')
            if price_per_1m:
                price_str = f"${price_per_1m:.2f}"
            else:
                price_str = "N/A"
            
            # Check if already queued
            queued = "✅" if any(q['id'] == model_id for q in self.model_queue) else f"[{i}]"
            
            table.add_row(
                model_id,
                purpose[:50] + "..." if len(purpose) > 50 else purpose,
                context,
                price_str,
                queued
            )
        
        console.print(table)
        
        if len(models) > 20:
            console.print(f"\n... and {len(models) - 20} more models in this category", style="dim white")
        
        # Allow queuing models
        console.print(f"\n🎯 Queue models for UI addition:")
        console.print("• Enter model numbers to queue (e.g., '1,3,5' or '1-3')")
        console.print("• Type 'all' to queue all models in this category")
        console.print("• Press Enter to go back")
        
        selection = Prompt.ask("Select models to queue", default="")
        
        if selection.strip():
            self.process_model_selection(selection, models[:20])

    def process_model_selection(self, selection: str, models: List[Dict]):
        """Process user's model selection and add to queue"""
        try:
            if selection.lower() == 'all':
                indices = list(range(len(models)))
            else:
                indices = []
                for part in selection.split(','):
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        indices.extend(range(start-1, end))
                    else:
                        indices.append(int(part) - 1)
            
            added = 0
            for i in indices:
                if 0 <= i < len(models):
                    model = models[i]
                    if not any(q['id'] == model['id'] for q in self.model_queue):
                        self.model_queue.append({
                            'id': model['id'],
                            'purpose': model.get('purpose_description', ''),
                            'context_length': model.get('context_length'),
                            'pricing': model.get('pricing', {}),
                            'recommended_name': self.generate_friendly_name(model['id'])
                        })
                        added += 1
            
            console.print(f"\n✅ Added {added} models to queue", style="bright_green")
            
        except ValueError:
            console.print("❌ Invalid selection format", style="bright_red")
        
        input("\nPress Enter to continue...")

    def generate_friendly_name(self, model_id: str) -> str:
        """Generate a user-friendly name for a model"""
        # Extract key parts and make readable
        parts = model_id.split('/')
        if len(parts) == 2:
            provider, model = parts
            
            # Clean up provider names
            provider_names = {
                'openai': 'OpenAI',
                'anthropic': 'Claude',
                'perplexity': 'Perplexity',
                'meta-llama': 'Llama',
                'mistralai': 'Mistral'
            }
            
            clean_provider = provider_names.get(provider, provider.title())
            
            # Clean up model names
            clean_model = model.replace('-', ' ').replace('_', ' ').title()
            
            # Special cases
            if 'sonar' in model.lower() and 'online' in model.lower():
                clean_model += ' (Web Search)'
            elif 'gpt-4o' in model.lower():
                clean_model = clean_model.replace('4O', '4o')
            
            return f"{clean_provider} {clean_model}"
        
        return model_id.replace('-', ' ').replace('_', ' ').title()

    def view_queued_models(self):
        """View queued models and provide copy-paste instructions"""
        console.clear()
        console.print(Panel("📋 Queued Models for UI Addition", style="bold bright_blue"))
        
        if not self.model_queue:
            console.print("📭 No models queued yet. Use 'Discover & Queue Models' first.", style="bright_yellow")
            input("\nPress Enter to continue...")
            return
        
        # Show queued models
        queue_table = Table(title=f"Models Ready for UI Addition ({len(self.model_queue)} total)")
        queue_table.add_column("#", style="dim white")
        queue_table.add_column("Recommended Name", style="bright_green")
        queue_table.add_column("Model ID", style="bright_cyan")
        queue_table.add_column("Purpose", style="bright_yellow")
        queue_table.add_column("Action", style="bright_magenta")
        
        for i, model in enumerate(self.model_queue, 1):
            queue_table.add_row(
                str(i),
                model['recommended_name'],
                model['id'],
                model['purpose'][:40] + "..." if len(model['purpose']) > 40 else model['purpose'],
                f"[{i}] Remove"
            )
        
        console.print(queue_table)
        
        # Show copy-paste instructions
        console.print("\n📋 UI Addition Instructions:")
        instruction_panel = Panel(
            "1. Go to Open WebUI → Admin Panel → Settings → Connections\n" +
            "2. Click '+' to add a new Direct Connection\n" +
            "3. For each model below, create a new connection with:\n" +
            "   • URL: https://openrouter.ai/api/v1\n" +
            f"   • API Key: {self.config['OPENROUTER_API_KEY'][:8]}...{self.config['OPENROUTER_API_KEY'][-4:] if self.config['OPENROUTER_API_KEY'] else 'YOUR_KEY'}\n" +
            "   • Name: Use the 'Recommended Name' from the table\n" +
            "   • Model: Copy the 'Model ID' exactly",
            style="bright_cyan"
        )
        console.print(instruction_panel)
        
        # Action menu
        console.print("\n🎯 Actions:")
        console.print("• Enter model numbers to remove (e.g., '1,3,5')")
        console.print("• Type 'export' to save to file")
        console.print("• Type 'clear' to clear all")
        console.print("• Press Enter to go back")
        
        action = Prompt.ask("Action", default="")
        
        if action.strip():
            self.process_queue_action(action)

    def process_queue_action(self, action: str):
        """Process actions on the model queue"""
        if action.lower() == 'clear':
            if Confirm.ask("Clear all queued models?"):
                self.model_queue.clear()
                console.print("✅ Queue cleared", style="bright_green")
        
        elif action.lower() == 'export':
            self.export_queue_to_file()
        
        else:
            # Remove specific models
            try:
                indices = [int(x.strip()) - 1 for x in action.split(',')]
                # Remove in reverse order to maintain indices
                for i in sorted(indices, reverse=True):
                    if 0 <= i < len(self.model_queue):
                        removed = self.model_queue.pop(i)
                        console.print(f"✅ Removed {removed['recommended_name']}", style="bright_green")
            except ValueError:
                console.print("❌ Invalid action format", style="bright_red")
        
        input("\nPress Enter to continue...")

    def export_queue_to_file(self):
        """Export queued models to a file for easy reference"""
        if not self.model_queue:
            console.print("❌ No models to export", style="bright_red")
            return
        
        filename = "openrouter_models_to_add.txt"
        
        with open(filename, 'w') as f:
            f.write("OpenRouter Models to Add in Open WebUI\n")
            f.write("=" * 50 + "\n\n")
            f.write("Instructions:\n")
            f.write("1. Go to Open WebUI → Admin Panel → Settings → Connections\n")
            f.write("2. Click '+' to add a new Direct Connection\n")
            f.write("3. For each model below, create a connection with:\n")
            f.write("   • URL: https://openrouter.ai/api/v1\n")
            f.write(f"   • API Key: {self.config['OPENROUTER_API_KEY']}\n")
            f.write("   • Name: Use the name provided\n")
            f.write("   • Model: Copy the Model ID exactly\n\n")
            
            f.write("Models to Add:\n")
            f.write("-" * 20 + "\n\n")
            
            for i, model in enumerate(self.model_queue, 1):
                f.write(f"{i}. {model['recommended_name']}\n")
                f.write(f"   Model ID: {model['id']}\n")
                f.write(f"   Purpose: {model['purpose']}\n")
                f.write(f"   Context: {model.get('context_length', 'Unknown')} tokens\n\n")
        
        console.print(f"✅ Exported to {filename}", style="bright_green")

    def show_help(self):
        """Show help and UI addition guide"""
        console.clear()
        console.print(Panel("❓ OpenRouter Backend Configuration & UI Addition Guide", style="bold bright_blue"))
        
        help_content = """
🎯 UNDERSTANDING THE TWO-STEP PROCESS:

Step 1: Backend Configuration (This Script)
• Sets up API authentication in Docker environment
• Required for Docker container to connect to OpenRouter
• Without this: Manual UI model addition will fail with auth errors

Step 2: UI Model Addition (Manual Process)
• Tells Open WebUI which specific models you want to use
• Creates "Direct Connections" for individual models
• Required for models to appear in the dropdown selector

🔧 BACKEND CONFIGURATION (This Script):
1. Configure your OpenRouter API key
2. Test the connection to verify it works
3. Restart Docker services to load new environment
4. ✅ Backend is now ready for UI model addition

🖥️  UI MODEL ADDITION (Manual Process):
1. Open your browser → http://localhost
2. Go to Admin Panel → Settings → Connections
3. Click '+' to add a new Direct Connection
4. For each model:
   • URL: https://openrouter.ai/api/v1
   • API Key: Your OpenRouter API key
   • Name: A friendly name (e.g., "Perplexity Web Search")
   • Model: The exact model ID (e.g., "perplexity/llama-3.1-sonar-large-128k-online")
5. Test the connection (should show ✅ success)
6. ✅ Model now appears in your dropdown selector

🔍 RECOMMENDED WORKFLOW:
1. Run this script → Configure API
2. Use "Discover & Queue Models" → Research and select models
3. Use "View Queued Models" → Get copy-paste instructions
4. Go to UI → Add each queued model as Direct Connection
5. ✅ Start using your OpenRouter models!

💡 WHY THIS APPROACH:
• Security: API key stored in environment variables
• Performance: Only load models you actually want to use
• Cost Control: Prevents accidental usage of expensive models
• Flexibility: Easy to add/remove models as needed
"""
        
        console.print(help_content, style="bright_cyan")
        input("\nPress Enter to continue...")

    def run(self):
        """Main application loop"""
        try:
            while True:
                self.show_header()
                self.show_workflow_info()
                self.show_status()
                self.show_menu()
                
                choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"])
                
                if choice == "1":
                    self.configure_api()
                elif choice == "2":
                    self.view_config()
                elif choice == "3":
                    self.test_connection()
                elif choice == "4":
                    self.discover_and_queue_models()
                elif choice == "5":
                    self.view_queued_models()
                elif choice == "6":
                    self.restart_docker()
                elif choice == "7":
                    self.generate_env()
                elif choice == "8":
                    self.show_help()
                elif choice == "9":
                    console.clear()
                    console.print("👋 Backend configuration complete! Next: Add models in UI", style="bright_green")
                    break
                
                # Reload config after any changes
                self.config = self.load_config()
                
        except KeyboardInterrupt:
            console.clear()
            console.print("\n👋 Backend configuration saved. Next: Add models in UI", style="bright_green")

if __name__ == "__main__":
    try:
        manager = OpenRouterManager()
        manager.run()
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1) 