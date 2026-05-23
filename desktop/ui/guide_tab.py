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
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)

        # Layout configure
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Scrollable container for guide content (looks like standard Help file window)
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        # ── Header Title ──────────────────────────────────────────────────────
        self.header_frame = ctk.CTkFrame(
            self.scroll_container, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.header_frame.pack(fill="x", pady=(5, 10), padx=5)

        title_bar_guide = ctk.CTkFrame(self.header_frame, fg_color="#000080", height=24, corner_radius=0)
        title_bar_guide.pack(fill="x", padx=2, pady=2)

        self.title_lbl = ctk.CTkLabel(
            title_bar_guide, 
            text="📖 HƯỚNG DẪN SỬ DỤNG - WIFI-CENSOR HELP FILE", 
            text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.title_lbl.pack(anchor="w", padx=6, pady=2)

        self.sub_lbl = ctk.CTkLabel(
            self.header_frame,
            text="Hệ thống giám sát té ngã và sinh hiệu phi tiếp xúc qua sóng Wi-Fi dành cho gia đình và phòng khám.",
            text_color="#000000",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        self.sub_lbl.pack(anchor="w", padx=15, pady=(10, 10))
        self.create_section(
            title="1. NGUYÊN LÝ HOẠT ĐỘNG CỦA HỆ THỐNG",
            content=(
                "• Thiết bị sử dụng sóng Wi-Fi từ bộ phát Wi-Fi (Router) trong nhà để giám sát.\n\n"
                "• Khi có người di chuyển hoặc hô hấp, cơ thể người sẽ làm biến đổi cường độ sóng Wi-Fi (RSSI).\n\n"
                "• Ứng dụng phân tích độ biến động của sóng (Variance) theo thời gian thực để nhận biết trạng thái:\n\n"
                "   - CÓ NGƯỜI (Di chuyển, Hoạt động hoặc Đang ngủ/nghỉ).\n\n"
                "   - VẮNG PHÒNG (Không có ai trong phòng).\n\n"
                "   - CẢNH BÁO BẤT ĐỘNG (Bất động quá lâu - nghi ngờ đột quỵ hoặc ngất).\n\n"
                "   - CẢNH BÁO TÉ NGÃ (Sóng biến động cực mạnh đột ngột rồi tắt hẳn - ngã quỵ)."
            ),
            accent_color="#000080"
        )

        # ── Section 2: Installation ──────────────────────────────────────────
        self.create_section(
            title="2. HƯỚNG DẪN LẮP ĐẶT & BỐ TRÍ THIẾT BỊ",
            content=(
                "• Bước 1: Hãy đặt Laptop hoặc máy tính giám sát tại một góc cao trong phòng (Ví dụ: trên bàn làm việc, kệ tủ).\n\n"
                "• Bước 2: Hãy đảm bảo khu vực cần bảo vệ nằm ở khoảng giữa Laptop và Bộ phát Wi-Fi (Router).\n\n"
                "• Bước 3: Khoảng cách tối ưu từ Laptop đến Router là từ 3 đến 8 mét.\n\n"
                "• Tránh đặt Laptop quá sát tường bê tông dày hoặc ngay cạnh các thiết bị kim loại lớn (như tủ lạnh, lò vi sóng)."
            ),
            accent_color="#000080"
        )

        # ── Section 3: Calibration ─────────────────────────────────────────────
        self.create_section(
            title="3. QUY TRÌNH HIỆU CHỈNH PHÒNG TRỐNG (RẤT QUAN TRỌNG)",
            content=(
                "• Để hệ thống nhận diện chính xác nhất, bạn cần thực hiện hiệu chỉnh ban đầu.\n\n"
                "• Bước thực hiện:\n\n"
                "   1. Đảm bảo phòng hoàn toàn trống (không có người, không có vật nuôi di chuyển).\n\n"
                "   2. Truy cập vào mục [Cấu Hình] trên thanh trình đơn bên trái.\n\n"
                "   3. Nhấp vào nút [Chạy hiệu chỉnh phòng trống (30 giây)].\n\n"
                "   4. Rời khỏi phòng và đợi 30 giây để hệ thống tự động học và thiết lập mức sóng nền.\n\n"
                "• Khuyến nghị: Chạy lại hiệu chỉnh nếu bạn thay đổi vị trí của Laptop hoặc Router."
            ),
            accent_color="#000080"
        )

        # ── Section 4: Safety & Support ───────────────────────────────────────
        self.create_section(
            title="4. LƯU Ý AN TOÀN CHO NGƯỜI LỚN TUỔI & GIA ĐÌNH",
            content=(
                "• Thiết bị hoạt động hoàn toàn tự động và không cần camera, bảo vệ tuyệt đối quyền riêng tư.\n\n"
                "• Luôn cắm sạc Laptop và thiết lập Laptop ở chế độ 'Không ngủ khi gập màn hình' (Never Sleep) để hoạt động liên tục.\n\n"
                "• Khi có tiếng chuông hú báo động đỏ (🆘 KHẨN CẤP):\n\n"
                "   - Hãy kiểm tra ngay lập tức phòng của người cao tuổi.\n\n"
                "   - Nếu đó là báo động nhầm, hãy nhấn nút [ĐÃ XÁC NHẬN] trên màn hình hoặc biểu tượng cảnh báo để tắt chuông.\n\n"
                "• Số điện thoại hỗ trợ kỹ thuật gia đình: 1900-XXXX (Vui lòng ghi nhớ)."
            ),
            accent_color="#800000"
        )

        # ── Section 5: Demo Mode Explanation ──────────────────────────────────
        self.create_section(
            title="5. GIẢI THÍCH VỀ CHẾ ĐỘ MÔ PHỎNG (DEMO)",
            content=(
                "• Nếu góc trên ứng dụng hiển thị 'Chế độ mô phỏng', hệ thống đang tự tạo tín hiệu giả lập do:\n\n"
                "   1. Máy tính không có card mạng Wi-Fi vật lý hoặc card Wi-Fi đang bị tắt.\n\n"
                "   2. Quyền vị trí (Location Services) trên Windows 10/11 đang bị tắt. Quyền này là bắt buộc để ứng dụng quét sóng Wi-Fi xung quanh.\n\n"
                "   3. Ứng dụng chưa được chạy bằng quyền Quản trị viên (Administrator).\n\n"
                "• Cách khắc phục:\n\n"
                "   - Bật Wi-Fi và đảm bảo bạn có thể kết nối Internet.\n\n"
                "   - Vào Cài đặt Windows → Privacy & Security → Location → Bật Location Services cho Windows và cho phép các ứng dụng desktop truy cập.\n\n"
                "   - Nhấp chuột phải vào biểu tượng ứng dụng (hoặc run_desktop.bat) và chọn 'Run as Administrator' (Chạy dưới quyền quản trị)."
            ),
            accent_color="#808000"
        )

        # ── Section 6: GitHub Sync Guidance ───────────────────────────────────
        self.create_section(
            title="6. HƯỚNG DẪN ĐỒNG BỘ GITHUB & ĐIỀU KHIỂN TỪ XA",
            content=(
                "• Cơ chế đồng bộ không máy chủ (Serverless) giúp bạn giám sát và điều khiển ứng dụng từ xa cực kỳ tiện lợi.\n\n"
                "• Các bước thiết lập:\n\n"
                "   1. Tạo một tài khoản GitHub phụ (khuyên dùng tài khoản bot riêng để tăng tính bảo mật) và fork/tạo repository chứa Dashboard.\n\n"
                "   2. Tạo một Personal Access Token (PAT) trên GitHub chỉ cấp duy nhất quyền ghi nội dung (contents:write) vào repo này.\n\n"
                "   3. Nhập Token PAT, Tên tài khoản, Tên repo, Nhánh (ví dụ: main) và Định danh thiết bị (ví dụ: desktop) vào tab [Cấu Hình].\n\n"
                "   4. Bật công tắc [Bật đồng bộ qua GitHub], nhấn [Lưu Cấu Hinh] và [Kiểm Tra Kết Nối] để xác nhận kết nối xanh.\n\n"
                "   5. Mở Web Dashboard trên điện thoại hoặc trình duyệt khác, điền các thông tin y hệt để liên kết. Bạn có thể xem biểu đồ thời gian thực, mức sóng nền, độ nhạy và thực hiện TẮT CÒI BÁO ĐỘNG TỪ XA hoặc YÊU CẦU HIỆU CHỈNH."
            ),
            accent_color="#000080"
        )

        # ── Section 7: Bio-signals & Hardware Sensors ─────────────────────────
        self.create_section(
            title="7. THEO DÕI CHỈ SỐ SINH HIỆU & KẾT NỐI CẢM BIẾN VẬT LÝ",
            content=(
                "• Hệ thống hỗ trợ hai chế độ theo dõi sinh hiệu song song cực kỳ thông minh:\n\n"
                "   1. CHẾ ĐỘ SUY LUẬN PASSIVE WI-FI (Mặc định):\n\n"
                "      - Nhịp tim (BPM) & Số người: Được phân tích từ sự suy hao sóng đa hướng và dao động tần số siêu nhỏ (micro-variance) khi lồng ngực di chuyển lúc hít thở của người ngồi yên.\n\n"
                "      - Nhiệt độ cơ thể: Được ước lượng từ mức độ hoạt động và sự phản hồi nhịp tim thông qua thuật toán sinh học thermoregulation phi xâm lấn.\n\n"
                "      - Nhãn chỉ số trên giao diện sẽ hiển thị kèm chữ '(Ước tính)' màu đỏ/cam.\n\n"
                "   2. CHẾ ĐỘ CẢM BIẾN VẬT LÝ (Sensor Mode):\n\n"
                "      - Khi kết nối các cảm biến phần cứng qua cổng USB/Serial của máy tính (ví dụ: mô-đun ESP32 gắn cảm biến nhịp tim/SpO2 MAX30102 hoặc cảm biến nhiệt độ hồng ngoại không tiếp xúc MLX90614),\n\n"
                "        hệ thống sẽ tự động nhận diện và nạp dữ liệu chuẩn y tế này.\n\n"
                "      - Giao diện và Web Dashboard sẽ tự động cập nhật, nhãn '(Ước tính)' sẽ lập tức chuyển sang nhãn màu xanh lá hiển thị tên cảm biến thực tế như '(MAX30102)' hoặc '(MLX90614)'.\n\n"
                "      - Nồng độ oxy trong máu SpO2 (mặc định bị ẩn hoặc N/A khi dùng Wi-Fi) sẽ hiển thị chuẩn xác khi cảm biến MAX30102 được đeo vào tay."
            ),
            accent_color="#000080"
        )

    def create_section(self, title: str, content: str, accent_color: str):
        section_frame = ctk.CTkFrame(
            self.scroll_container, 
            fg_color="#d4d0c8", 
            border_color="#ffffff", 
            border_width=2, 
            corner_radius=0
        )
        section_frame.pack(fill="x", pady=8, padx=5)

        # Section Indicator Bar (Title bar in Win98 help style)
        title_frame = ctk.CTkFrame(section_frame, fg_color="#808080", height=22, corner_radius=0)
        title_frame.pack(fill="x", padx=2, pady=2)

        sec_title = ctk.CTkLabel(
            title_frame, 
            text=title, 
            text_color="#ffffff", 
            font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")
        )
        sec_title.pack(side="left", padx=8)

        # Inset text box for standard Windows help readability
        text_inset = ctk.CTkFrame(
            section_frame, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        text_inset.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Content Text (High readability Tahoma font with spacious line height)
        sec_content = ctk.CTkLabel(
            text_inset, 
            text=content, 
            text_color="#000000", 
            font=ctk.CTkFont(family="Tahoma", size=14),
            justify="left", 
            anchor="w",
            wraplength=760
        )
        sec_content.pack(anchor="w", padx=12, pady=10)
