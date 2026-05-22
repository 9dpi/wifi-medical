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


import customtkinter as ctk

class GuideTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#050810", **kwargs)

        # Layout configure
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Scrollable container for guide content
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        # ── Header Title ──────────────────────────────────────────────────────
        self.header_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(10, 20), padx=5)

        self.title_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="📖 HƯỚNG DẪN SỬ DỤNG AN TOÀN", 
            text_color="#6366f1",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold")
        )
        self.title_lbl.pack(anchor="w")

        self.sub_lbl = ctk.CTkLabel(
            self.header_frame,
            text="Hệ thống giám sát té ngã và sự hiện diện không tiếp xúc qua sóng Wi-Fi dành cho gia đình.",
            text_color="#cbd5e1",
            font=ctk.CTkFont(family="Inter", size=15)
        )
        self.sub_lbl.pack(anchor="w", pady=(5, 0))

        # ── Section 1: How it works ───────────────────────────────────────────
        self.create_section(
            title="1. NGUYÊN LÝ HOẠT ĐỘNG CỦA HỆ THỐNG",
            content=(
                "• Thiết bị sử dụng sóng Wi-Fi từ bộ phát Wi-Fi (Router) trong nhà để giám sát.\n"
                "• Khi có người di chuyển hoặc hô hấp, cơ thể người sẽ làm biến đổi cường độ sóng Wi-Fi (RSSI).\n"
                "• Ứng dụng phân tích độ biến động của sóng (Variance) theo thời gian thực để nhận biết trạng thái:\n"
                "   - CÓ NGƯỜI (Di chuyển, Hoạt động hoặc Đang ngủ/nghỉ).\n"
                "   - VẮNG PHÒNG (Không có ai trong phòng).\n"
                "   - CẢNH BÁO BẤT ĐỘNG (Bất động quá lâu - nghi ngờ đột quỵ hoặc ngất).\n"
                "   - CẢNH BÁO TÉ NGÃ (Sóng biến động cực mạnh đột ngột rồi tắt hẳn - ngã quỵ)."
            ),
            accent_color="#10b981"
        )

        # ── Section 2: Installation ──────────────────────────────────────────
        self.create_section(
            title="2. HƯỚNG DẪN LẮP ĐẶT & BỐ TRÍ THIẾT BỊ",
            content=(
                "• Bước 1: Hãy đặt Laptop hoặc máy tính giám sát tại một góc cao trong phòng (Ví dụ: trên bàn làm việc, kệ tủ).\n"
                "• Bước 2: Hãy đảm bảo khu vực cần bảo vệ nằm ở khoảng giữa Laptop và Bộ phát Wi-Fi (Router).\n"
                "• Bước 3: Khoảng cách tối ưu từ Laptop đến Router là từ 3 đến 8 mét.\n"
                "• Tránh đặt Laptop quá sát tường bê tông dày hoặc ngay cạnh các thiết bị kim loại lớn (như tủ lạnh, lò vi sóng)."
            ),
            accent_color="#6366f1"
        )

        # ── Section 3: Calibration ─────────────────────────────────────────────
        self.create_section(
            title="3. QUY TRÌNH HIỆU CHỈNH PHÒNG TRỐNG (RẤT QUAN TRỌNG)",
            content=(
                "• Để hệ thống nhận diện chính xác nhất, bạn cần thực hiện hiệu chỉnh ban đầu.\n"
                "• Bước thực hiện:\n"
                "   1. Đảm bảo phòng hoàn toàn trống (không có người, không có vật nuôi di chuyển).\n"
                "   2. Truy cập vào mục [Cấu Hình] trên thanh trình đơn bên trái.\n"
                "   3. Nhấp vào nút [Chạy hiệu chỉnh phòng trống (30 giây)].\n"
                "   4. Rời khỏi phòng và đợi 30 giây để hệ thống tự động học và thiết lập mức sóng nền.\n"
                "• Khuyên nghị: Chạy lại hiệu chỉnh nếu bạn thay đổi vị trí của Laptop hoặc Router."
            ),
            accent_color="#06b6d4"
        )

        # ── Section 4: Safety & Support ───────────────────────────────────────
        self.create_section(
            title="4. LƯU Ý AN TOÀN CHO NGƯỜI LỚN TUỔI & GIA ĐÌNH",
            content=(
                "• Thiết bị hoạt động hoàn toàn tự động và không cần camera, bảo vệ tuyệt đối quyền riêng tư.\n"
                "• Luôn cắm sạc Laptop và thiết lập Laptop ở chế độ 'Không ngủ khi gập màn hình' (Never Sleep) để hoạt động liên tục.\n"
                "• Khi có tiếng chuông hú báo động đỏ (🆘 KHẨN CẤP):\n"
                "   - Hãy kiểm tra ngay lập tức phòng của người cao tuổi.\n"
                "   - Nếu đó là báo động nhầm, hãy nhấn nút [ĐÃ XÁC NHẬN] trên màn hình hoặc biểu tượng cảnh báo để tắt chuông.\n"
                "• Số điện thoại hỗ trợ kỹ thuật gia đình: 1900-XXXX (Vui lòng ghi nhớ)."
            ),
            accent_color="#ef4444"
        )

        # ── Section 5: Demo Mode Explanation ──────────────────────────────────
        self.create_section(
            title="5. GIẢI THÍCH VỀ CHẾ ĐỘ MÔ PHỎNG (DEMO)",
            content=(
                "• Nếu góc trên ứng dụng hiển thị 'Chế độ mô phỏng', hệ thống đang tự tạo tín hiệu giả lập do:\n"
                "   1. Máy tính không có card mạng Wi-Fi vật lý hoặc card Wi-Fi đang bị tắt.\n"
                "   2. Quyền vị trí (Location Services) trên Windows 10/11 đang bị tắt. Quyền này là bắt buộc để ứng dụng quét sóng Wi-Fi xung quanh.\n"
                "   3. Ứng dụng chưa được chạy bằng quyền Quản trị viên (Administrator).\n"
                "• Cách khắc phục:\n"
                "   - Bật Wi-Fi và đảm bảo bạn có thể kết nối Internet.\n"
                "   - Vào Cài đặt Windows → Privacy & Security → Location → Bật Location Services cho Windows và cho phép các ứng dụng desktop truy cập.\n"
                "   - Nhấp chuột phải vào biểu tượng ứng dụng (hoặc run_desktop.bat) và chọn 'Run as Administrator' (Chạy dưới quyền quản trị)."
            ),
            accent_color="#f59e0b"
        )

        # ── Section 6: GitHub Sync Guidance ───────────────────────────────────
        self.create_section(
            title="6. HƯỚNG DẪN ĐỒNG BỘ GITHUB & ĐIỀU KHIỂN TỪ XA",
            content=(
                "• Cơ chế đồng bộ không máy chủ (Serverless) giúp bạn giám sát và điều khiển ứng dụng từ xa cực kỳ tiện lợi.\n"
                "• Các bước thiết lập:\n"
                "   1. Tạo một tài khoản GitHub phụ (khuyên dùng tài khoản bot riêng để tăng tính bảo mật) và fork/tạo repository chứa Dashboard.\n"
                "   2. Tạo một Personal Access Token (PAT) trên GitHub chỉ cấp duy nhất quyền ghi nội dung (contents:write) vào repo này.\n"
                "   3. Nhập Token PAT, Tên tài khoản, Tên repo, Nhánh (ví dụ: main) và Định danh thiết bị (ví dụ: desktop) vào tab [Cấu Hình].\n"
                "   4. Bật công tắc [Bật đồng bộ qua GitHub], nhấn [Lưu Cấu Hình] và [Kiểm Tra Kết Nối] để xác nhận kết nối xanh.\n"
                "   5. Mở Web Dashboard trên điện thoại hoặc trình duyệt khác, điền các thông tin y hệt để liên kết. Bạn có thể xem biểu đồ thời gian thực, mức sóng nền, độ nhạy và thực hiện TẮT CÒI BÁO ĐỘNG TỪ XA hoặc YÊU CẦU HIỆU CHỈNH."
            ),
            accent_color="#10b981"
        )

    def create_section(self, title: str, content: str, accent_color: str):
        section_frame = ctk.CTkFrame(
            self.scroll_container, 
            fg_color="#0d1117", 
            border_color="#1f2937", 
            border_width=1, 
            corner_radius=12
        )
        section_frame.pack(fill="x", pady=10, padx=5)

        # Section Indicator Bar
        title_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 10))

        indicator = ctk.CTkLabel(
            title_frame, 
            text="▍", 
            text_color=accent_color, 
            font=ctk.CTkFont(family="Inter", size=20, weight="bold")
        )
        indicator.pack(side="left")

        sec_title = ctk.CTkLabel(
            title_frame, 
            text=title, 
            text_color="#f8fafc", 
            font=ctk.CTkFont(family="Inter", size=17, weight="bold")
        )
        sec_title.pack(side="left", padx=5)

        # Content Text (High readability, larger size, clear line height)
        sec_content = ctk.CTkLabel(
            section_frame, 
            text=content, 
            text_color="#e2e8f0", 
            font=ctk.CTkFont(family="Inter", size=15),
            justify="left", 
            anchor="w",
            wraplength=700
        )
        sec_content.pack(anchor="w", padx=25, pady=(0, 20))
