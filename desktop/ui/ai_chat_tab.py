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
ai_chat_tab.py — Tab Trợ lý AI mang phong cách Yahoo! Messenger cổ điển & Windows 98 Retro.

Đặc trưng Retro:
  - Góc vuông 100% (corner_radius = 0).
  - Viền bevel 3D nổi/thụt (xám sáng #d4d0c8, viền sáng #ffffff, viền tối #808080).
  - Font Tahoma chuẩn cổ điển Windows 98.
  - Tái hiện khung chat Yahoo Messenger cổ điển với text tags (không dùng bong bóng).
  - Tính năng 💥 BUZZ! rung lắc màn hình và beep hệ thống vô cùng chân thực!
"""

import time
import threading
import re
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import customtkinter as ctk

if TYPE_CHECKING:
    from desktop.app.ai.agent import WifiCensorAgent
    from desktop.app.ai.report_generator import ReportGenerator
    from desktop.app.ai.ollama_manager import OllamaManager


# Retro styling constants
COLOR_WIN_BG    = "#d4d0c8"  # Màu xám Windows 98 cổ điển
COLOR_TEXT_DARK = "#000000"
COLOR_TITLE_BG  = "#000080"  # Màu xanh lam đậm cho thanh active title bar
COLOR_TITLE_TXT = "#ffffff"
COLOR_TEXT_BG   = "#ffffff"  # Nền trắng cho các hộp nhập liệu/hiển thị chat
COLOR_BORDER    = "#808080"  # Màu xám đậm cho viền 3D shadow

# Yahoo Messenger Color constants
COLOR_USER_HEADER = "#0000ff"  # Xanh dương - Tên user
COLOR_AI_HEADER   = "#ff0000"  # Đỏ - Tên AI
COLOR_SYS_ALERT   = "#800080"  # Tím - Báo động khẩn cấp
COLOR_TIME_TXT    = "#555555"  # Xám vừa - Timestamp

# Quick prompts retro styled
QUICK_PROMPTS = [
    "📊 Tình trạng hôm nay?",
    "💓 Nhịp tim 1 giờ qua?",
    "⚠️ Có cảnh báo nào không?",
    "📈 Xu hướng hoạt động tuần này?",
    "📋 Xuất báo cáo ngay",
]


class AIChatTab(ctk.CTkFrame):
    """
    Tab Trợ lý AI mang phong cách giao diện Yahoo! Messenger & Windows 98.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLOR_WIN_BG, corner_radius=0, **kwargs)
        self._agent: Optional["WifiCensorAgent"] = None
        self._report_gen: Optional["ReportGenerator"] = None
        self._ollama: Optional["OllamaManager"] = None
        self._is_ai_responding = False
        self._is_first_chunk = True

        self._build_ui()
        self._start_status_checker()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Khung chat chiếm hầu hết khoảng trống

        # 1. Windows 98 Title Bar giả lập
        self._build_title_bar()

        # 2. Yahoo Menu Bar
        self._build_menu_bar()

        # 3. Yahoo Chat History Area (Khung chat chính)
        self._build_chat_area()

        # 4. Toolbar (Định dạng & BUZZ!)
        self._build_toolbar()

        # 5. Input Area & Send Button (Bố cục Yahoo Messenger)
        self._build_input_area()

        # 6. Quick Prompts Bar
        self._build_quick_prompts()

    def _build_title_bar(self):
        """Giả lập Active Title Bar của Windows 98."""
        title_bar = ctk.CTkFrame(self, fg_color=COLOR_TITLE_BG, height=28, corner_radius=0)
        title_bar.grid(row=0, column=0, sticky="ew", padx=3, pady=(3, 0))
        title_bar.grid_columnconfigure(1, weight=1)
        title_bar.pack_propagate(False)

        # Icon & Title Text
        lbl_title = ctk.CTkLabel(
            title_bar,
            text="💬 Trợ Lý Y Tế AI - Instant Message",
            text_color=COLOR_TITLE_TXT,
            font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")
        )
        lbl_title.pack(side="left", padx=8, pady=3)

        # Min / Max / Close Classic buttons
        btn_close = ctk.CTkButton(
            title_bar, text="✕", width=18, height=18,
            fg_color=COLOR_WIN_BG, hover_color="#e6e6e6",
            text_color=COLOR_TEXT_DARK, corner_radius=0,
            border_width=1, border_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=12, weight="bold"),
            command=self._on_clear_chat
        )
        btn_close.pack(side="right", padx=4, pady=3)

        # AI Status Badge (giả lập status)
        self._status_badge = ctk.CTkLabel(
            title_bar,
            text=" gemma4:e4b (Online) ",
            text_color="#10b981",
            font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")
        )
        self._status_badge.pack(side="right", padx=10)

    def _build_menu_bar(self):
        """Thanh trình đơn Yahoo Messenger cổ điển."""
        menu_bar = ctk.CTkFrame(self, fg_color=COLOR_WIN_BG, height=22, corner_radius=0,
                                border_width=1, border_color="#ffffff")
        menu_bar.grid(row=1, column=0, sticky="ew", padx=3, pady=(0, 2))
        menu_bar.pack_propagate(False)

        menus = ["Messenger", "Actions", "Tools", "Help"]
        for m in menus:
            btn = ctk.CTkButton(
                menu_bar, text=m, fg_color="transparent", hover_color="#e6e6e6",
                text_color=COLOR_TEXT_DARK, width=60, height=18, corner_radius=0,
                font=ctk.CTkFont(family="Tahoma", size=12)
            )
            btn.pack(side="left", padx=4, pady=2)

    def _build_chat_area(self):
        """Khung hiển thị lịch sử chat màu trắng, dùng CTkTextbox retro."""
        chat_container = ctk.CTkFrame(
            self, fg_color=COLOR_WIN_BG, corner_radius=0,
            border_width=2, border_color=COLOR_BORDER
        )
        chat_container.grid(row=2, column=0, sticky="nsew", padx=6, pady=4)
        chat_container.grid_columnconfigure(0, weight=1)
        chat_container.grid_rowconfigure(0, weight=1)
        chat_container.grid_rowconfigure(1, weight=0)

        # Sử dụng một CTkTextbox lớn duy nhất để hiển thị RichText retro
        self._chat_history = ctk.CTkTextbox(
            chat_container,
            fg_color=COLOR_TEXT_BG,
            text_color=COLOR_TEXT_DARK,
            font=ctk.CTkFont(family="Tahoma", size=15),
            corner_radius=0,
            wrap="word",
            activate_scrollbars=True
        )
        self._chat_history.grid(row=0, column=0, sticky="nsew", padx=2, pady=(2, 0))

        # Yahoo! status bar showing AI thinking / typing states
        self._status_label = ctk.CTkLabel(
            chat_container,
            text="",
            text_color="#808080",
            fg_color=COLOR_TEXT_BG,
            font=ctk.CTkFont(family="Tahoma", size=12, slant="italic"),
            anchor="w",
            justify="left"
        )
        self._status_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))
        
        # Cấu hình text tags cho định dạng phong cách Yahoo Messenger
        self._setup_text_tags()

        # Welcome message
        self._chat_history.configure(state="normal")
        self._insert_timestamp()
        self._chat_history.insert("end", " Trợ Lý Y Tế AI", "ai_header")
        self._chat_history.insert("end", ": Chào bạn! Tôi là Trợ lý Y tế AI chuyên sâu của hệ thống.\n", "message")
        self._chat_history.insert("end", "Tôi chạy hoàn toàn ngoại tuyến (offline) trên máy tính của bạn và giúp:\n", "message")
        self._chat_history.insert("end", " • Giám sát lâm sàng & phân tích sinh hiệu liên tục (Nhịp tim, Tần số hô hấp).\n", "message")
        self._chat_history.insert("end", " • Xác thực biến cố té ngã cấp cứu thông minh (giảm thiểu cảnh báo giả).\n", "message")
        self._chat_history.insert("end", " • Biên soạn Báo cáo Sức khỏe Y khoa tổng hợp cuối ngày.\n\n", "message")
        self._chat_history.configure(state="disabled")

    def _setup_text_tags(self):
        """Định nghĩa các thẻ màu và định dạng font chữ của Tkinter Text."""
        text_widget = self._chat_history._textbox
        text_widget.tag_config("user_header", foreground=COLOR_USER_HEADER, font=("Tahoma", 16, "bold"))
        text_widget.tag_config("ai_header", foreground=COLOR_AI_HEADER, font=("Tahoma", 16, "bold"))
        text_widget.tag_config("sys_header", foreground=COLOR_SYS_ALERT, font=("Tahoma", 16, "bold"))
        text_widget.tag_config("timestamp", foreground=COLOR_TIME_TXT, font=("Tahoma", 12))
        text_widget.tag_config("message", foreground=COLOR_TEXT_DARK, font=("Tahoma", 15))
        text_widget.tag_config("buzz_alert", foreground="#ff0000", font=("Tahoma", 16, "bold"))
        text_widget.tag_config("sys_msg", foreground="#475569", font=("Tahoma", 14, "italic"))

    def _build_toolbar(self):
        """Thanh công cụ chứa nút BUZZ! thần thánh và các nút định dạng."""
        toolbar = ctk.CTkFrame(
            self, fg_color=COLOR_WIN_BG, height=28, corner_radius=0,
            border_width=1, border_color="#ffffff"
        )
        toolbar.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 2))
        toolbar.pack_propagate(False)

        # CTkButtons nhỏ vuông vức
        btn_fonts = ctk.CTkButton(
            toolbar, text="Font", fg_color=COLOR_WIN_BG, hover_color="#e6e6e6",
            text_color=COLOR_TEXT_DARK, width=40, height=20, corner_radius=0,
            border_width=1, border_color=COLOR_BORDER,
            font=ctk.CTkFont(family="Tahoma", size=11)
        )
        btn_fonts.pack(side="left", padx=4, pady=3)

        btn_emoticons = ctk.CTkButton(
            toolbar, text="😊 Smiles", fg_color=COLOR_WIN_BG, hover_color="#e6e6e6",
            text_color=COLOR_TEXT_DARK, width=55, height=20, corner_radius=0,
            border_width=1, border_color=COLOR_BORDER,
            font=ctk.CTkFont(family="Tahoma", size=11)
        )
        btn_emoticons.pack(side="left", padx=4, pady=3)

        # 💥 NÚT BUZZ! ĐỎ CHÓI HUYỀN THOẠI
        btn_buzz = ctk.CTkButton(
            toolbar, text="💥 BUZZ!", fg_color="#ef4444", hover_color="#dc2626",
            text_color="#ffffff", width=65, height=22, corner_radius=0,
            border_width=1, border_color="#7f1d1d",
            font=ctk.CTkFont(family="Tahoma", size=11, weight="bold"),
            command=self._on_buzz_click
        )
        btn_buzz.pack(side="right", padx=10, pady=3)

    def _build_input_area(self):
        """Bố cục hộp nhập text bên trái, nút Send cổ điển bên phải."""
        input_container = ctk.CTkFrame(self, fg_color="transparent", height=70, corner_radius=0)
        input_container.grid(row=4, column=0, sticky="ew", padx=6, pady=2)
        input_container.grid_columnconfigure(0, weight=1)
        input_container.pack_propagate(False)

        # Hộp nhập liệu (CTkTextbox màu trắng vuông vức)
        self._input_text = ctk.CTkTextbox(
            input_container,
            fg_color=COLOR_TEXT_BG,
            text_color=COLOR_TEXT_DARK,
            font=ctk.CTkFont(family="Tahoma", size=15),
            corner_radius=0,
            border_width=2, border_color=COLOR_BORDER
        )
        self._input_text.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=2)
        
        # Bắt phím Return
        self._input_text.bind("<Return>", self._on_return_pressed)
        
        # Nút SEND to lớn màu xám, viền 3D Bevel nổi
        self._send_btn = ctk.CTkButton(
            input_container,
            text="Send",
            width=80,
            fg_color=COLOR_WIN_BG,
            hover_color="#e6e6e6",
            text_color=COLOR_TEXT_DARK,
            corner_radius=0,
            border_width=2,
            border_color=COLOR_BORDER,
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold"),
            command=self._on_send
        )
        self._send_btn.grid(row=0, column=1, sticky="nsew", pady=2)

    def _build_quick_prompts(self):
        """Quick prompts ở dưới cùng theo phong cách retro."""
        quick_frame = ctk.CTkFrame(self, fg_color="transparent", height=32, corner_radius=0)
        quick_frame.grid(row=5, column=0, sticky="ew", padx=6, pady=(2, 6))
        quick_frame.pack_propagate(False)

        ctk.CTkLabel(
            quick_frame, text="Quick Prompts:",
            text_color=COLOR_TEXT_DARK,
            font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")
        ).pack(side="left", padx=(4, 8))

        for q in QUICK_PROMPTS:
            btn = ctk.CTkButton(
                quick_frame, text=q,
                fg_color=COLOR_WIN_BG, hover_color="#e6e6e6",
                text_color=COLOR_TEXT_DARK, height=22, corner_radius=0,
                border_width=1, border_color=COLOR_BORDER,
                font=ctk.CTkFont(family="Tahoma", size=11),
                command=lambda prompt=q: self._on_quick_prompt(prompt)
            )
            btn.pack(side="left", padx=3)

    # ── Text Appending & Format Helpers ───────────────────────────────────────

    def _insert_timestamp(self):
        """Chèn timestamp theo chuẩn Yahoo: (1:24:52 AM)"""
        now = datetime.now()
        # Định dạng: hh:mm:ss AM/PM
        time_str = now.strftime("%I:%M:%S %p").lstrip('0')
        self._chat_history.insert("end", f"({time_str})", "timestamp")

    def _scroll_to_bottom(self):
        self._chat_history.see("end")

    # ── Public API (gọi từ app_window.py) ────────────────────────────────────

    def set_agent(self, agent: "WifiCensorAgent") -> None:
        self._agent = agent

    def set_report_generator(self, report_gen: "ReportGenerator") -> None:
        self._report_gen = report_gen

    def set_ollama(self, ollama: "OllamaManager") -> None:
        self._ollama = ollama

    def on_system_alert(self, alert_type: str, title: str, message: str) -> None:
        """Kích hoạt BUZZ! và comment tự động từ AI khi có sự cố khẩn cấp."""
        # Rung màn hình nếu có cảnh báo té ngã (FALL)
        if alert_type == "FALL":
            self.after(200, self.trigger_buzz)

        if not self._agent or self._is_ai_responding:
            return

        event_msg = f"[Sự cố hệ thống] Vừa kích hoạt báo động {title} — {message}. Đưa ra ý kiến phân tích sinh học và giải thích."
        self._send_message(event_msg, is_system_event=True)

    # ── 💥 TÍNH NĂNG BUZZ! RUNG MÀN HÌNH RETRO 💥 ─────────────────────────────

    def trigger_buzz(self):
        """Rung cửa sổ toplevel và phát âm thanh hệ thống Beep."""
        toplevel = self.winfo_toplevel()
        if not toplevel:
            return

        # 1. Phát âm thanh Beep hệ thống cực retro
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            toplevel.bell()

        # 2. Thêm thông báo BUZZ! vào khung chat
        self._chat_history.configure(state="normal")
        self._insert_timestamp()
        self._chat_history.insert("end", " Hệ thống", "sys_header")
        self._chat_history.insert("end", ": 💥 ĐÃ GỬI MỘT BUZZ!\n\n", "buzz_alert")
        self._chat_history.configure(state="disabled")
        self._scroll_to_bottom()

        # 3. Rung cửa sổ cơ học
        orig_geom = toplevel.geometry()
        match = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", orig_geom)
        
        if match:
            w, h, x, y = map(int, match.groups())
        else:
            w, h = toplevel.winfo_width(), toplevel.winfo_height()
            x, y = toplevel.winfo_x(), toplevel.winfo_y()

        # Xê dịch vị trí x, y để rung lắc cửa sổ
        offsets = [
            (10, 10), (-10, -10), (12, -8), (-8, 12),
            (6, 6), (-6, -6), (6, -6), (-6, 6),
            (2, 2), (-2, -2), (0, 0)
        ]

        def shake(step=0):
            if step < len(offsets):
                dx, dy = offsets[step]
                toplevel.geometry(f"{w}x{h}+{x + dx}+{y + dy}")
                self.after(40, lambda: shake(step + 1))
            else:
                toplevel.geometry(f"{w}x{h}+{x}+{y}")

        shake()

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _on_buzz_click(self):
        """Người dùng bấm nút BUZZ!."""
        if self._is_ai_responding:
            return
        self.trigger_buzz()

    def _on_return_pressed(self, event):
        """Bắt phím Return, gửi tin và không chèn dòng mới."""
        self.after(10, self._on_send)
        return "break"

    def _on_send(self):
        text = self._input_text.get("1.0", "end-1c").strip()
        if not text or self._is_ai_responding:
            return
        self._input_text.delete("1.0", "end")
        self._send_message(text)

    def _on_quick_prompt(self, prompt: str):
        # Bỏ emoji prefix khi gửi AI
        clean = prompt.split(" ", 1)[1] if " " in prompt else prompt
        self._send_message(clean)

    def _on_clear_chat(self):
        self._chat_history.configure(state="normal")
        self._chat_history.delete("1.0", "end")
        self._insert_timestamp()
        self._chat_history.insert("end", " Trợ Lý Y Tế AI", "ai_header")
        self._chat_history.insert("end", ": Lịch sử hội thoại lâm sàng đã được làm mới thành công! 🔄\n\n", "message")
        self._chat_history.configure(state="disabled")
        if self._agent:
            self._agent.reset_history()

    # ── Core Message Sending & Streaming Logic ───────────────────────────────

    def _send_message(self, text: str, is_system_event: bool = False) -> None:
        if self._agent is None:
            if not is_system_event:
                self._add_user_message_to_history(text)
            self._add_system_message_to_history(
                "Trợ lý AI đang Offline. Vui lòng đảm bảo Ollama đang hoạt động và model gemma4:e4b đã được tải."
            )
            return

        if self._is_ai_responding:
            return

        self._is_ai_responding = True
        self._is_first_chunk = True

        # Ghi nhận tin nhắn người dùng vào chat box
        if not is_system_event:
            self._add_user_message_to_history(text)

        # Khóa nút & hiển thị status suy nghĩ
        self._send_btn.configure(state="disabled", text="Typing...")
        self._status_label.configure(text="💬 Trợ Lý Y Tế AI đang phân tích dữ liệu...")
        
        def _on_token(token: str) -> None:
            self.after(0, lambda t=token: self._append_ai_chunk(t))

        def _on_done(full_text: str) -> None:
            self.after(0, self._finalize_ai_stream)

        def _on_error(err: str) -> None:
            self.after(0, lambda e=err: self._add_system_message_to_history(f"Lỗi: {e}"))
            self.after(0, self._finalize_ai_stream)

        # Chạy ReAct Agent
        self._agent.chat_async(
            user_message=text,
            on_token=_on_token,
            on_done=_on_done,
            on_error=_on_error
        )

    def _add_user_message_to_history(self, text: str):
        self._chat_history.configure(state="normal")
        self._insert_timestamp()
        
        # Format user username theo kiểu Yahoo Messenger
        username = " cuong_vq199x"
        self._chat_history.insert("end", username, "user_header")
        self._chat_history.insert("end", f": {text}\n\n", "message")
        self._chat_history.configure(state="disabled")
        self._scroll_to_bottom()

    def _add_system_message_to_history(self, text: str):
        self._chat_history.configure(state="normal")
        self._insert_timestamp()
        self._chat_history.insert("end", " Hệ thống", "sys_header")
        self._chat_history.insert("end", f": {text}\n\n", "sys_msg")
        self._chat_history.configure(state="disabled")
        self._scroll_to_bottom()

    def _append_ai_chunk(self, token: str):
        """Append từng token AI đang stream vào box history chat."""
        self._chat_history.configure(state="normal")
        
        if self._is_first_chunk:
            self._is_first_chunk = False
            self._insert_timestamp()
            self._chat_history.insert("end", " Trợ Lý Y Tế AI", "ai_header")
            self._chat_history.insert("end", ": ", "message")
            
        self._chat_history.insert("end", token, "message")
        self._chat_history.configure(state="disabled")
        self._status_label.configure(text="⚡ Trợ Lý Y Tế AI đang phản hồi chẩn đoán...")
        self._scroll_to_bottom()

    def _finalize_ai_stream(self):
        """Stream kết thúc — mở lại input."""
        self._chat_history.configure(state="normal")
        self._chat_history.insert("end", "\n\n", "message")
        self._chat_history.configure(state="disabled")
        
        self._is_ai_responding = False
        self._send_btn.configure(state="normal", text="Send")
        self._status_label.configure(text="")
        self._scroll_to_bottom()

    # ── Status Checker ────────────────────────────────────────────────────────

    def _start_status_checker(self) -> None:
        def _check():
            while True:
                try:
                    if self._ollama:
                        status = self._ollama.get_status_text()
                        is_online = "Online" in status
                        badge_txt = f" gemma4:e4b ({'Online' if is_online else 'Offline'}) "
                        badge_color = "#10b981" if is_online else "#ef4444"
                        self.after(0, lambda t=badge_txt, c=badge_color: self._status_badge.configure(
                            text=t, text_color=c
                        ))
                except Exception:
                    pass
                time.sleep(30)

        thread = threading.Thread(target=_check, daemon=True)
        thread.start()
