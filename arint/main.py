#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import os
import time
import random
import signal
import atexit
import threading
import json

for d in ["memory/consciousness/archive", "memory/dreams/backup", "memory/knowledge/raw", "memory/knowledge/clean", "logs"]:
    Path(d).mkdir(parents=True, exist_ok=True)

from core.SilentWatcherSuper import SilentWatcherSuper
from config import load_config

def signal_handler(sig, frame, ai):
    print("\n[ SYS ] Shutting down, saving state...")
    print("")
    ai.save_state()
    sys.exit(0)

def input_loop(ai):
    while True:
        try:
            cmd = input("\n[ CMD ] > ").strip()
            if cmd == "exit":
                ai.save_state()
                print("[ SYS ] Arint stopped.")
                os._exit(0)
            elif cmd.startswith("goal "):
                new = cmd[5:].strip()
                if new:
                    ai.goal_manager.update_primary_description(new, "Creator's Command", from_ai=False)
                    print("[ SYS ] Goal updated.")
                else:
                    print("[ SYS ] Usage: goal <description>")
            elif cmd == "show_goal":
                print(json.dumps(ai.goal_manager.goals, indent=2))
            else:
                print("[ SYS ] Unknown command. Available: exit, goal <text>, show_goal")
        except Exception as e:
            print(f"[ SYS ] Error: {e}")

if __name__ == "__main__":
    config = load_config()
    ai = SilentWatcherSuper(config)

    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, ai))
    atexit.register(lambda: ai.save_state() if 'ai' in locals() else None)

    threading.Thread(target=input_loop, args=(ai,), daemon=True).start()

    try:
        while True:
            ai.run_cycle()
            time.sleep(random.uniform(2, 5))
    except KeyboardInterrupt:
        ai.save_state()
        print("")
        print("\n[ SYS ] Shuttingdown Arint System.")