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
dashboard_tab.py — Real-time Dashboard Screen.
Houses the StatusCard, RSSI chart, signal stats, and live alert lists.
"""

import time
import customtkinter as ctk
from desktop.ui.components.status_card import StatusCard
from desktop.ui.components.rssi_chart import RssiChart
from desktop.app.presence_engine import PresenceResult, PresenceState, ActivityState
from desktop.app.database import AlertEvent, Database
from desktop.app.config import get_config


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db: Database, **kwargs):
        super().__init__(parent, fg_color="#050810", **kwargs)

        self.db = db

        # Configure Grid Layout
        self.grid_columnconfigure(0, weight=1, minsize=350)  # Left column (Stats, Status)
        self.grid_columnconfigure(1, weight=2, minsize=500)  # Right column (Charts, Alerts list)
        self.grid_rowconfigure(0, weight=1)

        # ── Left Column: Status & Stats ───────────────────────────────────────
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # Status Card
        self.status_card = StatusCard(self.left_frame)
        self.status_card.pack(fill="x", pady=(0, 15))

        # Stats Info Card
        self.stats_card = ctk.CTkFrame(self.left_frame, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12)
        self.stats_card.pack(fill="both", expand=True)

        self.stats_title = ctk.CTkLabel(
            self.stats_card, text="THÔNG SỐ GIÁM SÁT SÓNG", text_color="#f8fafc",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold")
        )
        self.stats_title.pack(anchor="w", padx=15, pady=(15, 10))

        # We will create standard key-value display fields
        self.metrics = {}
        metric_labels = [
            ("Mạng phát mục tiêu (AP):", "target_ap", "Chưa chọn thiết bị"),
            ("Cường độ sóng (RSSI):", "rssi_strength", "-- dBm"),
            ("Độ biến động tín hiệu:", "signal_var", "0.00"),
            ("Độ nhạy phân tích:", "sensitivity", "1.00x"),
            ("Trạng thái hiệu chỉnh:", "calib_status", "Đã hiệu chỉnh")
        ]

        for display_name, key, default_val in metric_labels:
            row = ctk.CTkFrame(self.stats_card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=8)
            
            lbl_name = ctk.CTkLabel(row, text=display_name, text_color="#cbd5e1", font=ctk.CTkFont(family="Inter", size=14, weight="bold"))
            lbl_name.pack(side="left")
            
            lbl_val = ctk.CTkLabel(row, text=default_val, text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=15, weight="bold"))
            lbl_val.pack(side="right")
            
            self.metrics[key] = lbl_val

        # ── Right Column: Charts & Alert Log ──────────────────────────────────
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        
        self.right_frame.grid_rowconfigure(0, weight=3) # Chart
        self.right_frame.grid_rowconfigure(1, weight=2) # Alerts List
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Real-time Matplotlib Chart
        self.chart = RssiChart(self.right_frame)
        self.chart.grid(row=0, column=0, sticky="nsew", pady=(0, 15))

        # Alert panel frame
        self.alert_panel = ctk.CTkFrame(self.right_frame, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12)
        self.alert_panel.grid(row=1, column=0, sticky="nsew")

        # Alert panel title
        self.alert_title = ctk.CTkLabel(
            self.alert_panel, text="🔔 CẢNH BÁO & SỰ CỐ GẦN ĐÂY", text_color="#f8fafc",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold")
        )
        self.alert_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Scrollable list for alerts
        self.alerts_scroll = ctk.CTkScrollableFrame(
            self.alert_panel, fg_color="transparent", height=120
        )
        self.alerts_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.refresh_alerts_list()

    def update_realtime_data(self, result: PresenceResult, is_alert: bool = False, alert_type: str = ""):
        """Called every time scanner streams new RSSI values."""
        cfg = get_config()

        # Update Status Card
        self.status_card.set_state(result.presence, result.activity, result.confidence, is_alert, alert_type)

        # Update Metrics panel
        target_ssid = cfg.target_ssid or "Thiết bị mạnh nhất"
        target_desc = f"{target_ssid}"
        if cfg.target_bssid:
            target_desc += f" ({cfg.target_bssid[:8]}..)"
        
        self.metrics["target_ap"].configure(text=target_desc)
        self.metrics["rssi_strength"].configure(text=f"{int(result.rssi_mean)} dBm")
        self.metrics["signal_var"].configure(text=f"{result.rssi_variance:.3f}")
        self.metrics["sensitivity"].configure(text=f"{cfg.sensitivity:.2f}x")

        # Calibration status
        if not cfg.is_calibrated:
            self.metrics["calib_status"].configure(text="Đang phân tích nền...", text_color="#06b6d4")
        else:
            self.metrics["calib_status"].configure(text="Hoàn thành (Đã khóa)", text_color="#10b981")

        # Fetch recent snapshots from DB to draw chart
        snapshots = self.db.get_rssi_last_n(n=100)
        if snapshots:
            ts = [s.timestamp for s in snapshots]
            rssis = [s.rssi for s in snapshots]
            vars_ = [s.variance for s in snapshots]
            self.chart.update_chart(ts, rssis, vars_)

    def refresh_alerts_list(self):
        """Re-fetches and displays current active/past alerts in the list."""
        # Clear current scroll frame children
        for child in self.alerts_scroll.winfo_children():
            child.destroy()

        alerts = self.db.get_recent_alerts(limit=10)
        
        if not alerts:
            no_alert_lbl = ctk.CTkLabel(
                self.alerts_scroll, text="🟢 Phòng hoạt động an toàn, không có cảnh báo nào.",
                text_color="#10b981", font=ctk.CTkFont(family="Inter", size=16, weight="bold")
            )
            no_alert_lbl.pack(pady=35)
            return

        for a in alerts:
            time_str = time.strftime("%H:%M:%S", time.localtime(a.timestamp))
            is_danger = a.alert_type == "FALL"
            
            item_frame = ctk.CTkFrame(
                self.alerts_scroll, fg_color="#271c1c" if is_danger else "#2a2214", 
                border_color="#ef4444" if is_danger else "#f59e0b", 
                border_width=1.5, corner_radius=8
            )
            item_frame.pack(fill="x", pady=6, padx=5)

            icon = "🔴" if is_danger else "⚠️"
            title = f"{icon} CẢNH BÁO: PHÁT HIỆN TÉ NGÃ" if is_danger else f"{icon} CẢNH BÁO: BẤT ĐỘNG QUÁ LÂU"
            
            lbl_title = ctk.CTkLabel(
                item_frame, text=title, text_color="#fca5a5" if is_danger else "#fde047",
                font=ctk.CTkFont(family="Inter", size=16, weight="bold")
            )
            lbl_title.pack(anchor="w", padx=15, pady=(10, 4))

            lbl_desc = ctk.CTkLabel(
                item_frame, text=f"{time_str} · {a.message}", text_color="#fecaca" if is_danger else "#fef3c7",
                font=ctk.CTkFont(family="Inter", size=14, weight="bold"), justify="left", anchor="w"
            )
            lbl_desc.pack(anchor="w", padx=15, pady=(2, 10))
