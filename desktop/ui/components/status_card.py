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
status_card.py — Animated pulse status card component.
Provides a premium visual status representation with smooth canvas-drawn pulses.
"""

import tkinter as tk
import customtkinter as ctk
from desktop.app.presence_engine import PresenceState, ActivityState


def interpolate_color(color_hex_1: str, color_hex_2: str, factor: float) -> str:
    """Interpolates between two hex colors. factor: 0.0 -> color_1, 1.0 -> color_2."""
    try:
        c1 = [int(color_hex_1[i:i+2], 16) for i in (1, 3, 5)]
        c2 = [int(color_hex_2[i:i+2], 16) for i in (1, 3, 5)]
        c = [int(a + (b - a) * factor) for a, b in zip(c1, c2)]
        return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
    except Exception:
        return color_hex_2


class StatusCard(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#0d1117", border_color="#1f2937", border_width=1, corner_radius=12, **kwargs)

        self.state = PresenceState.UNKNOWN
        self.activity = ActivityState.UNKNOWN
        self.confidence = 0.0

        # Colors
        self.BG_COLOR = "#0d1117"
        self.COLORS = {
            "ABSENT": "#4b5563",      # Gray
            "PRESENT_WALK": "#10b981", # Vibrant Green
            "PRESENT_STAT": "#059669", # Muted Green
            "PRESENT_SLEEP": "#6366f1",# Indigo
            "ALERT": "#f59e0b",        # Orange
            "DANGER": "#ef4444",       # Red
            "UNKNOWN": "#06b6d4",      # Cyan
        }

        # UI Setup
        # Title Label
        self.title_lbl = ctk.CTkLabel(
            self, text="TRẠNG THÁI PHÒNG HIỆN TẠI", text_color="#cbd5e1",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold")
        )
        self.title_lbl.pack(pady=(20, 5))

        # Canvas for Pulsing
        self.canvas_size = 140
        self.canvas = tk.Canvas(
            self, width=self.canvas_size, height=self.canvas_size,
            bg=self.BG_COLOR, highlightthickness=0
        )
        self.canvas.pack(pady=10)

        # Status Label (Large display font)
        self.status_lbl = ctk.CTkLabel(
            self, text="Đang Phân Tích...", text_color="#f8fafc",
            font=ctk.CTkFont(family="Inter", size=32, weight="bold")
        )
        self.status_lbl.pack(pady=5)

        # Sub-status Label (Medium display font)
        self.sub_lbl = ctk.CTkLabel(
            self, text="Đang khởi động cảm biến...", text_color="#cbd5e1",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold")
        )
        self.sub_lbl.pack(pady=(0, 20))

        # Pulse animation state
        self.pulse_radius = 20.0
        self.max_radius = 60.0
        self.pulse_speed = 0.8  # radius increment per tick
        self.anim_tick_ms = 40

        # Start animation
        self.animate()

    def _get_current_color(self) -> str:
        if self.state == PresenceState.ABSENT:
            return self.COLORS["ABSENT"]
        elif self.state == PresenceState.PRESENT:
            if self.activity == ActivityState.WALKING or self.activity == ActivityState.MOVING:
                return self.COLORS["PRESENT_WALK"]
            elif self.activity == ActivityState.SLEEPING:
                return self.COLORS["PRESENT_SLEEP"]
            else:
                return self.COLORS["PRESENT_STAT"]
        elif self.state == PresenceState.UNKNOWN:
            return self.COLORS["UNKNOWN"]
        return self.COLORS["UNKNOWN"]

    def set_state(self, state: PresenceState, activity: ActivityState, confidence: float, is_alert: bool = False, alert_type: str = ""):
        self.state = state
        self.activity = activity
        self.confidence = confidence

        # Text and style updates
        color = self._get_current_color()

        if is_alert:
            if alert_type == "FALL":
                color = self.COLORS["DANGER"]
                self.status_lbl.configure(text="🆘 NGUY HIỂM", text_color=color)
                self.sub_lbl.configure(text="PHÁT HIỆN CẢNH BÁO TÉ NGÃ! KIỂM TRA NGAY!", text_color=color)
            else:
                color = self.COLORS["ALERT"]
                self.status_lbl.configure(text="⚠️ CẢNH BÁO", text_color=color)
                self.sub_lbl.configure(text="Phát hiện bất động quá lâu!", text_color=color)
        else:
            if state == PresenceState.PRESENT:
                self.status_lbl.configure(text="🟢 CÓ NGƯỜI", text_color="#10b981")
                act_str = "🛋️ Đang Nghỉ Ngơi / Ngồi Yên"
                if activity == ActivityState.WALKING:
                    act_str = "🚶 Đang Đi Lại / Vận Động"
                elif activity == ActivityState.MOVING:
                    act_str = "🚶 Đang Hoạt Động Chuyển Động"
                elif activity == ActivityState.SLEEPING:
                    act_str = "😴 Đang Ngủ / Nằm Tĩnh Lặng"
                
                self.sub_lbl.configure(text=f"{act_str} ({int(confidence*100)}% độ tin cậy)", text_color="#cbd5e1")
            elif state == PresenceState.ABSENT:
                self.status_lbl.configure(text="⚪ PHÒNG TRỐNG", text_color="#8892a4")
                self.sub_lbl.configure(text=f"Không phát hiện người ({int(confidence*100)}%)", text_color="#8892a4")
            else:
                # Calibrating
                self.status_lbl.configure(text="📡 ĐANG HIỆU CHỈNH", text_color="#06b6d4")
                self.sub_lbl.configure(text=f"Đang phân tích nhiễu sóng nền ({int(confidence*100)}%)", text_color="#8892a4")

        # Adjust pulse speed based on activity
        if is_alert:
            self.pulse_speed = 1.8  # Rapid red alert pulsing
        elif state == PresenceState.PRESENT:
            if activity == ActivityState.WALKING or activity == ActivityState.MOVING:
                self.pulse_speed = 1.3  # Fast green pulsing
            elif activity == ActivityState.SLEEPING:
                self.pulse_speed = 0.4  # Slow blue sleeping pulse
            else:
                self.pulse_speed = 0.7  # Gentle green pulse
        else:
            self.pulse_speed = 0.5  # Slow gray / cyan pulse

    def animate(self):
        # Draw on Canvas
        self.canvas.delete("all")
        cx = self.canvas_size / 2
        cy = self.canvas_size / 2
        color = self._get_current_color()

        # Update pulse radius
        self.pulse_radius += self.pulse_speed
        if self.pulse_radius > self.max_radius:
            self.pulse_radius = 20.0

        # Calculate fade out factor
        factor = (self.pulse_radius - 20.0) / (self.max_radius - 20.0)
        ring_color = interpolate_color(color, self.BG_COLOR, factor)

        # Draw pulsing outer ring
        r_pulse = self.pulse_radius
        self.canvas.create_oval(
            cx - r_pulse, cy - r_pulse, cx + r_pulse, cy + r_pulse,
            outline=ring_color, width=3
        )

        # Draw a second fainter ring for richer visual effect
        if r_pulse > 30.0:
            r_pulse2 = r_pulse - 12
            factor2 = (r_pulse2 - 20.0) / (self.max_radius - 20.0)
            ring_color2 = interpolate_color(color, self.BG_COLOR, factor2)
            self.canvas.create_oval(
                cx - r_pulse2, cy - r_pulse2, cx + r_pulse2, cy + r_pulse2,
                outline=ring_color2, width=1.5
            )

        # Draw core solid inner circle
        r_inner = 20.0
        self.canvas.create_oval(
            cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
            fill=color, outline=""
        )
        
        # Center glow dot
        self.canvas.create_oval(
            cx - 6, cy - 6, cx + 6, cy + 6,
            fill="#ffffff", outline=""
        )

        # Schedule next tick
        self.after(self.anim_tick_ms, self.animate)
