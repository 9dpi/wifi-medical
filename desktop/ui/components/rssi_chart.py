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
rssi_chart.py — Real-time embedded Matplotlib chart component.
Renders RSSI and Variance side-by-side with a premium dark-mode aesthetic.
"""

import time
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime


class RssiChart(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#d4d0c8", border_color="#ffffff", border_width=2, corner_radius=0, **kwargs)

        # Title Bar
        title_bar = ctk.CTkFrame(self, fg_color="#000080", height=24, corner_radius=0)
        title_bar.pack(fill="x", padx=2, pady=2)
        
        self.title_lbl = ctk.CTkLabel(
            title_bar, text="📈 BIỂU ĐỒ RSSI & ĐỘ BIẾN ĐỘNG SÓNG REAL-TIME", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.title_lbl.pack(anchor="w", padx=6, pady=2)

        # 3D Inset Bevel Frame for Matplotlib chart
        chart_inset = ctk.CTkFrame(
            self, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        chart_inset.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # Matplotlib Figure Setup (Classic System Monitor style: white bg, dark grid)
        self.fig, self.ax = plt.subplots(figsize=(6, 2.5), facecolor="#ffffff")
        self.ax.set_facecolor("#ffffff")

        # Setup secondary y-axis for variance
        self.ax2 = self.ax.twinx()
        self.ax2.set_facecolor("#ffffff")

        # Style Spines
        for ax_obj in [self.ax, self.ax2]:
            ax_obj.spines["top"].set_color("none")
            ax_obj.spines["bottom"].set_color("#808080")
            ax_obj.spines["left"].set_color("#808080")
            ax_obj.spines["right"].set_color("#808080")
            ax_obj.tick_params(colors="#000000", labelsize=9)

        # Configure Grid (Retro look)
        self.ax.grid(True, color="#d4d0c8", linestyle="-", linewidth=0.7)

        # X-axis time formatting
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        self.fig.autofmt_xdate(rotation=15, ha="right")

        # Set labels with classic high contrast
        self.ax.set_ylabel("RSSI (dBm)", color="#0000ff", fontsize=10, fontweight="bold")
        self.ax2.set_ylabel("Độ biến động (Variance)", color="#ff0000", fontsize=10, fontweight="bold")

        # Pack into Tkinter Frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_inset)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=2, pady=2)

        # Initial Plot Lines
        self.rssi_line, = self.ax.plot([], [], color="#0000ff", linewidth=2.0, label="RSSI")
        self.var_line, = self.ax2.plot([], [], color="#ff0000", linewidth=1.5, linestyle="--", label="Variance")

        # Add clean legends inside the frame
        lines = [self.rssi_line, self.var_line]
        labels = [l.get_label() for l in lines]
        self.ax.legend(lines, labels, loc="upper left", facecolor="#ffffff", edgecolor="#808080", fontsize=9, labelcolor="#000000")

        # Make sure layout is perfect
        self.fig.tight_layout()

    def update_chart(self, timestamps: list[float], rssi_vals: list[int], variance_vals: list[float]):
        """Updates the chart lines with new real-time values."""
        if not timestamps:
            return

        # Convert epoch timestamps to datetime objects
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]

        # Update data series
        self.rssi_line.set_data(dates, rssi_vals)
        self.var_line.set_data(dates, variance_vals)

        # Adjust X limits
        self.ax.set_xlim(dates[0], dates[-1])

        # Adjust Y limits (RSSI typically -100 to -30 dBm)
        min_r, max_r = min(rssi_vals), max(rssi_vals)
        self.ax.set_ylim(min(min_r - 5, -95), max(max_r + 5, -45))

        # Adjust Y limits (Variance >= 0)
        max_v = max(variance_vals) if variance_vals else 1.0
        self.ax2.set_ylim(-0.2, max(max_v * 1.2, 5.0))

        # Redraw
        try:
            self.ax.relim()
            self.ax2.relim()
            self.canvas.draw_idle()
        except Exception as e:
            print(f"[Chart] Draw error: {e}")

    def destroy(self):
        # Prevent memory leaks
        plt.close(self.fig)
        super().destroy()
