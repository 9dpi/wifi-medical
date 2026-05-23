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
settings_tab.py — Configuration screen for Wifi-Censor Desktop (Windows 98 Retro Style).
All settings panels are transformed into classic outset bevel boxes with classic fonts.
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
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)

        self.on_recalibrate = on_recalibrate
        self.on_scan_once = on_scan_once
        self.scanned_networks: List[WifiNetwork] = []

        # Configure Layout (scrollable setting container)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        # ── Group 1: Wi-Fi Scanner Config ─────────────────────────────────────
        self.group_wifi = ctk.CTkFrame(
            self.scroll_container, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.group_wifi.pack(fill="x", pady=(0, 10), padx=5)

        title_bar_wifi = ctk.CTkFrame(self.group_wifi, fg_color="#000080", height=24, corner_radius=0)
        title_bar_wifi.pack(fill="x", padx=2, pady=2)

        self.lbl_wifi_title = ctk.CTkLabel(
            title_bar_wifi, text="1. CẤU HÌNH KẾT NỐI SÓNG WI-FI", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.lbl_wifi_title.pack(anchor="w", padx=6, pady=2)

        # Target AP Selection Rows
        row_select = ctk.CTkFrame(self.group_wifi, fg_color="transparent")
        row_select.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            row_select, text="Mạng Wi-Fi Giám Sát:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.ap_select = ctk.CTkOptionMenu(
            row_select, values=["Dùng mạng mạnh nhất (Mặc định)"],
            fg_color="#ffffff", button_color="#d4d0c8", button_hover_color="#e6e6e6",
            text_color="#000000", width=280, height=30, corner_radius=0,
            dropdown_fg_color="#ffffff", dropdown_hover_color="#e6e6e6",
            dropdown_text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"), command=self._handle_ap_change
        )
        self.ap_select.pack(side="right")

        self.btn_refresh_ap = ctk.CTkButton(
            self.group_wifi, text="🔍 Dò quét & tìm kiếm các mạng xung quanh",
            fg_color="#d4d0c8", hover_color="#e6e6e6", text_color="#000000",
            border_width=2, border_color="#ffffff", height=32, corner_radius=0,
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"), command=self.refresh_scanned_aps
        )
        self.btn_refresh_ap.pack(anchor="e", padx=15, pady=(5, 12))

        # ── Group 2: Thresholds & Sensitivity ────────────────────────────────
        self.group_thresh = ctk.CTkFrame(
            self.scroll_container, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.group_thresh.pack(fill="x", pady=(0, 10), padx=5)

        title_bar_thresh = ctk.CTkFrame(self.group_thresh, fg_color="#000080", height=24, corner_radius=0)
        title_bar_thresh.pack(fill="x", padx=2, pady=2)

        self.lbl_thresh_title = ctk.CTkLabel(
            title_bar_thresh, text="2. ĐỘ NHẠY & HIỆU CHỈNH PHÒNG TRỐNG", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.lbl_thresh_title.pack(anchor="w", padx=6, pady=2)

        # Sensitivity Row
        row_sens = ctk.CTkFrame(self.group_thresh, fg_color="transparent")
        row_sens.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            row_sens, text="Mức độ nhạy bén:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.lbl_sens_val = ctk.CTkLabel(
            row_sens, text="1.00x", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.lbl_sens_val.pack(side="right", padx=(5, 0))
        
        self.slider_sens = ctk.CTkSlider(
            row_sens, from_=0.5, to=3.0, number_of_steps=25,
            button_color="#d4d0c8", button_hover_color="#e6e6e6", progress_color="#000080",
            width=200, height=18, command=self._handle_sens_slider
        )
        self.slider_sens.pack(side="right")

        # Immobility Timeout Row
        row_immob = ctk.CTkFrame(self.group_thresh, fg_color="transparent")
        row_immob.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            row_immob, text="Thời gian chờ cảnh báo bất động:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.lbl_immob_val = ctk.CTkLabel(
            row_immob, text="30 phút", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.lbl_immob_val.pack(side="right", padx=(5, 0))
        
        self.slider_immob = ctk.CTkSlider(
            row_immob, from_=5, to=120, number_of_steps=23,
            button_color="#d4d0c8", button_hover_color="#e6e6e6", progress_color="#000080",
            width=200, height=18, command=self._handle_immob_slider
        )
        self.slider_immob.pack(side="right")

        # Calibration Box (Inset Bevel styled)
        self.calib_box = ctk.CTkFrame(
            self.group_thresh, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        self.calib_box.pack(fill="x", padx=15, pady=(8, 12))

        self.lbl_calib_info = ctk.CTkLabel(
            self.calib_box, text="Thiết lập nhiễu sóng nền giúp cảm biến khử các tác nhân tĩnh trong môi trường.\nVui lòng chạy hiệu chỉnh lúc PHÒNG TRỐNG HOÀN TOÀN để có độ chính xác tốt nhất.",
            text_color="#555555", font=ctk.CTkFont(family="Tahoma", size=12), justify="left"
        )
        self.lbl_calib_info.pack(anchor="w", padx=15, pady=(10, 4))

        self.lbl_baseline_var = ctk.CTkLabel(
            self.calib_box, text="Mức sóng nền hiện tại: --",
            text_color="#000080", font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.lbl_baseline_var.pack(anchor="w", padx=15, pady=4)

        self.btn_calib = ctk.CTkButton(
            self.calib_box, text="🔄 Chạy hiệu chỉnh phòng trống (30 giây)",
            fg_color="#d4d0c8", hover_color="#e6e6e6", text_color="#000000",
            border_width=2, border_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"), height=32, corner_radius=0,
            command=self._trigger_calibration
        )
        self.btn_calib.pack(fill="x", padx=15, pady=(6, 12))

        # ── Group 3: Web Dashboard Integration ────────────────────────────────
        self.group_web = ctk.CTkFrame(
            self.scroll_container, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.group_web.pack(fill="x", pady=(0, 10), padx=5)

        title_bar_web = ctk.CTkFrame(self.group_web, fg_color="#000080", height=24, corner_radius=0)
        title_bar_web.pack(fill="x", padx=2, pady=2)

        self.lbl_web_title = ctk.CTkLabel(
            title_bar_web, text="3. ĐỒNG BỘ DỮ LIỆU ĐẾN WEB DASHBOARD", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.lbl_web_title.pack(anchor="w", padx=6, pady=2)

        # Toggle export
        row_toggle = ctk.CTkFrame(self.group_web, fg_color="transparent")
        row_toggle.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(
            row_toggle, text="Kích hoạt tự động xuất tệp JSON:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.switch_export = ctk.CTkSwitch(
            row_toggle, text="", progress_color="#000080",
            command=self._handle_export_toggle
        )
        self.switch_export.pack(side="right")

        # Path picker
        row_path = ctk.CTkFrame(self.group_web, fg_color="transparent")
        row_path.pack(fill="x", padx=15, pady=(6, 12))
        
        self.entry_path = ctk.CTkEntry(
            row_path, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13)
        )
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            row_path, text="Chọn Thư Mục Lưu", fg_color="#d4d0c8", hover_color="#e6e6e6",
            text_color="#000000", border_width=2, border_color="#ffffff",
            width=140, height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"), command=self._browse_export_path
        )
        self.btn_browse.pack(side="right")

        # ── Group 4: GitHub Sync ──────────────────────────────────────────────
        self.group_github = ctk.CTkFrame(
            self.scroll_container, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.group_github.pack(fill="x", pady=(0, 10), padx=5)

        title_bar_github = ctk.CTkFrame(self.group_github, fg_color="#000080", height=24, corner_radius=0)
        title_bar_github.pack(fill="x", padx=2, pady=2)

        self.lbl_github_title = ctk.CTkLabel(
            title_bar_github, text="4. KẾT NỐI ĐỒNG BỘ GITHUB & ĐIỀU KHIỂN TỪ XA", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.lbl_github_title.pack(anchor="w", padx=6, pady=2)

        # Toggle Sync Switch
        row_sync_toggle = ctk.CTkFrame(self.group_github, fg_color="transparent")
        row_sync_toggle.pack(fill="x", padx=15, pady=6)
        
        ctk.CTkLabel(
            row_sync_toggle, text="Bật đồng bộ qua GitHub:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.switch_github = ctk.CTkSwitch(
            row_sync_toggle, text="", progress_color="#000080",
            command=self._handle_github_toggle
        )
        self.switch_github.pack(side="right")

        # GitHub Token PAT (password input)
        row_token = ctk.CTkFrame(self.group_github, fg_color="transparent")
        row_token.pack(fill="x", padx=15, pady=6)
        
        ctk.CTkLabel(
            row_token, text="GitHub Token (PAT):", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.entry_token = ctk.CTkEntry(
            row_token, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", show="*", height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13), width=280
        )
        self.entry_token.pack(side="right")

        # Username / Repo
        row_user_repo = ctk.CTkFrame(self.group_github, fg_color="transparent")
        row_user_repo.pack(fill="x", padx=15, pady=6)
        
        ctk.CTkLabel(
            row_user_repo, text="Tài khoản / Tên Repo:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        user_repo_sub = ctk.CTkFrame(row_user_repo, fg_color="transparent")
        user_repo_sub.pack(side="right")
        
        self.entry_username = ctk.CTkEntry(
            user_repo_sub, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", placeholder_text="Tài khoản", height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13), width=130
        )
        self.entry_username.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            user_repo_sub, text="/", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        self.entry_repo = ctk.CTkEntry(
            user_repo_sub, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", placeholder_text="Tên repo", height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13), width=130
        )
        self.entry_repo.pack(side="left")

        # Branch
        row_branch = ctk.CTkFrame(self.group_github, fg_color="transparent")
        row_branch.pack(fill="x", padx=15, pady=6)
        
        ctk.CTkLabel(
            row_branch, text="Nhánh (Branch):", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.entry_branch = ctk.CTkEntry(
            row_branch, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13), width=280
        )
        self.entry_branch.pack(side="right")

        # Device ID Selector
        row_device = ctk.CTkFrame(self.group_github, fg_color="transparent")
        row_device.pack(fill="x", padx=15, pady=6)
        
        ctk.CTkLabel(
            row_device, text="Định danh Thiết bị (Device ID):", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.entry_device = ctk.CTkEntry(
            row_device, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13), width=280
        )
        self.entry_device.pack(side="right")
        
        # Info Box and Warning Label (Inset Frame styled)
        row_warning = ctk.CTkFrame(
            self.group_github, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        row_warning.pack(fill="x", padx=15, pady=(8, 10))
        
        self.lbl_warning_text = ctk.CTkLabel(
            row_warning,
            text="⚠️ Khuyến cáo bảo mật: Vui lòng chỉ dùng token (PAT) có quyền contents:write\nvà giới hạn trong kho lưu trữ này. Không sử dụng Token cá nhân có quyền quản trị tối cao.",
            text_color="#b45309", font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"), justify="left"
        )
        self.lbl_warning_text.pack(anchor="w", padx=15, pady=10)

        # Button row: Save Config & Test Connection
        row_buttons = ctk.CTkFrame(self.group_github, fg_color="transparent")
        row_buttons.pack(fill="x", padx=15, pady=(10, 15))
        
        self.btn_save_github = ctk.CTkButton(
            row_buttons, text="💾 Lưu Cấu hình", fg_color="#d4d0c8", hover_color="#e6e6e6",
            text_color="#000000", border_width=2, border_color="#ffffff",
            height=32, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"), command=self._save_github_settings
        )
        self.btn_save_github.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_test_github = ctk.CTkButton(
            row_buttons, text="🔌 Kiểm Tra Kết Nối", fg_color="#d4d0c8", hover_color="#e6e6e6",
            text_color="#000000", border_width=2, border_color="#ffffff",
            height=30, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=11, weight="bold"), command=self._test_github_connection
        )
        self.btn_test_github.pack(side="right", fill="x", expand=True)

        # ── Group 5: AI Agent Configuration ──────────────────────────────────────
        self.group_ai = ctk.CTkFrame(
            self.scroll_container, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.group_ai.pack(fill="x", pady=(0, 10), padx=5)

        title_bar_ai = ctk.CTkFrame(self.group_ai, fg_color="#000080", height=24, corner_radius=0)
        title_bar_ai.pack(fill="x", padx=2, pady=2)

        ctk.CTkLabel(
            title_bar_ai,
            text="5. TRỢ LÝ AI (OLLAMA - CHẠY LOCAL)",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(anchor="w", padx=6, pady=2)

        ctk.CTkLabel(
            self.group_ai,
            text="AI chạy hoàn toàn trên máy bạn — không cần internet, dữ liệu không rời khỏi thiết bị.",
            text_color="#555555",
            font=ctk.CTkFont(family="Tahoma", size=11, slant="italic")
        ).pack(anchor="w", padx=15, pady=(4, 8))

        # Enable toggle
        row_ai_enable = ctk.CTkFrame(self.group_ai, fg_color="transparent")
        row_ai_enable.pack(fill="x", padx=15, pady=4)
        
        ctk.CTkLabel(
            row_ai_enable, text="Bật Trợ lý AI:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.switch_ai = ctk.CTkSwitch(
            row_ai_enable, text="", progress_color="#000080",
            command=self._handle_ai_toggle
        )
        self.switch_ai.pack(side="right")

        # Ollama URL
        row_ollama_url = ctk.CTkFrame(self.group_ai, fg_color="transparent")
        row_ollama_url.pack(fill="x", padx=15, pady=4)
        
        ctk.CTkLabel(
            row_ollama_url, text="Ollama URL:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.entry_ollama_url = ctk.CTkEntry(
            row_ollama_url, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", height=30, width=250, corner_radius=0,
            font=ctk.CTkFont(family="Tahoma", size=13)
        )
        self.entry_ollama_url.pack(side="right")

        # Model name
        row_model = ctk.CTkFrame(self.group_ai, fg_color="transparent")
        row_model.pack(fill="x", padx=15, pady=4)
        
        ctk.CTkLabel(
            row_model, text="Model AI:", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.entry_ai_model = ctk.CTkEntry(
            row_model, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", height=30, width=200, corner_radius=0,
            font=ctk.CTkFont(family="Tahoma", size=13)
        )
        self.entry_ai_model.pack(side="right")

        # Report hour
        row_report_hour = ctk.CTkFrame(self.group_ai, fg_color="transparent")
        row_report_hour.pack(fill="x", padx=15, pady=4)
        
        ctk.CTkLabel(
            row_report_hour, text="Giờ tạo báo cáo tự động (0-23):", text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        ).pack(side="left")
        
        self.entry_report_hour = ctk.CTkEntry(
            row_report_hour, fg_color="#ffffff", border_color="#808080", border_width=2,
            text_color="#000000", height=30, width=60, corner_radius=0,
            font=ctk.CTkFont(family="Tahoma", size=13)
        )
        self.entry_report_hour.pack(side="right")

        # AI status + save + test buttons
        row_ai_btns = ctk.CTkFrame(self.group_ai, fg_color="transparent")
        row_ai_btns.pack(fill="x", padx=15, pady=(8, 12))

        self.btn_save_ai = ctk.CTkButton(
            row_ai_btns, text="💾 Lưu AI Settings", fg_color="#d4d0c8", hover_color="#e6e6e6",
            text_color="#000000", border_width=2, border_color="#ffffff",
            height=32, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"),
            command=self._save_ai_settings
        )
        self.btn_save_ai.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_test_ai = ctk.CTkButton(
            row_ai_btns, text="🔌 Test Kết Nối Ollama", fg_color="#d4d0c8", hover_color="#e6e6e6",
            text_color="#000000", border_width=2, border_color="#ffffff",
            height=32, corner_radius=0, font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"),
            command=self._test_ollama_connection
        )
        self.btn_test_ai.pack(side="right", fill="x", expand=True)

        self.lbl_ai_status = ctk.CTkLabel(
            self.group_ai, text="",
            font=ctk.CTkFont(family="Tahoma", size=13), text_color="#555555"
        )
        self.lbl_ai_status.pack(anchor="w", padx=15, pady=(0, 8))

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
            self.lbl_baseline_var.configure(text=f"Mức sóng nền hiện tại: Baseline Variance = {cfg.baseline_variance:.4f}")
            self.btn_calib.configure(text="🔄 Chạy lại hiệu chỉnh phòng trống", fg_color="#d4d0c8")
        else:
            self.lbl_baseline_var.configure(text="Mức sóng nền hiện tại: Chưa hiệu chỉnh")
            self.btn_calib.configure(text="🔄 Chạy hiệu chỉnh phòng trống (30 giây)", fg_color="#d4d0c8")

        # Export configs
        if cfg.json_export_enabled:
            self.switch_export.select()
        else:
            self.switch_export.deselect()

        manager = get_config_manager()
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, str(manager.get_export_path()))

        # GitHub sync fields
        if cfg.github_sync_enabled:
            self.switch_github.select()
        else:
            self.switch_github.deselect()

        self.entry_token.delete(0, "end")
        self.entry_token.insert(0, cfg.github_token)

        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, cfg.github_username)

        self.entry_repo.delete(0, "end")
        self.entry_repo.insert(0, cfg.github_repo)

        self.entry_branch.delete(0, "end")
        self.entry_branch.insert(0, cfg.github_branch)

        self.entry_device.delete(0, "end")
        self.entry_device.insert(0, cfg.github_device_id)

        # AI Configs
        if cfg.ai_enabled:
            self.switch_ai.select()
        else:
            self.switch_ai.deselect()

        self.entry_ollama_url.delete(0, "end")
        self.entry_ollama_url.insert(0, cfg.ollama_url)

        self.entry_ai_model.delete(0, "end")
        self.entry_ai_model.insert(0, cfg.ollama_model)

        self.entry_report_hour.delete(0, "end")
        self.entry_report_hour.insert(0, str(cfg.ai_report_hour))

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

        self.after(2000, lambda: self.btn_refresh_ap.configure(text="🔍 Dò quét & tìm kiếm các mạng xung quanh"))

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
        self.btn_calib.configure(text="⏳ Đang ghi nhận tín hiệu phòng trống...", fg_color="#d4d0c8")
        self.lbl_baseline_var.configure(text="Hiệu chỉnh: Giai đoạn thu thập mẫu...")
        self.update()

        # The actual progress will update the config, we poll config values after 30 seconds
        self._check_calibration_status(0)

    def _check_calibration_status(self, attempts: int):
        cfg = get_config()
        if cfg.is_calibrated:
            self.lbl_baseline_var.configure(text=f"Mức sóng nền hiện tại: Baseline Variance = {cfg.baseline_variance:.4f}")
            self.btn_calib.configure(text="🔄 Chạy lại hiệu chỉnh phòng trống", fg_color="#d4d0c8")
        elif attempts < 10:
            # Poll every 3 seconds for 30s
            self.lbl_baseline_var.configure(text=f"Hiệu chỉnh: Đang học... ({attempts * 10}%)")
            self.after(3000, lambda: self._check_calibration_status(attempts + 1))
        else:
            # Safe reset
            self.lbl_baseline_var.configure(text="Hiệu chỉnh hoàn thành!")
            self._load_settings_values()

    def _handle_github_toggle(self):
        enabled = self.switch_github.get() == 1
        get_config_manager().update(github_sync_enabled=enabled)

    def _save_github_settings(self):
        token = self.entry_token.get().strip()
        username = self.entry_username.get().strip()
        repo = self.entry_repo.get().strip()
        branch = self.entry_branch.get().strip()
        device_id = self.entry_device.get().strip()
        
        get_config_manager().update(
            github_token=token,
            github_username=username,
            github_repo=repo,
            github_branch=branch,
            github_device_id=device_id
        )
        
        self.btn_save_github.configure(text="✅ Đã Lưu Cấu Hình!", fg_color="#d4d0c8")
        self.after(2000, lambda: self.btn_save_github.configure(text="💾 Lưu Cấu Hình", fg_color="#d4d0c8"))

    def _test_github_connection(self):
        self.btn_test_github.configure(text="⏳ Đang kết nối...", state="disabled")
        self.update()
        
        token = self.entry_token.get().strip()
        username = self.entry_username.get().strip()
        repo = self.entry_repo.get().strip()
        branch = self.entry_branch.get().strip()
        
        def run_test():
            import requests
            url = f"https://api.github.com/repos/{username}/{repo}/branches/{branch}"
            headers = {
                'Authorization': f'token {token}' if token else '',
                'Accept': 'application/vnd.github.v3+json'
            }
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    status_text = "✅ Kết nối thành công!"
                else:
                    status_text = f"❌ Thất bại: HTTP {resp.status_code}"
            except Exception as e:
                status_text = "❌ Thất bại: Lỗi mạng"
                
            def update_ui():
                self.btn_test_github.configure(text="🔌 Kiểm Tra Kết Nối", fg_color="#d4d0c8", state="normal")
                self.lbl_warning_text.configure(text=status_text)
            
            self.after(0, update_ui)
            
        import threading
        threading.Thread(target=run_test, daemon=True).start()

    def _handle_ai_toggle(self):
        enabled = self.switch_ai.get() == 1
        get_config_manager().update(ai_enabled=enabled)
        self.lbl_ai_status.configure(
            text=f"AI Agent đã {'BẬT' if enabled else 'TẮT'}.",
            text_color="#000080" if enabled else "#555555"
        )

    def _save_ai_settings(self):
        url = self.entry_ollama_url.get().strip()
        model = self.entry_ai_model.get().strip()
        try:
            hour = int(self.entry_report_hour.get().strip())
            if not (0 <= hour <= 23):
                raise ValueError()
        except ValueError:
            self.lbl_ai_status.configure(text="❌ Giờ tạo báo cáo phải là số nguyên từ 0 đến 23", text_color="#ef4444")
            return

        get_config_manager().update(
            ollama_url=url,
            ollama_model=model,
            ai_report_hour=hour
        )
        self.btn_save_ai.configure(text="✅ Đã Lưu AI Settings!", fg_color="#d4d0c8")
        self.lbl_ai_status.configure(text="Cấu hình AI đã được lưu thành công.", text_color="#15803d")
        self.after(2000, lambda: self.btn_save_ai.configure(text="💾 Lưu AI Settings", fg_color="#d4d0c8"))

    def _test_ollama_connection(self):
        self.btn_test_ai.configure(text="⏳ Đang kết nối...", state="disabled")
        self.update()

        url = self.entry_ollama_url.get().strip()
        model = self.entry_ai_model.get().strip()

        def run_test():
            import requests
            try:
                # Test basic tag API to check if Ollama is running
                resp = requests.get(f"{url}/api/tags", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    # Check if model in any form (e.g. gemma4:e4b or gemma4:e4b:latest)
                    matched = False
                    for m in models:
                        if model == m or f"{model}:latest" == m or m.startswith(model + ":") or model.startswith(m + ":"):
                            matched = True
                            break
                    if matched:
                        status_text = f"✅ Kết nối thành công! Đã tìm thấy model '{model}'"
                        color = "#15803d"
                    else:
                        available_models = ", ".join(models[:3]) + ("..." if len(models) > 3 else "")
                        status_text = f"⚠️ Ollama OK, nhưng không có model '{model}'. Có: {available_models or 'Trống'}"
                        color = "#b45309"
                else:
                    status_text = f"❌ Thất bại: Ollama HTTP {resp.status_code}"
                    color = "#b91c1c"
            except Exception as e:
                status_text = f"❌ Không thể kết nối tới Ollama tại: {url}"
                color = "#b91c1c"

            def update_ui():
                self.btn_test_ai.configure(text="🔌 Test Kết Nối Ollama", fg_color="#d4d0c8", state="normal")
                self.lbl_ai_status.configure(text=status_text, text_color=color)

            self.after(0, update_ui)

        import threading
        threading.Thread(target=run_test, daemon=True).start()
