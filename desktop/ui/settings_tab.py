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
settings_tab.py — Configuration screen for Wifi-Censor Desktop.
Allows selecting target APs, tweaking sensitivity, triggering calibration, and customizing JSON output path.
"""

import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from typing import Callable, List, Optional
from desktop.app.config import get_config, get_config_manager
from desktop.app.scanner import WifiNetwork


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, on_recalibrate: Callable[[], None], on_scan_once: Callable[[], List[WifiNetwork]], **kwargs):
        super().__init__(parent, fg_color="#050810", **kwargs)

        self.on_recalibrate = on_recalibrate
        self.on_scan_once = on_scan_once
        self.scanned_networks: List[WifiNetwork] = []

        # Configure Layout (scrollable setting container)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        # ── Group 1: Wi-Fi Scanner Config ─────────────────────────────────────
        self.group_wifi = ctk.CTkFrame(self.scroll_container, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12)
        self.group_wifi.pack(fill="x", pady=(0, 15), padx=5)

        self.lbl_wifi_title = ctk.CTkLabel(self.group_wifi, text="1. CẤU HÌNH KẾT NỐI SÓNG WI-FI", text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=16, weight="bold"))
        self.lbl_wifi_title.pack(anchor="w", padx=15, pady=(15, 8))

        # Target AP Selection Rows
        row_select = ctk.CTkFrame(self.group_wifi, fg_color="transparent")
        row_select.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(row_select, text="Mạng Wi-Fi Giám Sát:", text_color="#cbd5e1", font=ctk.CTkFont(family="Inter", size=14, weight="bold")).pack(side="left")
        
        self.ap_select = ctk.CTkOptionMenu(
            row_select, values=["Dùng mạng mạnh nhất (Mặc định)"],
            fg_color="#1f2937", button_color="#374151", button_hover_color="#4b5563",
            width=280, height=32, dropdown_fg_color="#0d1117", dropdown_hover_color="#1f2937",
            dropdown_text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), command=self._handle_ap_change
        )
        self.ap_select.pack(side="right")

        self.btn_refresh_ap = ctk.CTkButton(
            self.group_wifi, text="🔍 Dò quét & tìm kiếm các mạng xung quanh",
            fg_color="#1f2937", hover_color="#374151", text_color="#f8fafc",
            height=34, font=ctk.CTkFont(family="Inter", size=13, weight="bold"), command=self.refresh_scanned_aps
        )
        self.btn_refresh_ap.pack(anchor="e", padx=15, pady=(5, 15))

        # ── Group 2: Thresholds & Sensitivity ────────────────────────────────
        self.group_thresh = ctk.CTkFrame(self.scroll_container, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12)
        self.group_thresh.pack(fill="x", pady=(0, 15), padx=5)

        self.lbl_thresh_title = ctk.CTkLabel(self.group_thresh, text="2. ĐỘ NHẠY & HIỆU CHỈNH PHÒNG TRỐNG", text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=16, weight="bold"))
        self.lbl_thresh_title.pack(anchor="w", padx=15, pady=(15, 8))

        # Sensitivity Row
        row_sens = ctk.CTkFrame(self.group_thresh, fg_color="transparent")
        row_sens.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(row_sens, text="Mức độ nhạy bén:", text_color="#cbd5e1", font=ctk.CTkFont(family="Inter", size=14, weight="bold")).pack(side="left")
        
        self.lbl_sens_val = ctk.CTkLabel(row_sens, text="1.00x", text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=14, weight="bold"))
        self.lbl_sens_val.pack(side="right", padx=(5, 0))
        
        self.slider_sens = ctk.CTkSlider(
            row_sens, from_=0.5, to=3.0, number_of_steps=25,
            button_color="#6366f1", button_hover_color="#4f46e5", progress_color="#6366f1",
            width=200, height=18, command=self._handle_sens_slider
        )
        self.slider_sens.pack(side="right")

        # Immobility Timeout Row
        row_immob = ctk.CTkFrame(self.group_thresh, fg_color="transparent")
        row_immob.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(row_immob, text="Thời gian chờ cảnh báo bất động:", text_color="#cbd5e1", font=ctk.CTkFont(family="Inter", size=14, weight="bold")).pack(side="left")
        
        self.lbl_immob_val = ctk.CTkLabel(row_immob, text="30 phút", text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=14, weight="bold"))
        self.lbl_immob_val.pack(side="right", padx=(5, 0))
        
        self.slider_immob = ctk.CTkSlider(
            row_immob, from_=5, to=120, number_of_steps=23,
            button_color="#6366f1", button_hover_color="#4f46e5", progress_color="#6366f1",
            width=200, height=18, command=self._handle_immob_slider
        )
        self.slider_immob.pack(side="right")

        # Calibration Box
        self.calib_box = ctk.CTkFrame(self.group_thresh, fg_color="#181d26", corner_radius=8)
        self.calib_box.pack(fill="x", padx=15, pady=(8, 15))

        self.lbl_calib_info = ctk.CTkLabel(
            self.calib_box, text="Thiết lập nhiễu sóng nền giúp cảm biến khử các tác nhân tĩnh trong môi trường.\nVui lòng chạy hiệu chỉnh lúc PHÒNG TRỐNG HOÀN TOÀN để có độ chính xác tốt nhất.",
            text_color="#94a3b8", font=ctk.CTkFont(family="Inter", size=13, weight="bold"), justify="left"
        )
        self.lbl_calib_info.pack(anchor="w", padx=15, pady=(12, 6))

        self.lbl_baseline_var = ctk.CTkLabel(
            self.calib_box, text="Mức sóng nền hiện tại: --",
            text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=14, weight="bold")
        )
        self.lbl_baseline_var.pack(anchor="w", padx=15, pady=4)

        self.btn_calib = ctk.CTkButton(
            self.calib_box, text="🔄 Chạy hiệu chỉnh phòng trống (30 giây)",
            fg_color="#06b6d4", hover_color="#0891b2", text_color="#ffffff",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"), height=36,
            command=self._trigger_calibration
        )
        self.btn_calib.pack(fill="x", padx=15, pady=(8, 15))

        # ── Group 3: Web Dashboard Integration ────────────────────────────────
        self.group_web = ctk.CTkFrame(self.scroll_container, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12)
        self.group_web.pack(fill="x", pady=(0, 15), padx=5)

        self.lbl_web_title = ctk.CTkLabel(self.group_web, text="3. ĐỒNG BỘ DỮ LIỆU ĐẾN WEB DASHBOARD", text_color="#f8fafc", font=ctk.CTkFont(family="Inter", size=16, weight="bold"))
        self.lbl_web_title.pack(anchor="w", padx=15, pady=(15, 8))

        # Toggle export
        row_toggle = ctk.CTkFrame(self.group_web, fg_color="transparent")
        row_toggle.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(row_toggle, text="Kích hoạt tự động xuất tệp JSON:", text_color="#cbd5e1", font=ctk.CTkFont(family="Inter", size=14, weight="bold")).pack(side="left")
        
        self.switch_export = ctk.CTkSwitch(
            row_toggle, text="", progress_color="#10b981",
            command=self._handle_export_toggle
        )
        self.switch_export.pack(side="right")

        # Path picker
        row_path = ctk.CTkFrame(self.group_web, fg_color="transparent")
        row_path.pack(fill="x", padx=15, pady=(6, 15))
        
        self.entry_path = ctk.CTkEntry(
            row_path, fg_color="#1f2937", border_color="#374151",
            text_color="#f8fafc", height=32, font=ctk.CTkFont(family="Inter", size=12)
        )
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            row_path, text="Chọn Thư Mục Lưu", fg_color="#1f2937", hover_color="#374151",
            text_color="#f8fafc", width=140, height=32, font=ctk.CTkFont(family="Inter", size=13, weight="bold"), command=self._browse_export_path
        )
        self.btn_browse.pack(side="right")

        # Load values into UI elements
        self._load_settings_values()

    def _load_settings_values(self):
        cfg = get_config()

        # Target AP dropdown option matching BSSID/SSID
        if cfg.target_bssid and cfg.target_ssid:
            self.ap_select.set(f"{cfg.target_ssid} ({cfg.target_bssid})")
        else:
            self.ap_select.set("Dùng mạng mạnh nhất (Mặc định)")

        # Sliders
        self.slider_sens.set(cfg.sensitivity)
        self.lbl_sens_val.configure(text=f"{cfg.sensitivity:.2f}x")

        self.slider_immob.set(cfg.immobility_threshold_min)
        self.lbl_immob_val.configure(text=f"{cfg.immobility_threshold_min} phút")

        # Baseline
        if cfg.is_calibrated:
            self.lbl_baseline_var.configure(text=f"Baseline Variance hiện tại: {cfg.baseline_variance:.4f}")
            self.btn_calib.configure(text="🔄 Chạy lại hiệu chỉnh phòng trống", fg_color="#1f2937")
        else:
            self.lbl_baseline_var.configure(text="Baseline Variance hiện tại: Chưa hiệu chỉnh")
            self.btn_calib.configure(text="🔄 Chạy hiệu chỉnh phòng trống (30 giây)", fg_color="#06b6d4")

        # Export configs
        if cfg.json_export_enabled:
            self.switch_export.select()
        else:
            self.switch_export.deselect()

        manager = get_config_manager()
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, str(manager.get_export_path()))

    def refresh_scanned_aps(self):
        """Scans the airwaves and fills the drop-down menu with actual networks found."""
        self.btn_refresh_ap.configure(text="⏳ Đang quét sóng mạng...")
        self.update()

        try:
            networks = self.on_scan_once()
            self.scanned_networks = networks

            # Build readable entries
            options = ["Dùng mạng mạnh nhất (Mặc định)"]
            seen_bssids = set()

            for n in networks:
                if n.bssid not in seen_bssids:
                    seen_bssids.add(n.bssid)
                    options.append(f"{n.ssid} ({n.bssid})")

            self.ap_select.configure(values=options)
            
            # Show positive state
            self.btn_refresh_ap.configure(text="✅ Đã cập nhật mạng phát!")
        except Exception as e:
            print(f"[Settings] Scanning failed: {e}")
            self.btn_refresh_ap.configure(text="❌ Quét thất bại. Thử lại")

        self.after(2000, lambda: self.btn_refresh_ap.configure(text="🔍 Quét & tìm thiết bị phát xung quanh"))

    def _handle_ap_change(self, value: str):
        manager = get_config_manager()
        if value == "Dùng mạng mạnh nhất (Mặc định)":
            manager.update(target_bssid="", target_ssid="")
        else:
            # Parse SSID and BSSID out of string format "SSID (BSSID)"
            for n in self.scanned_networks:
                if f"{n.ssid} ({n.bssid})" == value:
                    manager.update(target_bssid=n.bssid, target_ssid=n.ssid)
                    break

    def _handle_sens_slider(self, val: float):
        self.lbl_sens_val.configure(text=f"{val:.2f}x")
        get_config_manager().update(sensitivity=round(val, 2))

    def _handle_immob_slider(self, val: float):
        minutes = int(val)
        self.lbl_immob_val.configure(text=f"{minutes} phút")
        get_config_manager().update(immobility_threshold_min=minutes)

    def _handle_export_toggle(self):
        enabled = self.switch_export.get() == 1
        get_config_manager().update(json_export_enabled=enabled)

    def _browse_export_path(self):
        current_path = self.entry_path.get()
        dir_name = os.path.dirname(current_path)

        # File picker dialog for saving
        selected_file = filedialog.asksaveasfilename(
            initialdir=dir_name,
            title="Đường dẫn xuất tệp trạng thái JSON",
            filetypes=[("JSON files", "*.json")],
            defaultextension=".json"
        )
        if selected_file:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, selected_file)
            get_config_manager().update(json_export_path=selected_file)

    def _trigger_calibration(self):
        # Call the calibration callback
        self.on_recalibrate()

        # Update UI feedback
        self.btn_calib.configure(text="⏳ Đang ghi nhận tín hiệu phòng trống...", fg_color="#d97706")
        self.lbl_baseline_var.configure(text="Hiệu chỉnh: Giai đoạn thu thập mẫu...")
        self.update()

        # The actual progress will update the config, we poll config values after 30 seconds
        # Wait, since calibration runs asynchronously in the scanner/engine loop,
        # we can monitor and wait, or let it update dynamically. Let's poll in 5s intervals.
        self._check_calibration_status(0)

    def _check_calibration_status(self, attempts: int):
        cfg = get_config()
        if cfg.is_calibrated:
            self.lbl_baseline_var.configure(text=f"Baseline Variance hiện tại: {cfg.baseline_variance:.4f}")
            self.btn_calib.configure(text="🔄 Chạy lại hiệu chỉnh phòng trống", fg_color="#1f2937")
        elif attempts < 10:
            # Poll every 3 seconds for 30s
            self.lbl_baseline_var.configure(text=f"Hiệu chỉnh: Đang học... ({attempts * 10}%)")
            self.after(3000, lambda: self._check_calibration_status(attempts + 1))
        else:
            # Safe reset
            self.lbl_baseline_var.configure(text="Hiệu chỉnh hoàn thành!")
            self._load_settings_values()
