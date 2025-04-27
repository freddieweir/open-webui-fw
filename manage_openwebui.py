#!/usr/bin/env python3
"""
🚀 Open WebUI Manager
Interactive CLI to manage Open WebUI: restart, rebuild, run fix IP script, and update API keys.
"""

import curses
import subprocess
import os
import sys

ENV_FILE = os.path.join(os.getcwd(), ".env")
FIX_IP_SCRIPT = os.path.join(os.getcwd(), "fix_ip_address.sh")

MENU = [
    "🔄 Restart Open WebUI",
    "🛠️  Rebuild & Deploy Open WebUI",
    "🌐 Fix IP Address",
    "🔑 Update API Keys (.env)",
    "🐙 Manage Ollama Models",
    "🚪 Exit",
]


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


# New function to manage pulling and deleting Ollama models
def manage_ollama_models():
    curses.endwin()
    while True:
        print("\n=== 🐙 Manage Ollama Models ===")
        print("1. 🔄 Pull a model from Ollama.com")
        print("2. 🤖 Pull a model from HuggingFace.co")
        print("3. 🗑️ Delete an existing Ollama model")
        print("4. ↩️ Return to main menu")
        choice = input("Enter choice [1-4]: ").strip()
        if choice == "1":
            model = input("Enter model name to pull from Ollama.com: ").strip()
            run_command(["docker", "exec", "ollama", "ollama", "pull", model])
        elif choice == "2":
            model = input("Enter HuggingFace model path (org/model) to pull: ").strip()
            full = f"hf.co/{model}"
            run_command(["docker", "exec", "ollama", "ollama", "pull", full])
        elif choice == "3":
            try:
                output = subprocess.check_output(["docker", "exec", "ollama", "ollama", "list"], text=True)
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
                        run_command(["docker", "exec", "ollama", "ollama", "rm", to_delete])
                    else:
                        print("Invalid selection.")
            except Exception as e:
                print(f"Error listing models: {e}")
        elif choice == "4":
            break
        else:
            print("Invalid selection.")
        input("Press Enter to continue...")


def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    h, w = stdscr.getmaxyx()
    current = 0
    while True:
        stdscr.clear()
        title = "🛡️  Open WebUI Manager"
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(1, w//2 - len(title)//2, title)
        stdscr.attroff(curses.A_BOLD)
        for idx, item in enumerate(MENU):
            x = 4
            y = idx + 4
            if idx == current:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, item)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, item)
        key = stdscr.getch()
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(MENU) - 1:
            current += 1
        elif key in [curses.KEY_ENTER, ord("\n")]:
            stdscr.clear()
            stdscr.refresh()
            if current == 0:
                run_command(["docker", "compose", "restart", "open-webui"] )
            elif current == 1:
                run_command(["docker", "compose", "up", "--build", "-d"] )
            elif current == 2:
                run_command([FIX_IP_SCRIPT])
            elif current == 3:
                update_api_keys()
            elif current == 4:
                manage_ollama_models()
            elif current == 5:
                break
        stdscr.refresh()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 