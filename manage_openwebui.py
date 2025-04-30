#!/usr/bin/env python3
"""
🚀 Open WebUI Manager
Interactive CLI to manage Open WebUI: restart, rebuild, run fix IP script, and update API keys.
"""

import curses
import subprocess
import os
import sys
import shutil  # for locating local Ollama CLI binary
import locale  # ensure Unicode support in curses

ENV_FILE = os.path.join(os.getcwd(), ".env")
FIX_IP_SCRIPT = os.path.join(os.getcwd(), "fix_ip_address.sh")

MENU = [
    "🔄 Restart Open WebUI",
    "🛠️  Rebuild & Deploy Open WebUI",
    "🌐 Fix IP Address",
    "🔑 Update API Keys (.env)",
    "🐙 Manage Ollama Models",
    "🔄 Restart Ollama",
    "🔄 Restart Both Services",
    "🚪 Exit",
]

# Set locale for broad Unicode support
locale.setlocale(locale.LC_ALL, '')

# Utility for safely printing Unicode or wide strings in curses windows
def safe_addstr(win, y, x, text):
    try:
        win.addstr(y, x, text)
    except curses.error:
        # Strip non-ASCII characters as fallback
        ascii_text = ''.join(ch for ch in text if ord(ch) < 128)
        try:
            win.addstr(y, x, ascii_text)
        except curses.error:
            pass

def run_command(cmd):
    try:
        subprocess.run(cmd, shell=False, check=False)
    except Exception as e:
        print(f"Error running {cmd}: {e}")
        input("Press Enter to continue...")


def update_api_keys():
    curses.endwin()
    # Load existing .env or create
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k,v = line.strip().split('=',1)
                    env[k] = v
    else:
        open(ENV_FILE, 'a').close()
    print("\n=== Update API Keys (.env) ===")
    print("Available keys:")
    for k in sorted(env.keys()):
        print(f"  • {k}")
    key = input("Enter the key to update (or new key): ").strip()
    val = input(f"Enter new value for {key}: ").strip()
    env[key] = val
    # Write back
    with open(ENV_FILE, 'w') as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")
    print(f"Updated {key} in .env")
    input("Press Enter to return to menu...")


# Helper to determine how to invoke the Ollama CLI: check for Docker container first, then local binary
def get_ollama_cmd():
    # If a Docker container named 'ollama' is running, use it
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=ollama", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=False
        )
        names = result.stdout.strip().splitlines()
        if "ollama" in names:
            return ["docker", "exec", "ollama", "ollama"]
    except Exception:
        pass
    # Fallback to local Ollama CLI if installed via Homebrew
    if shutil.which("ollama"):
        return ["ollama"]
    # No Ollama CLI found
    print("⚠️  Ollama CLI not found. Please install via Homebrew: brew install ollama")
    sys.exit(1)


