# Copyright 2025 - 2026 Vu Quang Cuong
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
main.py — Main Entry Point for Wifi-Censor Desktop.
Initializes the configuration manager, SQLite database, Wi-Fi scanner thread,
and launches the CustomTkinter AppWindow.
"""

import sys
from pathlib import Path

# Add root folder to sys.path so we can import 'desktop.app' as package module
if getattr(sys, "frozen", False):
    root_dir = Path(sys._MEIPASS)
else:
    root_dir = Path(__file__).resolve().parent.parent

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import customtkinter as ctk
from desktop.app.logger import get_logger
from desktop.app.config import get_config_manager
from desktop.app.database import Database
from desktop.app.scanner import WifiScanner
from desktop.ui.app_window import AppWindow

logger = get_logger("main")


def start_ollama_if_needed():
    import os
    import subprocess
    import urllib.request
    
    # 1. Check if Ollama is already active
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.5) as resp:
            if resp.status == 200:
                logger.info("Ollama is already active and running.")
                return
    except Exception:
        pass

    # 2. If not running, locate and start ollama.exe
    ollama_path = os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe")
    if os.path.exists(ollama_path):
        logger.info(f"Starting Ollama background service from: {ollama_path}")
        try:
            # CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen([ollama_path, "serve"], creationflags=0x08000000)
            # Short sleep to allow service startup
            import time
            time.sleep(2)
        except Exception as e:
            logger.error(f"Failed to start Ollama: {e}")
    else:
        logger.warning("Ollama is not installed in standard user path.")


def main():
    # Force UTF-8 encoding for standard output to support emojis/diacritics in Windows console
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("==============================================")
    print("      [AP] WIFI-CENSOR DESKTOP GUARD v1.0.0")
    print("       Copyright (C) 2025-2026 Vu Quang Cuong")
    print("==============================================")

    # 0. Auto-start Ollama if needed
    start_ollama_if_needed()

    # 1. Config Manager
    logger.info("Loading configuration...")
    cfg_manager = get_config_manager()
    cfg = cfg_manager.config

    # 2. SQLite Database
    db_path = cfg_manager.get_db_path()
    logger.info(f"Initializing SQLite Database at: {db_path}")
    db = Database(db_path)
    # Purge historical entries older than 30 days
    db.purge_old_data()

    # 3. Wi-Fi Scanner thread
    logger.info(f"Initializing Wi-Fi Scanner (Interval: {cfg.scan_interval_sec}s)...")
    scanner = WifiScanner(interval_sec=cfg.scan_interval_sec)
    logger.info(f"Scanner Mode Detected: {scanner.mode.value.upper()}")
    if scanner.is_demo:
        logger.info("Note: Running in DEMO mode (realistic synthetic data fallback)")
    
    logger.info("Starting background scanning thread...")
    scanner.start()

    # 4. App Window UI
    logger.info("Launching CustomTkinter Graphical User Interface...")
    app = AppWindow(db, scanner)
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("Interrupted by keyboard...")
    finally:
        logger.info("Shutting down background scan threads...")
        scanner.stop()
        logger.info("Closing database connections...")
        db.close()
        logger.info("Exited cleanly.")


if __name__ == "__main__":
    main()
