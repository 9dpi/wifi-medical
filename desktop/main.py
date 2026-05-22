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
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import customtkinter as ctk
from desktop.app.config import get_config_manager
from desktop.app.database import Database
from desktop.app.scanner import WifiScanner
from desktop.ui.app_window import AppWindow


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

    # 1. Config Manager
    print("[Core] Loading configuration...")
    cfg_manager = get_config_manager()
    cfg = cfg_manager.config

    # 2. SQLite Database
    db_path = cfg_manager.get_db_path()
    print(f"[Core] Initializing SQLite Database at: {db_path}")
    db = Database(db_path)
    # Purge historical entries older than 30 days
    db.purge_old_data()

    # 3. Wi-Fi Scanner thread
    print(f"[Core] Initializing Wi-Fi Scanner (Interval: {cfg.scan_interval_sec}s)...")
    scanner = WifiScanner(interval_sec=cfg.scan_interval_sec)
    print(f"[Core] Scanner Mode Detected: {scanner.mode.value.upper()}")
    if scanner.is_demo:
        print("[Core] Note: Running in DEMO mode (realistic synthetic data fallback)")
    
    print("[Core] Starting background scanning thread...")
    scanner.start()

    # 4. App Window UI
    print("[UI] Launching CustomTkinter Graphical User Interface...")
    app = AppWindow(db, scanner)
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("[Core] Interrupted by keyboard...")
    finally:
        print("[Core] Shutting down background scan threads...")
        scanner.stop()
        print("[Core] Closing database connections...")
        db.close()
        print("[Core] Exited cleanly.")


if __name__ == "__main__":
    main()
