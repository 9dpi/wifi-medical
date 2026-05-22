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
alert_banner.py — Banner component for active alerts (fall, immobility).
Flashes red/orange with a clean, urgent layout and an 'Acknowledge' action button.
"""

import customtkinter as ctk
from typing import Callable, Optional


class AlertBanner(ctk.CTkFrame):
    def __init__(self, parent, on_acknowledge: Optional[Callable[[], None]] = None, **kwargs):
        # Default styling
        super().__init__(parent, fg_color="#7f1d1d", border_color="#f87171", border_width=1.5, corner_radius=10, **kwargs)

        self.on_acknowledge = on_acknowledge
        self.alert_id: Optional[int] = None

        # Content Layout
        # Alert Icon
        self.icon_lbl = ctk.CTkLabel(
            self, text="🔴", font=ctk.CTkFont(size=24)
        )
        self.icon_lbl.pack(side="left", padx=(15, 10), pady=10)

        # Message Container
        self.msg_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.msg_frame.pack(side="left", fill="both", expand=True, pady=10)

        # Alert Title
        self.title_lbl = ctk.CTkLabel(
            self.msg_frame, text="NGHI NGỜ TÉ NGÃ KHẨN CẤP", text_color="#fecaca",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"), anchor="w"
        )
        self.title_lbl.pack(fill="x", anchor="w", pady=(2, 2))

        # Alert Description
        self.desc_lbl = ctk.CTkLabel(
            self.msg_frame, text="Tín hiệu biến mất đột ngột. Vui lòng kiểm tra phòng ngay lập tức!",
            text_color="#fca5a5", font=ctk.CTkFont(family="Inter", size=15, weight="bold"), anchor="w"
        )
        self.desc_lbl.pack(fill="x", anchor="w", pady=(2, 2))

        # Action Button (Acknowledge)
        self.ack_btn = ctk.CTkButton(
            self, text="Xác nhận", fg_color="#ef4444", hover_color="#dc2626",
            text_color="#ffffff", font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            width=130, height=40, corner_radius=8, command=self._handle_ack
        )
        self.ack_btn.pack(side="right", padx=15, pady=10)

        # Hide initially
        self.pack_forget()

    def show_alert(self, alert_id: int, alert_type: str, title: str, message: str):
        """Displays the banner with appropriate severity styles."""
        self.alert_id = alert_id

        # Format layout based on type
        if alert_type == "FALL":
            # High severity (Danger Red)
            self.configure(fg_color="#7f1d1d", border_color="#f87171")
            self.icon_lbl.configure(text="🔴")
            self.title_lbl.configure(text=title.upper(), text_color="#fecaca")
            self.desc_lbl.configure(text=message, text_color="#fca5a5")
            self.ack_btn.configure(fg_color="#ef4444", hover_color="#dc2626")
        else:
            # Medium severity (Warning Orange)
            self.configure(fg_color="#78350f", border_color="#fbbf24")
            self.icon_lbl.configure(text="⚠️")
            self.title_lbl.configure(text=title.upper(), text_color="#fef3c7")
            self.desc_lbl.configure(text=message, text_color="#fde047")
            self.ack_btn.configure(fg_color="#d97706", hover_color="#b45309")

        # Force pack placement
        self.pack(fill="x", padx=15, pady=(10, 5), before=self.master.winfo_children()[0] if self.master.winfo_children() else None)

    def hide(self):
        self.pack_forget()
        self.alert_id = None

    def _handle_ack(self):
        if self.on_acknowledge and self.alert_id is not None:
            self.on_acknowledge()
        self.hide()
