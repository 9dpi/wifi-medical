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
history_tab.py — Historical Reports & Event Timeline tab.
Provides a deep retrospective view of presence ratios via matplotlib donut charts and logs.
"""

import time
from datetime import datetime, timedelta
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from desktop.app.database import Database


class HistoryTab(ctk.CTkFrame):
    def __init__(self, parent, db: Database, **kwargs):
        super().__init__(parent, fg_color="#050810", **kwargs)

        self.db = db
        self.selected_filter_days = 1 # 1: 24h, 7: 7 days, 30: 30 days

        # Grid config
        self.grid_columnconfigure(0, weight=1, minsize=400) # Chart & aggregates
        self.grid_columnconfigure(1, weight=1, minsize=400) # Timeline log
        self.grid_rowconfigure(1, weight=1)

        # ── Top Bar: Filter Actions ───────────────────────────────────────────
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="ew")

        self.tab_title = ctk.CTkLabel(
            self.top_bar, text="⏱️ NHẬT KÝ SỰ KIỆN & LỊCH SỬ", text_color="#f8fafc",
            font=ctk.CTkFont(family="Inter", size=22, weight="bold")
        )
        self.tab_title.pack(side="left")

        # Filters buttons container (Larger and highly clickable buttons)
        self.filters_frame = ctk.CTkFrame(self.top_bar, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=8)
        self.filters_frame.pack(side="right")

        self.btn_24h = ctk.CTkButton(
            self.filters_frame, text="24 Giờ Qua", fg_color="#6366f1", text_color="#ffffff",
            width=100, height=34, corner_radius=6, font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            command=lambda: self.set_filter(1)
        )
        self.btn_24h.pack(side="left", padx=3, pady=3)

        self.btn_7d = ctk.CTkButton(
            self.filters_frame, text="7 Ngày Qua", fg_color="transparent", text_color="#cbd5e1",
            hover_color="#1e293b", width=100, height=34, corner_radius=6, font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            command=lambda: self.set_filter(7)
        )
        self.btn_7d.pack(side="left", padx=3, pady=3)

        self.btn_30d = ctk.CTkButton(
            self.filters_frame, text="30 Ngày Qua", fg_color="transparent", text_color="#cbd5e1",
            hover_color="#1e293b", width=100, height=34, corner_radius=6, font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            command=lambda: self.set_filter(30)
        )
        self.btn_30d.pack(side="left", padx=3, pady=3)

        # ── Left Column: Analytics & Pie Chart ────────────────────────────────
        self.left_col = ctk.CTkFrame(self, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12)
        self.left_col.grid(row=1, column=0, padx=(20, 10), pady=(10, 20), sticky="nsew")

        self.stats_title = ctk.CTkLabel(
            self.left_col, text="📊 TỶ LỆ CÓ MẶT TRONG PHÒNG", text_color="#f8fafc",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold")
        )
        self.stats_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Embedded Donut Chart (Enhanced size for legibility)
        self.fig, self.ax = plt.subplots(figsize=(3.5, 3.5), facecolor="#0d1117")
        self.ax.set_facecolor("#0d1117")
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.left_col)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=5)

        # Stats info text (Larger high-contrast fonts)
        self.aggregates_frame = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.aggregates_frame.pack(fill="x", padx=20, pady=(5, 15))

        self.present_min_lbl = ctk.CTkLabel(self.aggregates_frame, text="Tổng thời gian có mặt: -- phút", text_color="#10b981", font=ctk.CTkFont(family="Inter", size=15, weight="bold"))
        self.present_min_lbl.pack(pady=4)
        self.absent_min_lbl = ctk.CTkLabel(self.aggregates_frame, text="Tổng thời gian phòng trống: -- phút", text_color="#cbd5e1", font=ctk.CTkFont(family="Inter", size=15, weight="bold"))
        self.absent_min_lbl.pack(pady=4)

        # ── Right Column: Timeline Event List ─────────────────────────────────
        self.right_col = ctk.CTkFrame(self, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12)
        self.right_col.grid(row=1, column=1, padx=(10, 20), pady=(10, 20), sticky="nsew")

        self.timeline_title = ctk.CTkLabel(
            self.right_col, text="🕒 NHẬT KÝ CHI TIẾT SỰ KIỆN", text_color="#f8fafc",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold")
        )
        self.timeline_title.pack(anchor="w", padx=15, pady=(15, 10))

        self.timeline_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        self.timeline_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.refresh_data()

    def set_filter(self, days: int):
        self.selected_filter_days = days

        # Toggle Button aesthetics
        buttons = [(1, self.btn_24h), (7, self.btn_7d), (30, self.btn_30d)]
        for d, btn in buttons:
            if d == days:
                btn.configure(fg_color="#6366f1", text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color="#8892a4")

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
                text_color="#8892a4", font=ctk.CTkFont(family="Inter", size=14, weight="bold")
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
                card = ctk.CTkFrame(self.timeline_scroll, fg_color="#1e293b" if is_present else "#111827", corner_radius=8, height=60)
                card.pack(fill="x", pady=6, padx=5)

                color_dot = "#10b981" if is_present else "#6b7280"
                lbl_badge = ctk.CTkLabel(card, text="●", text_color=color_dot, font=ctk.CTkFont(size=18))
                lbl_badge.pack(side="left", padx=(15, 8))

                lbl_text = ctk.CTkLabel(
                    card, text=f"{'Có người trong phòng' if is_present else 'Phòng đang trống'} (Thời gian: {duration_str})",
                    text_color="#f8fafc" if is_present else "#94a3b8",
                    font=ctk.CTkFont(family="Inter", size=14, weight="bold" if is_present else "normal")
                )
                lbl_text.pack(side="left", padx=5)

                lbl_time = ctk.CTkLabel(
                    card, text=start_str, text_color="#cbd5e1", font=ctk.CTkFont(family="Inter", size=13, weight="bold")
                )
                lbl_time.pack(side="right", padx=15)

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
            colors=["#10b981", "#374151"],
            wedgeprops=dict(width=0.4, edgecolor="#0d1117", linewidth=2),
            startangle=-90
        )
        self.ax.legend(
            wedges, ["Có mặt", "Phòng trống"],
            loc="center", facecolor="none", edgecolor="none",
            fontsize=11, labelcolor="#f8fafc"
        )
        self.chart_canvas.draw_idle()

    def destroy(self):
        plt.close(self.fig)
        super().destroy()