# New function to manage pulling and deleting Ollama models
def manage_ollama_models():
    # Safely end curses mode if initialized
    try:
        curses.endwin()
    except curses.error:
        pass
    # Determine how to call Ollama (docker container or local binary)
    base_cmd = get_ollama_cmd()
    while True:
        print("\n=== 🐙 Manage Ollama Models ===")
        print("1. 🔄 Pull a model from Ollama.com")
        print("2. 🤖 Pull a model from HuggingFace.co")
        print("3. 🗑️ Delete an existing Ollama model")
        print("4. ↩️ Return to main menu")
        choice = input("Enter choice [1-4]: ").strip()
        if choice == "1":
            model = input("Enter model name to pull from Ollama.com: ").strip()
            run_command(base_cmd + ["pull", model])
        elif choice == "2":
            model = input("Enter HuggingFace model path (org/model) to pull: ").strip()
            full = f"hf.co/{model}"
            run_command(base_cmd + ["pull", full])
        elif choice == "3":
            try:
                output = subprocess.check_output(base_cmd + ["list"], text=True)
                lines = output.splitlines()[1:]
                models = [line.split()[0] for line in lines]
                if not models:
                    print("No Ollama models found.")
                else:
                    print("\nInstalled Ollama models:")
                    for idx, m in enumerate(models):
                        print(f"  {idx+1}. {m}")
                    sel = input("Enter number of model to delete: ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(models):
                        to_delete = models[int(sel)-1]
                        run_command(base_cmd + ["rm", to_delete])
                    else:
                        print("Invalid selection.")
            except Exception as e:
                print(f"Error listing models: {e}")
        elif choice == "4":
            break
        else:
            print("Invalid selection.")
        input("Press Enter to continue...")


# New curses-based manage function for arrow-key UI when invoked standalone
def manage_ollama_models_curses(stdscr):
    """Curses-based interactive menu for managing Ollama models using arrow keys."""
    curses.curs_set(0)
    # Initialize color support
    curses.start_color()
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    h, w = stdscr.getmaxyx()
    items = [
        "🔄 Pull a model from Ollama.com",
        "🤖 Pull a model from HuggingFace.co",
        "🗑️ Delete an existing Ollama model",
        "↩️ Return to main menu",
    ]
    current = 0
    while True:
        stdscr.clear()
        title = "🐙 Manage Ollama Models"
        stdscr.attron(curses.A_BOLD)
        safe_addstr(stdscr, 1, w // 2 - len(title) // 2, title)
        stdscr.attroff(curses.A_BOLD)
        for idx, item in enumerate(items):
            x, y = 4, idx + 3
            if idx == current:
                stdscr.attron(curses.color_pair(2))
                safe_addstr(stdscr, y, x, item)
                stdscr.attroff(curses.color_pair(2))
            else:
                safe_addstr(stdscr, y, x, item)
        key = stdscr.getch()
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(items) - 1:
            current += 1
        elif key in [curses.KEY_ENTER, ord("\n")]:
            break
    # exit curses mode to perform actions
    curses.endwin()
    base_cmd = get_ollama_cmd()
    if current == 0:
        model = input("Enter model name to pull from Ollama.com: ").strip()
        run_command(base_cmd + ["pull", model])
    elif current == 1:
        model = input("Enter HuggingFace model path (org/model): ").strip()
        full = f"hf.co/{model}"
        run_command(base_cmd + ["pull", full])
    elif current == 2:
        try:
            output = subprocess.check_output(base_cmd + ["list"], text=True)
            lines = output.splitlines()[1:]
            models = [line.split()[0] for line in lines]
            if not models:
                print("No Ollama models found.")
            else:
                print("\nInstalled Ollama models:")
                for idx, m in enumerate(models):
                    print(f"  {idx+1}. {m}")
                sel = input("Enter number of model to delete: ").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(models):
                    to_delete = models[int(sel)-1]
                    run_command(base_cmd + ["rm", to_delete])
                else:
                    print("Invalid selection.")
        except Exception as e:
            print(f"Error listing models: {e}")
    # else Return chosen, nothing to do
    input("Press Enter to exit...")


def restart_ollama():
    """Restart Ollama service based on installation method."""
    try:
        # Check if running in Docker
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=ollama", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=False
        )
        names = result.stdout.strip().splitlines()
        if "ollama" in names:
            # Restart Docker container
            run_command(["docker", "restart", "ollama"])
        else:
            # Restart local Ollama service
            run_command(["brew", "services", "restart", "ollama"])
    except Exception as e:
        print(f"Error restarting Ollama: {e}")
        input("Press Enter to continue...")

def restart_both_services():
    """Restart both Open WebUI and Ollama services."""
    restart_ollama()
    run_command(["docker", "compose", "restart", "open-webui"])
    print("Both services have been restarted.")
    input("Press Enter to continue...")

def main(stdscr):
    curses.curs_set(0)
    # Initialize color support
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    h, w = stdscr.getmaxyx()
    current = 0
    while True:
        stdscr.clear()
        title = "🛡️  Open WebUI Manager"
        stdscr.attron(curses.A_BOLD)
        safe_addstr(stdscr, 1, w//2 - len(title)//2, title)
        stdscr.attroff(curses.A_BOLD)
        for idx, item in enumerate(MENU):
            x = 4
            y = idx + 4
            if idx == current:
                stdscr.attron(curses.color_pair(1))
                safe_addstr(stdscr, y, x, item)
                stdscr.attroff(curses.color_pair(1))
            else:
                safe_addstr(stdscr, y, x, item)
        key = stdscr.getch()
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(MENU) - 1:
            current += 1
        elif key in [curses.KEY_ENTER, ord("\n")]:
            stdscr.clear()
            stdscr.refresh()
            if current == 0:
                run_command(["docker", "compose", "restart", "open-webui"])
            elif current == 1:
                run_command(["docker", "compose", "up", "--build", "-d"])
            elif current == 2:
                run_command([FIX_IP_SCRIPT])
            elif current == 3:
                update_api_keys()
            elif current == 4:
                manage_ollama_models_curses(stdscr)
            elif current == 5:
                restart_ollama()
            elif current == 6:
                restart_both_services()
            elif current == 7:
                sys.exit(0)
        stdscr.refresh()

if __name__ == "__main__":
    # If called with 'ollama', use arrow-key interactive curses menu
    if len(sys.argv) > 1 and sys.argv[1] == "ollama":
        curses.wrapper(manage_ollama_models_curses)
        sys.exit(0)
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 