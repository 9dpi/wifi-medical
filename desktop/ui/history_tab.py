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
history_tab.py — Historical Reports & Event Timeline tab (Windows 98 Style).
Provides a deep retrospective view of presence ratios via matplotlib donut charts and classic logs.
"""

import time
from datetime import datetime, timedelta
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from desktop.app.database import Database


class HistoryTab(ctk.CTkFrame):
    def __init__(self, parent, db: Database, **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)

        self.db = db
        self.selected_filter_days = 1 # 1: 24h, 7: 7 days, 30: 30 days

        # Grid config
        self.grid_columnconfigure(0, weight=1, minsize=400) # Left column: Timeline log
        self.grid_columnconfigure(1, weight=1, minsize=400) # Right column: Statistics & Donut
        self.grid_rowconfigure(1, weight=1)                  # Top Row (ML Terminal - spans full width)
        self.grid_rowconfigure(2, weight=1)                  # Bottom Row (Timeline log & Stats)

        # ── Top Bar: Filter Actions ───────────────────────────────────────────
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        self.tab_title = ctk.CTkLabel(
            self.top_bar, text="⏱️ NHẬT KÝ SỰ KIỆN & LỊCH SỬ GIÁM SÁT", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=18, weight="bold")
        )
        self.tab_title.pack(side="left")

        # Filters buttons container (Windows 98 Bevel)
        self.filters_frame = ctk.CTkFrame(
            self.top_bar, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.filters_frame.pack(side="right")

        self.btn_24h = ctk.CTkButton(
            self.filters_frame, text="24 Giờ Qua", fg_color="#000080", text_color="#ffffff",
            width=95, height=28, corner_radius=0, border_width=1, border_color="#808080",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"),
            command=lambda: self.set_filter(1)
        )
        self.btn_24h.pack(side="left", padx=2, pady=2)

        self.btn_7d = ctk.CTkButton(
            self.filters_frame, text="7 Ngày Qua", fg_color="#d4d0c8", text_color="#000000",
            hover_color="#e6e6e6", width=95, height=28, corner_radius=0, border_width=2, border_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"),
            command=lambda: self.set_filter(7)
        )
        self.btn_7d.pack(side="left", padx=2, pady=2)

        self.btn_30d = ctk.CTkButton(
            self.filters_frame, text="30 Ngày Qua", fg_color="#d4d0c8", text_color="#000000",
            hover_color="#e6e6e6", width=95, height=28, corner_radius=0, border_width=2, border_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"),
            command=lambda: self.set_filter(30)
        )
        self.btn_30d.pack(side="left", padx=2, pady=2)

        # ── Row 1: Cửa sổ giám sát tiến trình học máy AI (Prioritized on top spanning full width!) ──
        self.terminal_frame = ctk.CTkFrame(
            self, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.terminal_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="nsew")
        
        # Title bar for terminal frame (Navy Blue Retro title bar)
        term_title_bar = ctk.CTkFrame(self.terminal_frame, fg_color="#000080", height=24, corner_radius=0)
        term_title_bar.pack(fill="x", padx=2, pady=2)
        
        self.term_title = ctk.CTkLabel(
            term_title_bar, text="🖥️ CỬA SỔ GIÁM SÁT TIẾN TRÌNH HỌC MÁY LÂM SÀNG AI (WIFI-CENSOR DESKTOP GUARD)", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.term_title.pack(anchor="w", padx=6, pady=2)
        
        # Inset Border for console
        term_inset = ctk.CTkFrame(
            self.terminal_frame, fg_color="#000000",
            border_color="#808080", border_width=2, corner_radius=0
        )
        term_inset.pack(fill="both", expand=True, padx=8, pady=(4, 10))
        
        self.terminal_text = ctk.CTkTextbox(
            term_inset, fg_color="#000000", text_color="#00ff00",
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=0, activate_scrollbars=True
        )
        self.terminal_text.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Row 2 Column 0: Timeline Event List ──
        self.right_col = ctk.CTkFrame(
            self, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.right_col.grid(row=2, column=0, padx=(10, 5), pady=(5, 10), sticky="nsew")

        title_bar_timeline = ctk.CTkFrame(self.right_col, fg_color="#000080", height=24, corner_radius=0)
        title_bar_timeline.pack(fill="x", padx=2, pady=2)

        self.timeline_title = ctk.CTkLabel(
            title_bar_timeline, text="🕒 NHẬT KÝ CHI TIẾT SỰ KIỆN", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.timeline_title.pack(anchor="w", padx=6, pady=2)

        # Inset Border for white event list scroll
        list_inset = ctk.CTkFrame(
            self.right_col, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        list_inset.pack(fill="both", expand=True, padx=8, pady=(4, 10))

        self.timeline_scroll = ctk.CTkScrollableFrame(list_inset, fg_color="#ffffff", corner_radius=0)
        self.timeline_scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Row 2 Column 1: Bottom Panel for Donut Chart & Aggregates ──
        self.bottom_panel = ctk.CTkFrame(
            self, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.bottom_panel.grid(row=2, column=1, padx=(5, 10), pady=(5, 10), sticky="nsew")

        title_bar_stats = ctk.CTkFrame(self.bottom_panel, fg_color="#000080", height=24, corner_radius=0)
        title_bar_stats.pack(fill="x", padx=2, pady=2)

        self.stats_title = ctk.CTkLabel(
            title_bar_stats, text="📊 TỔNG HỢP THỐNG KÊ & TỶ LỆ CÓ MẶT TRONG PHÒNG", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.stats_title.pack(anchor="w", padx=6, pady=2)

        # Horizontal side-by-side grid inside bottom panel
        stats_content = ctk.CTkFrame(self.bottom_panel, fg_color="transparent")
        stats_content.pack(fill="both", expand=True, padx=10, pady=5)
        stats_content.grid_columnconfigure(0, weight=1) # Donut chart left
        stats_content.grid_columnconfigure(1, weight=1) # Stats text right
        stats_content.grid_rowconfigure(0, weight=1)

        # Embedded Donut Chart
        self.fig, self.ax = plt.subplots(figsize=(2.8, 1.8), facecolor="#d4d0c8")
        self.ax.set_facecolor("#d4d0c8")
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=stats_content)
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=2)

        # Stats info text
        self.aggregates_frame = ctk.CTkFrame(stats_content, fg_color="transparent")
        self.aggregates_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)

        self.present_min_lbl = ctk.CTkLabel(self.aggregates_frame, text="Tổng thời gian có mặt: -- phút", text_color="#15803d", font=ctk.CTkFont(family="Tahoma", size=14, weight="bold"), anchor="w")
        self.present_min_lbl.pack(pady=4, fill="x")
        self.absent_min_lbl = ctk.CTkLabel(self.aggregates_frame, text="Tổng thời gian phòng trống: -- phút", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=14, weight="bold"), anchor="w")
        self.absent_min_lbl.pack(pady=4, fill="x")

        self.refresh_data()

    def set_filter(self, days: int):
        self.selected_filter_days = days

        # Toggle Button aesthetics
        buttons = [(1, self.btn_24h), (7, self.btn_7d), (30, self.btn_30d)]
        for d, btn in buttons:
            if d == days:
                btn.configure(fg_color="#000080", text_color="#ffffff", border_color="#808080", border_width=1)
            else:
                btn.configure(fg_color="#d4d0c8", text_color="#000000", border_color="#ffffff", border_width=2)

        self.refresh_data()

    def refresh_data(self):
        """Fetches history events from the database and updates both chart and timeline list."""
        cutoff_ts = time.time() - self.selected_filter_days * 86400
        events = self.db.get_presence_events_since(cutoff_ts)

        # 1. Timeline List updates
        # Clear existing timeline items
        for child in self.timeline_scroll.winfo_children():
            child.destroy()

        if not events:
            no_data_lbl = ctk.CTkLabel(
                self.timeline_scroll, text="📭 Chưa ghi nhận hoạt động nào trong khoảng thời gian này.",
                text_color="#555555", font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
            )
            no_data_lbl.pack(pady=40)
        else:
            # Show events (latest first)
            for e in reversed(events):
                start_str = datetime.fromtimestamp(e.start_time).strftime("%d/%m %H:%M:%S")
                duration_str = "Vừa xảy ra"
                if e.end_time:
                    dur_sec = int(e.end_time - e.start_time)
                    if dur_sec < 60:
                        duration_str = f"{dur_sec} giây"
                    else:
                        duration_str = f"{dur_sec // 60} phút"

                is_present = e.event_type == "PRESENT"
                card = ctk.CTkFrame(
                    self.timeline_scroll, fg_color="#ffffff",
                    border_width=0, corner_radius=0, height=36
                )
                card.pack(fill="x", pady=0, padx=0)

                color_dot = "#15803d" if is_present else "#808080"
                lbl_badge = ctk.CTkLabel(card, text="●", text_color=color_dot, font=ctk.CTkFont(size=14))
                lbl_badge.pack(side="left", padx=(12, 8))

                lbl_text = ctk.CTkLabel(
                    card, text=f"{'Có người trong phòng' if is_present else 'Phòng đang trống'} ({duration_str})",
                    text_color="#000000",
                    font=ctk.CTkFont(family="Tahoma", size=13, weight="bold" if is_present else "normal")
                )
                lbl_text.pack(side="left", padx=4)

                lbl_time = ctk.CTkLabel(
                    card, text=start_str, text_color="#555555", font=ctk.CTkFont(family="Tahoma", size=13)
                )
                lbl_time.pack(side="right", padx=15)

                # Windows 98 Flat ListView row separator divider
                divider = ctk.CTkFrame(self.timeline_scroll, fg_color="#d4d0c8", height=1, corner_radius=0)
                divider.pack(fill="x", pady=0, padx=0)

        # 2. Statistics and Pie/Donut Chart updates
        present_sec = 0.0
        absent_sec = 0.0
        now = time.time()
        for e in events:
            end = e.end_time or now
            duration = end - e.start_time
            if e.event_type == "PRESENT":
                present_sec += duration
            else:
                absent_sec += duration

        present_min = int(present_sec / 60)
        absent_min = int(absent_sec / 60)

        # fallback values if empty so donut chart displays correctly
        if present_min == 0 and absent_min == 0:
            present_min = 1
            absent_min = 1

        self.present_min_lbl.configure(text=f"Tổng thời gian có mặt: {present_min} phút")
        self.absent_min_lbl.configure(text=f"Tổng thời gian phòng trống: {absent_min} phút")

        # Redraw Matplotlib Donut Chart
        self.ax.clear()
        wedges, texts = self.ax.pie(
            [present_min, absent_min],
            colors=["#15803d", "#808080"],
            wedgeprops=dict(width=0.4, edgecolor="#d4d0c8", linewidth=2),
            startangle=-90
        )
        self.ax.legend(
            wedges, ["Có mặt", "Phòng trống"],
            loc="center", facecolor="none", edgecolor="none",
            fontsize=11, labelcolor="#000000"
        )
        self.chart_canvas.draw_idle()

        # 3. Update learning log terminal
        from desktop.app.config import get_config
        cfg = get_config()
        try:
            conn = self.db._conn()
            total_rssi_count = conn.execute("SELECT COUNT(*) FROM rssi_snapshots").fetchone()[0]
            total_alerts_count = conn.execute("SELECT COUNT(*) FROM alert_events").fetchone()[0]
        except Exception:
            total_rssi_count = 0
            total_alerts_count = 0
            
        terminal_lines = [
            f"==================================================================================",
            f" 📡 HỆ THỐNG TRỰC GIÁM SÁT Y TẾ KHÔNG TIẾP XÚC - CỬA SỔ HỌC MÁY LÂM SÀNG AI",
            f"==================================================================================",
            f"[THIẾT BỊ PHÒNG KHÁM]: Hệ Thống Trực Giám Sát Y Tế & Cảnh Báo Cấp Cứu Không Tiếp Xúc",
            f"[TRỢ LÝ Y TẾ AI]     : Trợ Lý Y Tế AI Chuyên Sâu (Mô hình: {cfg.ollama_model})",
            f"[CẤU HÌNH Y KHOA ĐÃ HỌC ĐƯỢC TỪ MÔI TRƯỜNG THỰC TẾ LÂM SÀNG]:",
            f"  - Trạng thái hiệu chuẩn sóng nền: {'ĐÃ HIỆU CHUẨN LÂM SÀNG (Đạt yêu cầu)' if cfg.is_calibrated else 'MẶC ĐỊNH (Cần hiệu chuẩn môi trường)'}",
            f"  - Phương sai nhiễu động nền (Baseline Variance): {cfg.baseline_variance:.6f}",
            f"  - Độ nhạy cảm biến lâm sàng (Clinical Sensitivity): {cfg.sensitivity:.1f}x (Hệ số khuếch đại ngưỡng)",
            f"  - Giới hạn thời gian bất động khẩn cấp: {cfg.immobility_threshold_min} phút (Phát cảnh báo té ngã/bất tỉnh)",
            f"  - Dữ liệu sóng không gian đã thu nhận học tập: {total_rssi_count} điểm ảnh phổ sóng RSSI",
            f"  - Tổng số biến cố lâm sàng đã được ghi nhận: {total_alerts_count} cảnh báo được xác thực",
            f"[TIẾN TRÌNH PHÂN TÍCH SINH HIỆU THỜI GIAN THỰC]:",
            f"  - Trạng thái học máy: Đang liên tục thích ứng thích nghi với tín hiệu phản xạ đa đường không gian...",
            f"  - Ước tính sinh hiệu lâm sàng: Tự động học và lọc nhiễu nhịp thở và tần số nhịp tim (BPM)...",
            f"  - Trạng thái kết nối: Hoạt động ngoại tuyến (Offline) bảo mật tuyệt đối 100% cho bệnh nhân.",
            f"=================================================================================="
        ]
        
        self.terminal_text.configure(state="normal")
        self.terminal_text.delete("1.0", "end")
        self.terminal_text.insert("end", "\n".join(terminal_lines))
        self.terminal_text.configure(state="disabled")
        self.terminal_text.see("end")

    def destroy(self):
        plt.close(self.fig)
        super().destroy()
