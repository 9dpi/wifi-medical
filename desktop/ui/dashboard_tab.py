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
dashboard_tab.py — Real-time Dashboard Screen (Windows 98 Style).
Houses classic outset bevel Groupboxes, classic Tahoma fonts, and retro charts.
"""

import subprocess
import time
import customtkinter as ctk
from desktop.ui.components.status_card import StatusCard
from desktop.ui.components.rssi_chart import RssiChart
from desktop.app.presence_engine import PresenceResult, PresenceState, ActivityState
from desktop.app.database import AlertEvent, Database
from desktop.app.config import get_config

_cached_ssid = None
_last_ssid_check = 0.0

def get_active_wifi_ssid() -> str:
    global _cached_ssid, _last_ssid_check
    now = time.time()
    if _cached_ssid is not None and now - _last_ssid_check < 6.0:
        return _cached_ssid
    
    _last_ssid_check = now
    try:
        # Run netsh to get connected SSID on Windows
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=1.5, encoding="utf-8", errors="replace",
            creationflags=0x08000000
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("SSID"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    ssid = parts[1].strip()
                    if ssid:
                        _cached_ssid = ssid
                        return _cached_ssid
    except Exception:
        pass
    
    _cached_ssid = ""
    return _cached_ssid


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db: Database, **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)

        self.db = db

        # Configure Grid Layout
        self.grid_columnconfigure(0, weight=1, minsize=350)  # Left column (Stats, Status)
        self.grid_columnconfigure(1, weight=2, minsize=500)  # Right column (Charts, Alerts list)
        self.grid_rowconfigure(0, weight=1)

        # ── Left Column: Status & Stats ───────────────────────────────────────
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        # Status Card (Classic customized)
        self.status_card = StatusCard(self.left_frame)
        self.status_card.pack(fill="x", pady=(0, 10))

        # Stats Info Card (Windows 98 Bevel style)
        self.stats_card = ctk.CTkFrame(
            self.left_frame, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.stats_card.pack(fill="x", pady=(0, 10))

        # Header Title (Gray / Bevel)
        title_bar_stats = ctk.CTkFrame(self.stats_card, fg_color="#000080", height=24, corner_radius=0)
        title_bar_stats.pack(fill="x", padx=2, pady=2)
        
        self.stats_title = ctk.CTkLabel(
            title_bar_stats, text="📡 THÔNG SỐ GIÁM SÁT SÓNG", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.stats_title.pack(anchor="w", padx=6, pady=2)

        # We will create standard key-value display fields
        self.metrics = {}
        metric_labels = [
            ("Mạng Wi-Fi kết nối:", "target_ap", "Chưa kết nối"),
            ("Cường độ sóng (RSSI):", "rssi_strength", "-- dBm"),
            ("Độ biến động tín hiệu:", "signal_var", "0.00"),
            ("Độ nhạy phân tích:", "sensitivity", "1.00x"),
            ("Trạng thái hiệu chỉnh:", "calib_status", "Đã hiệu chỉnh")
        ]

        for display_name, key, default_val in metric_labels:
            row = ctk.CTkFrame(self.stats_card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=5)
            
            lbl_name = ctk.CTkLabel(row, text=display_name, text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=13))
            lbl_name.pack(side="left")
            
            lbl_val = ctk.CTkLabel(row, text=default_val, text_color="#000080", font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"))
            lbl_val.pack(side="right")
            
            self.metrics[key] = lbl_val

        # Bio Signals Info Card (Windows 98 Bevel Style)
        self.bio_card = ctk.CTkFrame(
            self.left_frame, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.bio_card.pack(fill="both", expand=True)

        title_bar_bio = ctk.CTkFrame(self.bio_card, fg_color="#000080", height=24, corner_radius=0)
        title_bar_bio.pack(fill="x", padx=2, pady=2)

        self.bio_title = ctk.CTkLabel(
            title_bar_bio, text="🔬 GIÁM SÁT SINH HIỆU LÂM SÀNG", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.bio_title.pack(anchor="w", padx=6, pady=2)

        # People Count Header
        row_people = ctk.CTkFrame(self.bio_card, fg_color="transparent")
        row_people.pack(fill="x", padx=10, pady=5)
        
        lbl_people_name = ctk.CTkLabel(row_people, text="👥 Số người trong phòng:", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"))
        lbl_people_name.pack(side="left")
        
        self.lbl_people_val = ctk.CTkLabel(row_people, text="-- người", text_color="#000080", font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"))
        self.lbl_people_val.pack(side="right")

        # Sunken Bevel Box for Individual Vitals
        self.vitals_border = ctk.CTkFrame(
            self.bio_card, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        self.vitals_border.pack(fill="both", expand=True, padx=10, pady=(2, 5))

        self.vitals_scroll = ctk.CTkScrollableFrame(
            self.vitals_border, fg_color="transparent", corner_radius=0
        )
        self.vitals_scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # Footnote for bio estimates clarity
        self.bio_footnote = ctk.CTkLabel(
            self.bio_card, text="* Chỉ số nhịp tim/nhiệt độ được suy luận gián tiếp qua sóng Wi-Fi.\nTự động đo chính xác bằng cảm biến MAX30102 / MLX90614 khi kết nối.",
            text_color="#555555", font=ctk.CTkFont(family="Tahoma", size=10, slant="italic"),
            justify="left", anchor="w"
        )
        self.bio_footnote.pack(anchor="w", padx=10, pady=(5, 5))

        # ── Right Column: Charts & Alert Log ──────────────────────────────────
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        
        self.right_frame.grid_rowconfigure(0, weight=3) # Chart
        self.right_frame.grid_rowconfigure(1, weight=2) # Alerts List
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Real-time Matplotlib Chart
        self.chart = RssiChart(self.right_frame)
        self.chart.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # Alert panel frame
        self.alert_panel = ctk.CTkFrame(
            self.right_frame, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.alert_panel.grid(row=1, column=0, sticky="nsew")

        title_bar_alerts = ctk.CTkFrame(self.alert_panel, fg_color="#000080", height=24, corner_radius=0)
        title_bar_alerts.pack(fill="x", padx=2, pady=2)

        # Alert panel title
        self.alert_title = ctk.CTkLabel(
            title_bar_alerts, text="🔔 CẢNH BÁO & SỰ CỐ GẦN ĐÂY", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.alert_title.pack(anchor="w", padx=6, pady=2)

        # Scrollable list for alerts (inside a inset border frame)
        scroll_inset = ctk.CTkFrame(
            self.alert_panel, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        scroll_inset.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self.alerts_scroll = ctk.CTkScrollableFrame(
            scroll_inset, fg_color="transparent", height=120, corner_radius=0
        )
        self.alerts_scroll.pack(fill="both", expand=True, padx=2, pady=2)

        self.refresh_alerts_list()

    def update_realtime_data(self, result: PresenceResult, is_alert: bool = False, alert_type: str = "", bio_result=None):
        """Called every time scanner streams new RSSI values."""
        cfg = get_config()

        # Update Status Card
        self.status_card.set_state(result.presence, result.activity, result.confidence, is_alert, alert_type)

        # Update Metrics panel (Fetch real Wi-Fi SSID)
        active_ssid = get_active_wifi_ssid()
        if active_ssid:
            target_desc = f"{active_ssid} (Đang kết nối)"
        else:
            target_ssid = cfg.target_ssid or "HomeWifi-5G (Mô phỏng)"
            target_desc = f"{target_ssid}"
            if cfg.target_bssid:
                target_desc += f" ({cfg.target_bssid[:8]}..)"
        
        self.metrics["target_ap"].configure(text=target_desc)
        self.metrics["rssi_strength"].configure(text=f"{int(result.rssi_mean)} dBm")
        self.metrics["signal_var"].configure(text=f"{result.rssi_variance:.3f}")
        self.metrics["sensitivity"].configure(text=f"{cfg.sensitivity:.2f}x")

        # Calibration status
        if not cfg.is_calibrated:
            self.metrics["calib_status"].configure(text="Đang phân tích nền...", text_color="#a21caf")
        else:
            self.metrics["calib_status"].configure(text="Hoàn thành (Đã khóa)", text_color="#15803d")

        # Fetch recent snapshots from DB to draw chart
        snapshots = self.db.get_rssi_last_n(n=100)
        if snapshots:
            ts = [s.timestamp for s in snapshots]
            rssis = [s.rssi for s in snapshots]
            vars_ = [s.variance for s in snapshots]
            self.chart.update_chart(ts, rssis, vars_)

        # Clear existing dynamic occupant widgets
        for child in self.vitals_scroll.winfo_children():
            child.destroy()

        # Update Bio Metrics UI fields
        if bio_result:
            # Update People Count
            people_conf = int(bio_result.people_confidence * 100)
            self.lbl_people_val.configure(
                text=f"{bio_result.people_count} người (Độ tin cậy {people_conf}%)"
            )

            # Render vital cards for each occupant
            vitals_list = getattr(bio_result, "people_vitals", [])
            if not vitals_list or bio_result.people_count == 0:
                empty_lbl = ctk.CTkLabel(
                    self.vitals_scroll,
                    text="📭 Phòng trống (Không phát hiện sinh hiệu)",
                    text_color="#7f8c8d",
                    font=ctk.CTkFont(family="Tahoma", size=12, slant="italic")
                )
                empty_lbl.pack(pady=30, fill="x")
            else:
                for occupant in vitals_list:
                    # Occupant frame (outset bevel)
                    occ_frame = ctk.CTkFrame(
                        self.vitals_scroll,
                        fg_color="#d4d0c8",
                        border_color="#ffffff",
                        border_width=1.5,
                        corner_radius=0
                    )
                    occ_frame.pack(fill="x", pady=4, padx=2)

                    # Occupant title bar (Yahoo theme colors)
                    title_row = ctk.CTkFrame(occ_frame, fg_color="#000080" if occupant.get("id") == 1 else "#808080", height=20, corner_radius=0)
                    title_row.pack(fill="x", padx=1, pady=1)

                    occ_name = occupant.get("name")
                    if occupant.get("id") == 1:
                        occ_name = "👤 Người thứ 1 (Cụ Ông / Cụ Bà)"
                    else:
                        occ_name = f"👤 Người thứ {occupant.get('id')} (Người cùng phòng)"

                    lbl_occ_name = ctk.CTkLabel(
                        title_row,
                        text=occ_name,
                        text_color="#ffffff",
                        font=ctk.CTkFont(family="Tahoma", size=11, weight="bold")
                    )
                    lbl_occ_name.pack(side="left", padx=5)

                    # Vitals content
                    vitals_content = ctk.CTkFrame(occ_frame, fg_color="transparent")
                    vitals_content.pack(fill="x", padx=10, pady=5)

                    # Heart rate row
                    hr_val = occupant.get("heart_rate")
                    hr_str = f"{hr_val:.1f} BPM" if hr_val is not None else "-- BPM"
                    hr_mode = "Ước tính" if bio_result.heart_rate_estimated or occupant.get("id") > 1 else bio_result.heart_rate_source.upper()
                    hr_color = "#b91c1c" if bio_result.heart_rate_estimated or occupant.get("id") > 1 else "#15803d"
                    
                    row_hr = ctk.CTkFrame(vitals_content, fg_color="transparent")
                    row_hr.pack(fill="x", pady=2)
                    ctk.CTkLabel(row_hr, text="💓 Nhịp tim:", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12)).pack(side="left")
                    ctk.CTkLabel(row_hr, text=f"{hr_str} ({hr_mode})", text_color=hr_color, font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")).pack(side="right")

                    # Temp row
                    temp_val = occupant.get("body_temp")
                    temp_str = f"{temp_val:.1f} °C" if temp_val is not None else "-- °C"
                    temp_mode = "Ước tính" if bio_result.body_temp_estimated or occupant.get("id") > 1 else bio_result.body_temp_source.upper()
                    temp_color = "#c2410c" if bio_result.body_temp_estimated or occupant.get("id") > 1 else "#15803d"
                    
                    row_temp = ctk.CTkFrame(vitals_content, fg_color="transparent")
                    row_temp.pack(fill="x", pady=2)
                    ctk.CTkLabel(row_temp, text="🌡️ Nhiệt độ:", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12)).pack(side="left")
                    ctk.CTkLabel(row_temp, text=f"{temp_str} ({temp_mode})", text_color=temp_color, font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")).pack(side="right")

                    # SpO2 row (for primary occupant only)
                    if occupant.get("id") == 1:
                        spo2_val = occupant.get("spo2")
                        spo2_str = f"{spo2_val:.1f}% (MAX30102)" if spo2_val is not None else "N/A (Chờ cảm biến)"
                        spo2_color = "#15803d" if spo2_val is not None else "#555555"
                        
                        row_spo2 = ctk.CTkFrame(vitals_content, fg_color="transparent")
                        row_spo2.pack(fill="x", pady=2)
                        ctk.CTkLabel(row_spo2, text="🩸 Oxy SpO2:", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12)).pack(side="left")
                        ctk.CTkLabel(row_spo2, text=spo2_str, text_color=spo2_color, font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")).pack(side="right")
        else:
            self.lbl_people_val.configure(text="-- người")
            empty_lbl = ctk.CTkLabel(
                self.vitals_scroll,
                text="📭 Đang kết nối dữ liệu...",
                text_color="#7f8c8d",
                font=ctk.CTkFont(family="Tahoma", size=12, slant="italic")
            )
            empty_lbl.pack(pady=30, fill="x")

    def refresh_alerts_list(self):
        """Re-fetches and displays current active/past alerts in the list."""
        # Clear current scroll frame children
        for child in self.alerts_scroll.winfo_children():
            child.destroy()

        alerts = self.db.get_recent_alerts(limit=10)
        
        if not alerts:
            no_alert_lbl = ctk.CTkLabel(
                self.alerts_scroll, text="🟢 Phòng hoạt động an toàn, không có cảnh báo nào.",
                text_color="#16803d", font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
            )
            no_alert_lbl.pack(pady=35)
            return

        for a in alerts:
            time_str = time.strftime("%H:%M:%S", time.localtime(a.timestamp))
            is_danger = a.alert_type == "FALL"
            
            item_frame = ctk.CTkFrame(
                self.alerts_scroll, fg_color="#f8fafc" if not is_danger else "#fee2e2", 
                border_color="#808080" if not is_danger else "#b91c1c", 
                border_width=1.5, corner_radius=0
            )
            item_frame.pack(fill="x", pady=4, padx=5)

            icon = "🔴" if is_danger else "⚠️"
            title = f"{icon} CẢNH BÁO: PHÁT HIỆN TÉ NGÃ" if is_danger else f"{icon} CẢNH BÁO: BẤT ĐỘNG QUÁ LÂU"
            
            lbl_title = ctk.CTkLabel(
                item_frame, text=title, text_color="#b91c1c" if is_danger else "#c2410c",
                font=ctk.CTkFont(family="Tahoma", size=14, weight="bold")
            )
            lbl_title.pack(anchor="w", padx=10, pady=(6, 2))

            lbl_desc = ctk.CTkLabel(
                item_frame, text=f"{time_str} · {a.message}", text_color="#000000",
                font=ctk.CTkFont(family="Tahoma", size=13), justify="left", anchor="w"
            )
            lbl_desc.pack(anchor="w", padx=10, pady=(2, 6))
