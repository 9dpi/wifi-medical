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
app_window.py — Main Window of Wifi-Censor Desktop.
Coordinates the sidebar navigation, AlertBanner, and embeds the Dashboard, History, and Settings tabs.
Sets up the polling loop which processes the live Wi-Fi RSSI queue.
"""

import time
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from typing import List, Optional
from desktop.app.logger import get_logger

logger = get_logger("ui.app_window")

# Core imports
from desktop.app.config import get_config, get_config_manager
from desktop.app.database import Database
from desktop.app.scanner import WifiScanner, WifiNetwork
from desktop.app.presence_engine import PresenceEngine, PresenceState, ActivityState
from desktop.app.anomaly_tracker import AnomalyTracker
from desktop.app.exporter import JsonExporter

# AI Agent imports (MVP 2)
try:
    from desktop.app.ai.ollama_manager import OllamaManager
    from desktop.app.ai.tools import ToolExecutor
    from desktop.app.ai.agent import WifiCensorAgent
    from desktop.app.ai.fall_verifier import FallVerifier
    from desktop.app.ai.report_generator import ReportGenerator
    AI_AVAILABLE = True
except ImportError as _e:
    logger.warning(f"AI modules not available: {_e}")
    AI_AVAILABLE = False

# UI imports
from desktop.ui.components.alert_banner import AlertBanner
from desktop.ui.dashboard_tab import DashboardTab
from desktop.ui.history_tab import HistoryTab
from desktop.ui.settings_tab import SettingsTab
from desktop.ui.guide_tab import GuideTab
from desktop.ui.ai_chat_tab import AIChatTab

# Fail-safe system tray support
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image
    TRAY_SUPPORTED = True
except ImportError:
    TRAY_SUPPORTED = False


class AppWindow(ctk.CTk):
    def __init__(self, db: Database, scanner: WifiScanner):
        super().__init__()

        self.db = db
        self.scanner = scanner
        self.engine = PresenceEngine()
        self.tracker = AnomalyTracker()
        self.exporter = JsonExporter(db)

        # Alert state variables
        self.has_active_alert = False
        self.active_alert_type = ""
        self.active_alert_id = None

        # Configuration load
        cfg = get_config()
        self.title("Wifi-Censor - Hệ Thống Trực Giám Sát Y Tế & Cảnh Báo Cấp Cứu Không Tiếp Xúc")
        self.geometry(f"{cfg.window_width}x{cfg.window_height}")
        self.minsize(1100, 750)

        # Set theme colors globally
        ctk.set_appearance_mode("dark")

        # Grid Layout: Sidebar left, Main Panel right
        self.grid_columnconfigure(0, weight=0, minsize=260)  # Expanded sidebar width for clarity
        self.grid_columnconfigure(1, weight=1)              # Main Content
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar Navigation (Windows 98 Style) ──────────────────────────────
        self.sidebar = ctk.CTkFrame(self, fg_color="#d4d0c8", border_color="#808080", border_width=2, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Logo and Title
        self.logo_lbl = ctk.CTkLabel(
            self.sidebar, text="📡 Trực Y Tế Wifi-Censor", text_color="#000080",
            font=ctk.CTkFont(family="Tahoma", size=18, weight="bold")
        )
        self.logo_lbl.pack(padx=20, pady=(25, 2))
        
        self.sublogo_lbl = ctk.CTkLabel(
            self.sidebar, text="Hệ Thống Cảnh Báo Cấp Cứu", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=11, weight="bold")
        )
        self.sublogo_lbl.pack(padx=20, pady=(0, 20))

        # Nav Buttons (Windows 98 Bevel style - Pure Medical Terms)
        self.btn_nav_dash = self._create_nav_btn("📊 Bảng Trực Giám Sát", self.show_dashboard)
        self.btn_nav_dash.pack(fill="x", padx=10, pady=4)

        self.btn_nav_hist = self._create_nav_btn("📜 Nhật Ký Y Tế & Học Máy", self.show_history)
        self.btn_nav_hist.pack(fill="x", padx=10, pady=4)

        self.btn_nav_sett = self._create_nav_btn("⚙️ Cấu Hình Chỉ Số Y Tế", self.show_settings)
        self.btn_nav_sett.pack(fill="x", padx=10, pady=4)

        self.btn_nav_guid = self._create_nav_btn("📖 Hướng Dẫn Trực Y Tế", self.show_guide)
        self.btn_nav_guid.pack(fill="x", padx=10, pady=4)

        self.btn_nav_ai = self._create_nav_btn("🤖 Trợ Lý Y Tế AI", self.show_ai_chat)
        self.btn_nav_ai.pack(fill="x", padx=10, pady=4)

        # Bottom Connection Status Card
        self.conn_card = ctk.CTkFrame(self.sidebar, fg_color="#d4d0c8", border_color="#808080", border_width=2, corner_radius=0)
        self.conn_card.pack(side="bottom", fill="x", padx=10, pady=20)
        
        from desktop.ui.dashboard_tab import get_active_wifi_ssid
        active_ssid = get_active_wifi_ssid()
        if active_ssid:
            mode_text = f"Wi-Fi: {active_ssid}"
        else:
            mode_text = "Chế độ: Mô phỏng" if self.scanner.is_demo else f"Quét: {self.scanner.mode.value.upper()}"
            
        self.conn_lbl = ctk.CTkLabel(
            self.conn_card, text=mode_text,
            text_color="#000080" if active_ssid or not self.scanner.is_demo else "#800080",
            font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")
        )
        self.conn_lbl.pack(pady=10)

        # ── Main Content Area (Teal Green Classic Windows 98) ──────────────────
        self.main_content = ctk.CTkFrame(self, fg_color="#008080", corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew")

        # Top Alert Banner
        self.alert_banner = AlertBanner(self.main_content, on_acknowledge=self.acknowledge_active_alert)
        self.alert_banner.pack(fill="x", padx=10, pady=(10, 5))

        # Tab Frames container
        self.tab_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.tab_container.pack(fill="both", expand=True)

        # Initialize screen classes
        self.dashboard_tab = DashboardTab(self.tab_container, self.db)
        self.history_tab = HistoryTab(self.tab_container, self.db)
        self.settings_tab = SettingsTab(
            self.tab_container,
            on_recalibrate=self.engine.recalibrate,
            on_scan_once=self._scan_once_helper
        )
        self.guide_tab = GuideTab(self.tab_container)
        self.ai_chat_tab = AIChatTab(self.tab_container)

        # Start with dashboard
        self.active_tab = None
        self.show_dashboard()

        # Wire protocol for close
        self.protocol("WM_DELETE_WINDOW", self.on_close_request)

        # Start engines
        self.tracker.start()
        self.exporter.sync_manager.start(self.handle_remote_command)

        # Initialize AI Agent in background (non-blocking)
        self._ai_agent: Optional["WifiCensorAgent"] = None
        self._fall_verifier: Optional["FallVerifier"] = None
        self._report_gen: Optional["ReportGenerator"] = None
        self._ollama: Optional["OllamaManager"] = None
        if AI_AVAILABLE and get_config().ai_enabled:
            import threading
            threading.Thread(target=self._init_ai_agent, daemon=True).start()

        self.poll_scanner()

    def _create_nav_btn(self, text: str, command) -> ctk.CTkButton:
        return ctk.CTkButton(
            self.sidebar, text=text, fg_color="#d4d0c8", text_color="#000000",
            hover_color="#e6e6e6", anchor="w", height=38, corner_radius=0,
            border_width=2, border_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=12, weight="bold"), command=command
        )

    def _init_ai_agent(self):
        """Initialize AI Agent components in background thread."""
        try:
            cfg = get_config()
            logger.info("Khởi động AI Agent...")
            ollama = OllamaManager(base_url=cfg.ollama_url)

            if not ollama.health_check():
                logger.warning("Ollama không phản hồi — AI tắt.")
                return

            # Select best available model
            model = ollama.select_best_model()
            if not model:
                logger.warning("Không tìm thấy model nào.")
                return

            # Initialize tool executor and agent
            tool_exec = ToolExecutor(self.db, self.exporter, get_config_manager())
            agent = WifiCensorAgent(ollama, tool_exec)

            # Initialize fall verifier
            fall_verifier = FallVerifier()
            fall_verifier.set_agent(agent)
            fall_verifier.set_alert_callback(self.trigger_alert)

            # Initialize report generator
            report_gen = ReportGenerator(self.db, self.exporter.bio_estimator)
            report_gen.set_agent(agent)
            report_gen.start_scheduler(hour=cfg.ai_report_hour)

            # Wire fall verifier to anomaly tracker
            self.tracker.set_fall_verifier(fall_verifier)

            # Store references
            self._ollama = ollama
            self._ai_agent = agent
            self._fall_verifier = fall_verifier
            self._report_gen = report_gen

            # Wire to AI chat tab (must run on main thread)
            self.after(0, lambda: self._connect_ai_to_ui())

            # Warm up model in background
            ollama.warm_up()
            logger.info(f"AI Agent sẵn sàng với model: {model}")

        except Exception as e:
            logger.error(f"Lỗi khởi động AI Agent: {e}")

    def _connect_ai_to_ui(self):
        """Wire AI components to AIChatTab (must be called from main thread)."""
        if self._ai_agent:
            self.ai_chat_tab.set_agent(self._ai_agent)
        if self._report_gen:
            self.ai_chat_tab.set_report_generator(self._report_gen)
        if self._ollama:
            self.ai_chat_tab.set_ollama(self._ollama)

    def select_nav_button(self, active_btn: ctk.CTkButton):
        for btn in [self.btn_nav_dash, self.btn_nav_hist, self.btn_nav_sett,
                    self.btn_nav_guid, self.btn_nav_ai]:
            if btn == active_btn:
                btn.configure(fg_color="#000080", text_color="#ffffff", border_color="#808080", border_width=1)
            else:
                btn.configure(fg_color="#d4d0c8", text_color="#000000", border_color="#ffffff", border_width=2)

    def show_dashboard(self):
        self.select_nav_button(self.btn_nav_dash)
        if self.active_tab:
            self.active_tab.pack_forget()
        self.dashboard_tab.pack(fill="both", expand=True)
        self.active_tab = self.dashboard_tab
        self.dashboard_tab.refresh_alerts_list()

    def show_history(self):
        self.select_nav_button(self.btn_nav_hist)
        if self.active_tab:
            self.active_tab.pack_forget()
        self.history_tab.pack(fill="both", expand=True)
        self.active_tab = self.history_tab
        self.history_tab.refresh_data()

    def show_settings(self):
        self.select_nav_button(self.btn_nav_sett)
        if self.active_tab:
            self.active_tab.pack_forget()
        self.settings_tab.pack(fill="both", expand=True)
        self.active_tab = self.settings_tab

    def show_guide(self):
        self.select_nav_button(self.btn_nav_guid)
        if self.active_tab:
            self.active_tab.pack_forget()
        self.guide_tab.pack(fill="both", expand=True)
        self.active_tab = self.guide_tab

    def show_ai_chat(self):
        self.select_nav_button(self.btn_nav_ai)
        if self.active_tab:
            self.active_tab.pack_forget()
        self.ai_chat_tab.pack(fill="both", expand=True)
        self.active_tab = self.ai_chat_tab

    def _scan_once_helper(self) -> List[WifiNetwork]:
        # Return networks by fetching immediately or reading queue
        latest = self.scanner.get_latest(timeout=1.0)
        return latest or []

    def poll_scanner(self):
        """Main real-time background scanner polling loop."""
        networks = self.scanner.get_latest()
        if networks:
            # Process RSSI values
            result = self.engine.process(networks)

            # Insert raw scan snap in DB
            self.db.insert_rssi(
                ts=time.time(),
                bssid=result.dominant_bssid,
                ssid=next((n.ssid for n in networks if n.bssid == result.dominant_bssid), ""),
                rssi=int(result.rssi_mean),
                variance=result.rssi_variance,
                label=result.presence.value
            )

            # Run anomaly tracking checks (with bio_bpm for AI context)
            bio_result = self.exporter.bio_estimator.last_result
            bio_bpm = bio_result.heart_rate_bpm if bio_result else None
            self.tracker.on_result(result, self.trigger_alert, bio_bpm=bio_bpm)

            # Feed RSSI to fall verifier buffer
            if self._fall_verifier is not None:
                self._fall_verifier.push_rssi(
                    rssi=result.rssi_mean,
                    variance=result.rssi_variance,
                    activity=result.activity.value
                )

            # Export JSON snapshot for web integration
            self.exporter.export_snapshot(result)

            # Update currently visible UI elements
            self.dashboard_tab.update_realtime_data(
                result,
                is_alert=self.has_active_alert,
                alert_type=self.active_alert_type,
                bio_result=self.exporter.bio_estimator.last_result
            )

        # Update sidebar active connected Wi-Fi dynamically (outside of networks check to ensure it always runs)
        from desktop.ui.dashboard_tab import get_active_wifi_ssid
        active_ssid = get_active_wifi_ssid()
        if active_ssid:
            self.conn_lbl.configure(text=f"Wi-Fi: {active_ssid}", text_color="#000080")
        else:
            mode_text = "Chế độ: Mô phỏng" if self.scanner.is_demo else f"Quét: {self.scanner.mode.value.upper()}"
            self.conn_lbl.configure(text=mode_text, text_color="#800080" if self.scanner.is_demo else "#000080")

        # Reschedule next check in 100ms
        self.after(100, self.poll_scanner)

    def trigger_alert(self, alert_type: str, title: str, message: str):
        """Invoked when anomaly tracker detects danger/warn event."""
        # Check if already active to prevent duplicates
        if self.has_active_alert and self.active_alert_type == alert_type:
            return

        now = time.time()
        # Save alert event to database
        alert_id = self.db.insert_alert(now, alert_type, message)

        self.has_active_alert = True
        self.active_alert_type = alert_type
        self.active_alert_id = alert_id

        # Update UI Banner
        self.alert_banner.show_alert(alert_id, alert_type, title, message)

        # Notify AI Chat tab for auto-commentary
        if self._ai_agent is not None:
            self.after(500, lambda: self.ai_chat_tab.on_system_alert(alert_type, title, message))

        # Trigger desktop popups / flashes
        self._trigger_os_popup(title, message)

    def _trigger_os_popup(self, title: str, message: str):
        """Displays a beautiful standalone top-most dialog in case app is minimized."""
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("480x240")
        popup.attributes("-topmost", True)
        popup.configure(fg_color="#0d1117")

        # Position popup center of screen
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = (screen_width / 2) - 240
        y = (screen_height / 2) - 120
        popup.geometry(f"+{int(x)}+{int(y)}")

        lbl_icon = ctk.CTkLabel(popup, text="🆘 CẢNH BÁO NGUY HIỂM", text_color="#ef4444", font=ctk.CTkFont(family="Inter", size=18, weight="bold"))
        lbl_icon.pack(pady=(25, 10))

        lbl_msg = ctk.CTkLabel(popup, text=message, text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=14, weight="bold"), wraplength=420)
        lbl_msg.pack(pady=(0, 25))

        btn_ok = ctk.CTkButton(
            popup, text="Xác nhận An toàn (Tắt còi)", fg_color="#ef4444", hover_color="#dc2626",
            text_color="#ffffff", font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            width=240, height=42, command=lambda: [self.acknowledge_active_alert(), popup.destroy()]
        )
        btn_ok.pack()

    def acknowledge_active_alert(self):
        """Acknowledge active alert through the banner close button."""
        if self.active_alert_id is not None:
            self.db.acknowledge_alert(self.active_alert_id)

        self.has_active_alert = False
        self.active_alert_type = ""
        self.active_alert_id = None

        # Re-fetch alerts
        self.dashboard_tab.refresh_alerts_list()
        if self.active_tab == self.history_tab:
            self.history_tab.refresh_data()

    def on_close_request(self):
        """Minimize to tray instead of hard closing if tray is supported, else close."""
        self.withdraw()  # Hide UI window

        if TRAY_SUPPORTED:
            icon_img = Image.new('RGB', (64, 64), color=(99, 102, 241))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(icon_img)
            draw.ellipse((16, 16, 48, 48), fill=(240, 244, 255))
            menu = (item('Hiện Wifi-Censor', self._tray_show_window),
                    item('Thoát', self._tray_exit_app))
            self.tray = pystray.Icon("WifiCensor", icon_img, "Wifi-Censor Guard", menu)
            self.tray.run_detached()
        else:
            self._cleanup_and_exit()

    def _cleanup_and_exit(self):
        """Stop all background services and exit."""
        self.scanner.stop()
        self.exporter.sync_manager.stop()
        if self._report_gen:
            self._report_gen.stop_scheduler()
        self.destroy()

    def _tray_show_window(self):
        if hasattr(self, "tray") and self.tray:
            self.tray.stop()
        self.deiconify()

    def _tray_exit_app(self):
        if hasattr(self, "tray") and self.tray:
            self.tray.stop()
        self.scanner.stop()
        self.exporter.sync_manager.stop()
        self.destroy()

    def handle_remote_command(self, action, value):
        """Processes remote control commands fetched from GitHub in a thread-safe way."""
        def execute_cmd():
            if action == "acknowledge_alert":
                if self.has_active_alert:
                    self.acknowledge_active_alert()
                    logger.info("Tắt còi báo động từ xa thành công.")
            elif action == "calibrate":
                self.engine.recalibrate()
                logger.info("Kích hoạt hiệu chỉnh sóng nền từ xa.")
            elif action == "set_sensitivity":
                try:
                    sensitivity = float(value)
                    get_config_manager().update(sensitivity=round(sensitivity, 2))
                    self.settings_tab._load_settings_values()
                    logger.info(f"Đặt độ nhạy từ xa thành {sensitivity}.")
                except Exception as e:
                    logger.error(f"Lỗi định dạng độ nhạy: {e}")
        
        # Queue execution on Tkinter's main thread
        self.after(0, execute_cmd)
