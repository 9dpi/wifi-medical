# 📡 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG GIÁM SÁT AN TOÀN WIFI-CENSOR

Chào mừng bạn đến với **Wifi-Censor** — Hệ thống giám sát té ngã, sự hiện diện và theo dõi sinh hiệu phi tiếp xúc bằng sóng Wi-Fi dành cho gia đình. Hệ thống được thiết kế đặc biệt nhằm bảo vệ và theo dõi sức khỏe cho người lớn tuổi theo tiêu chí **bảo mật tối đa (local-first)** và **không tốn chi phí vận hành máy chủ**.

---

## 📌 MỤC LỤC
1. [Nguyên Lý Hoạt Động](#1-nguyên-lý-hoạt-động)
2. [Hướng Dẫn Lắp Đặt & Bố Trí](#2-hướng-dẫn-lắp-đặt--bố-trí)
3. [Quy Trình Hiệu Chỉnh Phòng Trống (Quan Trọng)](#3-quy-trình-hiệu-chỉnh-phòng-trống-quan-trọng)
4. [Cấu Hình Đồng Bộ Từ Xa Qua GitHub (Không Cần Server)](#4-cấu-hình-đồng-bộ-từ-xa-qua-github-không-cần-server)
5. [Giải Thích Các Chỉ Số Sinh Hiệu (Bio-Signals)](#5-giải-thích-các-chỉ-số-sinh-hiệu-bio-signals)
6. [Hướng Dẫn Tích Hợp Cảm Biến Vật Lý (Sensor Mode)](#6-hướng-dẫn-tích-hợp-cảm-biến-vật-lý-sensor-mode)
7. [Xử Lý Sự Cố Thường Gặp (Chế Độ Mô Phỏng)](#7-xử-lý-sự-cố-thường-gặp-chế-độ-mô-phỏng)
8. [Hướng Dẫn Sử Dụng Trợ Lý AI Cục Bộ (Local AI Agent)](#8-hướng-dẫn-sử-dụng-trợ-lý-ai-cục-bộ-local-ai-agent)

---

## 1. NGUYÊN LÝ HOẠT ĐỘNG
Hệ thống hoạt động dựa trên hiện tượng **Multipath Fading (Suy hao đa đường)** của sóng vô tuyến:
* Khi sóng Wi-Fi truyền từ bộ phát (Router) đến máy tính giám sát (Laptop), nó sẽ phản xạ qua các vật thể và cơ thể người.
* Cơ thể người chứa lượng nước lớn (khoảng 70%), làm hấp thụ và phản xạ sóng Wi-Fi mạnh mẽ.
* Khi lồng ngực di chuyển lúc hít thở hoặc khi đi lại, nó sẽ tạo ra những biến động siêu nhỏ trong cường độ tín hiệu sóng nhận được (**RSSI Variance**).
* Wifi-Censor thu thập và phân tích các biến động sóng này theo thời gian thực để đưa ra các dự đoán về sự hiện diện, hành vi (đi lại, nằm ngủ, bất động) và sinh hiệu.

---

## 2. HƯỚNG DẪN LẮP ĐẶT & BỐ TRÍ
Để đạt độ chính xác tối ưu, hãy bố trí các thiết bị theo nguyên tắc sau:
1. **Vị trí Laptop**: Đặt Laptop giám sát ở một góc cao trong phòng (trên kệ tủ, bàn làm việc) để có tầm nhìn bao quát và tránh bị che khuất bởi các đồ vật kim loại lớn (như tủ lạnh, lò vi sóng).
2. **Đường truyền sóng trực tiếp (LoS - Line of Sight)**: Hãy thiết lập sao cho khu vực giường nằm hoặc khu vực sinh hoạt chính của người cao tuổi nằm ở khoảng giữa Laptop giám sát và Bộ phát Wi-Fi (Router).
3. **Khoảng cách tối ưu**: Từ **3 đến 8 mét** giữa Laptop và Router Wi-Fi.
4. **Vật cản**: Tránh đặt thiết bị sau những bức tường bê tông quá dày (>20cm) vì sóng Wi-Fi sẽ bị suy hao cực lớn trước khi tới thiết bị.

---

## 3. QUY TRÌNH HIỆU CHỈNH PHÒNG TRỐNG (QUAN TRỌNG)
Hệ thống cần học mức độ nhiễu sóng nền của phòng khi không có người để làm mốc so sánh. Bạn **bắt buộc** phải thực hiện bước này sau khi lắp đặt hoặc khi di chuyển vị trí thiết bị:

1. Đảm bảo phòng **hoàn toàn trống** (không có người, không có vật nuôi di chuyển).
2. Mở ứng dụng Wifi-Censor trên máy tính.
3. Chọn mục **⚙️ Cài Đặt Hệ Thống** ở thanh trình đơn bên trái.
4. Nhấn nút **[Chạy hiệu chỉnh phòng trống (30 giây)]**.
5. Rời khỏi phòng lập tức và đóng cửa lại.
6. Hệ thống sẽ thu thập 30 mẫu sóng nền để tính toán ngưỡng chuẩn tự động. Sau 30 giây, trạng thái sẽ báo **"Hoàn thành (Đã khóa)"**.

---

## 4. CẤU HÌNH ĐỒNG BỘ TỪ XA QUA GITHUB (KHÔNG CẦN SERVER)
Wifi-Censor sử dụng kiến trúc **Serverless** thông minh dựa trên GitHub API làm cổng trung gian, loại bỏ hoàn toàn chi phí thuê máy chủ riêng và bảo vệ quyền riêng tư tuyệt đối.

Hệ thống hỗ trợ 2 phương pháp thiết lập kết nối:

### 🌟 PHƯƠNG PHÁP 1: CẤU HÌNH TỰ ĐỘNG 1-CLICK BẰNG FILE `quick_connect.bat` (Khuyên dùng)
Đây là cách nhanh nhất và tiện lợi nhất để kết nối Desktop App và Web Dashboard cùng một lúc:
1. Nhấp đúp vào tệp tin **`quick_connect.bat`** ở thư mục gốc của dự án.
2. Nhập các thông tin theo yêu cầu của chương trình:
   * **GitHub Personal Access Token (PAT)**
   * **GitHub Username** (Tên tài khoản)
   * **GitHub Repository** (Tên kho chứa, ví dụ: `wifi-medical`)
3. Chương trình sẽ tự động cập nhật tệp tin cấu hình `wificensor_config.json` của Desktop App.
4. Đồng thời, chương trình sẽ tự động tạo URL kết nối chứa sẵn Token và thông tin định danh của bạn, rồi hỏi xem bạn có muốn mở trình duyệt hay không.
5. Nếu chọn **[Y] (Yes)**, trình duyệt sẽ mở Web Dashboard và tự động ghi nhớ cấu hình của bạn vào bộ nhớ trình duyệt (**LocalStorage**). Bạn không cần phải nhập thủ công bất kỳ thông tin nào trên Web nữa!

---

### 🛠️ PHƯƠNG PHÁP 2: THIẾT LẬP THỦ CÔNG
Nếu bạn muốn tự tay thiết lập từng bước:

#### Bước A: Thiết lập trên GitHub (Một lần duy nhất)
1. Tạo một tài khoản GitHub riêng (khuyên dùng tài khoản phụ độc lập để bảo mật).
2. Tạo một Repository mới (ví dụ: đặt tên là `wifi-medical`).
3. Đi tới **Settings (Cài đặt tài khoản)** -> **Developer Settings** -> **Personal Access Tokens (Tokens cổ điển)** -> **Generate new token**.
4. Cấp duy nhất quyền `repo` hoặc `contents:write` (ghi tệp tin). Copy mã Token này và lưu trữ an toàn (mã Token chỉ hiển thị 1 lần).

### Bước B: Nhập thông tin cấu hình vào Desktop App
1. Trên Desktop App, mở mục **⚙️ Cài Đặt Hệ Thống**.
2. Nhập các thông tin sau vào khu vực **ĐỒNG BỘ CLOUD / GITHUB**:
   * **GitHub Token (PAT)**: *Mã Token bạn vừa copy ở Bước A*.
   * **Tên tài khoản**: *Username GitHub của bạn*.
   * **Tên Repository**: `wifi-medical` *(hoặc tên repo bạn đã tạo)*.
   * **Định danh thiết bị**: `desktop`.
   * **Nhánh đồng bộ**: `main`.
3. Bật công tắc **[Bật đồng bộ qua GitHub]**.
4. Nhấn **[Lưu Cấu Hình]**, sau đó nhấn **[Kiểm Tra Kết Nối]** để hệ thống kiểm tra. Đèn báo chuyển sang **xanh lá** nghĩa là liên kết thành công!

### Bước C: Sử dụng Web Dashboard giám sát
1. Mở trang Web Dashboard (liên kết với GitHub Pages hoặc chạy local).
2. Điền chính xác các thông tin GitHub Token, Tài khoản và Repo y hệt như trên Desktop App vào hộp cấu hình bảo mật trên trình duyệt.
3. Giờ đây bạn có thể giám sát trạng thái, xem biểu đồ nhịp tim, nhiệt độ thời gian thực trên điện thoại từ bất cứ đâu.
4. Bạn cũng có thể điều khiển thiết bị từ xa qua Web như **[TẮT CÒI BÁO ĐỘNG]** hoặc **[YÊU CẦU HIỆU CHỈNH]**.

---

## 5. GIẢI THÍCH CÁC CHỈ SỐ SINH HIỆU (BIO-SIGNALS)
Hệ thống Wifi-Censor hỗ trợ hai nguồn dữ liệu sinh hiệu song song:

### A. Chế độ Suy Luận Phi Xâm Lấn Qua Sóng Wi-Fi (Wi-Fi Inference)
Khi không có cảm biến vật lý kết nối, hệ thống sẽ suy luận các chỉ số thông qua các thuật toán AI/Sinh học:
* **💓 Nhịp tim (BPM)**: Phân tích tần số dao động siêu nhỏ trong biến động sóng (micro-variance) tương thích với nhịp thở và nhịp tim sinh học khi người dùng ngồi tĩnh lặng hoặc nằm ngủ.
* **🌡️ Nhiệt độ cơ thể (°C)**: Được suy luận gián tiếp từ sự phản hồi nhịp tim và mức độ vận động vật lý dựa trên các quy luật cân bằng thân nhiệt sinh học.
* **👥 Số người ước tính**: Tính toán từ sự suy hao sóng đa hướng tổng thể trong phòng.
* **Lưu ý hiển thị**: Các chỉ số này sẽ hiển thị nhãn **(Ước tính)** màu đỏ/cam trên giao diện để tránh nhầm lẫn với chẩn đoán y khoa chuyên sâu.

### B. Chế độ Cảm Biến Vật Lý Trực Tiếp (Sensor Mode)
Khi kết nối các cảm biến phần cứng thực tế, các thuật toán suy luận Wi-Fi sẽ tự động nhường chỗ cho dữ liệu đo đạc trực tiếp chính xác từ cảm biến:
* Các chỉ số nhịp tim, nhiệt độ sẽ lập tức chuyển sang nhãn màu xanh lá hiển thị tên cảm biến thực tế, ví dụ: **(MAX30102)** hoặc **(MLX90614)**.
* Chỉ số nồng độ oxy trong máu **SpO2 (%)** sẽ được kích hoạt hiển thị trực tiếp.

---

## 6. HƯỚNG DẪN TÍCH HỢP CẢM BIẾN VẬT LÝ (SENSOR MODE)
Bạn có thể dễ dàng nâng cấp hệ thống giám sát bằng cách bổ sung phần cứng đo đạc trực tiếp cực kỳ tiết kiệm chi phí:

### A. Phần cứng khuyên dùng:
1. **Mô-đun ESP32** hoặc **Arduino Nano** kết nối máy tính qua cổng USB.
2. **Cảm biến nhịp tim/SpO2 MAX30102** (đeo ngón tay hoặc cổ tay).
3. **Cảm biến nhiệt độ hồng ngoại không tiếp xúc MLX90614** (đo trán hoặc đo da nhiệt độ cơ thể).

### B. Sơ đồ lập trình & tích hợp dữ liệu:
* Bạn chỉ cần lập trình bo mạch ESP32 đọc dữ liệu từ cảm biến MAX30102 / MLX90614 và truyền qua cổng Serial (USB COM Port) lên máy tính.
* Ứng dụng Desktop có sẵn API `inject_sensor_data(heart_rate, spo2, temperature)` trong file `desktop/app/bio_estimator.py`.
* Bạn có thể chạy một tiến trình Python phụ đọc cổng Serial hoặc gửi API trực tiếp vào tiến trình chính để cập nhật dữ liệu sinh hiệu thời gian thực lên UI và Web Dashboard ngay lập tức.

---

## 7. XỬ LÝ SỰ CỐ THƯỜNG GẶP (CHẾ ĐỘ MÔ PHỎNG)
Nếu góc dưới ứng dụng hiển thị trạng thái màu xanh cyan: **"Chế độ: Mô phỏng" (Demo Mode)**, hệ thống đang phải tự tạo dữ liệu giả lập do không thể truy cập card mạng Wi-Fi thực tế.

### Nguyên nhân và cách khắc phục:
1. **Tắt vị trí (Location Services) trên Windows 10/11**:
   * *Nguyên nhân*: Windows yêu cầu quyền truy cập Vị trí để cho phép quét các trạm phát Wi-Fi xung quanh nhằm mục đích bảo mật.
   * *Cách sửa*: Vào **Settings (Cài đặt Windows)** -> **Privacy & Security** -> **Location** -> Gạt nút bật **Location Services** lên, và đảm bảo tùy chọn **"Let desktop apps access your location"** đã được kích hoạt.
2. **Thiếu quyền Quản trị viên (Administrator)**:
   * *Nguyên nhân*: Một số dòng lệnh quét sóng cấp thấp yêu cầu đặc quyền hệ thống.
   * *Cách sửa*: Nhấp chuột phải vào file chạy ứng dụng (hoặc file `desktop/main.py` / file chạy `.bat`) và chọn **"Run as Administrator"** (Chạy dưới quyền quản trị viên).
3. **Không có card mạng Wi-Fi vật lý**:
   * *Nguyên nhân*: Thiết bị sử dụng mạng dây LAN và không có card mạng không dây Wi-Fi, hoặc card Wi-Fi đang bị vô hiệu hóa (Disabled).
   * *Cách sửa*: Hãy gắn thêm một chiếc USB Wi-Fi nhỏ gọn hoặc bật tính năng Wi-Fi trong Windows Device Manager.

---

## 8. HƯỚNG DẪN SỬ DỤNG TRỢ LÝ AI CỤC BỘ (LOCAL AI AGENT)
Từ phiên bản MVP 2, Wifi-Censor tích hợp một **Trợ lý AI chạy hoàn toàn cục bộ (Local AI Agent)** trên máy tính của bạn thông qua nền tảng **Ollama** và mô hình **Gemma 4**. Tính năng này không cần kết nối internet, đảm bảo dữ liệu sức khỏe và sinh hoạt của người thân không bao giờ rời khỏi ngôi nhà của bạn.

### A. Chuẩn bị hệ thống & Cài đặt (Ollama)
Hệ thống sử dụng mô hình local siêu nhẹ nhưng thông minh để phân tích và ra quyết định thời gian thực:
1. **Ollama**: Đảm bảo ứng dụng Ollama đã được cài đặt và đang chạy ngầm trên máy tính của bạn (mặc định tại cổng `http://localhost:11434`).
2. **Tải Mô hình (Model)**: Hệ thống sử dụng mô hình **`gemma4:e4b`** làm mô hình chính (hoặc tự động fallback sang `gemma3:4b` hoặc `gemma3:2b` tùy theo cấu hình GPU/RAM máy tính của bạn).
   * Bạn có thể tải mô hình bằng dòng lệnh: `ollama pull gemma4:e4b`

### B. Cấu hình AI trên Desktop App
1. Trên ứng dụng, truy cập tab **⚙️ Cài Đặt Hệ Thống** ở thanh trình đơn bên trái.
2. Cuộn xuống phần **5. TRỢ LÝ AI (OLLAMA - CHẠY LOCAL)**:
   * **Bật Trợ lý AI**: Gạt công tắc sang trạng thái **Bật**.
   * **Ollama URL**: Mặc định là `http://localhost:11434` (đường dẫn tới Ollama API).
   * **Model AI**: Tên model muốn sử dụng (mặc định: `gemma4:e4b`).
   * **Giờ tạo báo cáo tự động (0-23)**: Đặt khung giờ bạn muốn AI tự động phân tích dữ liệu ngày và xuất báo cáo PDF (ví dụ: `21` nghĩa là 21:00 tối hằng ngày).
3. Nhấn **[Lưu AI Settings]** để lưu cấu hình.
4. Nhấn **[Test Kết Nối Ollama]** để xác minh kết nối. Hệ thống sẽ báo kết nối thành công và xác nhận sự tồn tại của model được chọn.

### C. Chat trực tiếp với Trợ lý AI (Tab AI Chat)
Truy cập tab **🤖 Trợ Lý AI** ở menu bên trái để mở giao diện đối thoại tiếng Việt thời gian thực:
* **Giao diện Chat Streaming**: AI sẽ gõ câu trả lời trực tiếp từng chữ (streaming) cực kỳ sinh động mà không bắt bạn phải chờ đợi lâu.
* **Gợi ý Câu hỏi Nhanh (Quick Prompts)**: Nhấn trực tiếp vào các nút gợi ý ở dưới khung chat để yêu cầu AI trả lời nhanh:
  * 📊 *Tình trạng sức khỏe hôm nay?*: AI sẽ gọi tool `query_health` phân tích nhịp tim, thân nhiệt, sự hiện diện và hoạt động của người thân trong phòng 24 giờ qua.
  * 🔔 *Hôm nay có cảnh báo nào không?*: AI kiểm tra lịch sử cảnh báo ngã hoặc bất động trong SQLite và giải thích chi tiết.
  * 💾 *Xuất báo cáo PDF ngay*: AI sẽ lập tức biên soạn báo cáo phân tích sức khỏe trong ngày và xuất ra một tệp PDF chuyên nghiệp.
* **Gọi Tool Python tự động (ReAct Agent)**: Bạn có thể chat tự do bằng tiếng Việt (ví dụ: *"Nhịp tim của mẹ 2 tiếng qua thế nào?"* hoặc *"Tăng độ nhạy giám sát lên"*). AI sẽ tự động phân tích câu hỏi, gọi các hàm Python (Tools) truy vấn SQLite hoặc cập nhật cấu hình hệ thống, rồi tổng hợp câu trả lời cho bạn.

### D. Cơ chế AI Fall Verifier (Giảm Báo Giả té ngã)
Một trong những đột phá lớn nhất của MVP 2 là việc sử dụng AI để xác nhận té ngã:
* **Cơ chế cũ (MVP 1)**: Khi sóng RSSI biến động mạnh đột ngột và tắt hẳn, hệ thống sẽ hú còi báo ngã ngay lập tức. Điều này có thể dẫn đến báo động giả khi người dùng đặt vật nặng hoặc di chuyển quá nhanh.
* **Cơ chế AI mới (MVP 2)**: Khi phát hiện biến động nghi ngờ té ngã, hệ thống sẽ kích hoạt **FallVerifier**:
  1. Thu thập dữ liệu sóng RSSI và nhịp tim (BPM) 10 giây trước và sau sự kiện.
  2. Gửi dữ liệu này cùng bối cảnh hoạt động và thời điểm trong ngày cho AI Agent phân tích.
  3. AI sẽ phán quyết xem đó là một cú **Ngã thực sự (FALL)** hay là **Báo động giả (False alarm)** dựa trên mô hình học máy.
  4. Nếu AI xác nhận ngã, còi báo động khẩn cấp sẽ hú vang. Nếu AI phán quyết là báo giả, hệ thống sẽ im lặng ghi nhận, giảm thiểu sự hoảng loạn cho gia đình lên tới 50%!
  * *Lưu ý*: Nếu AI không phản hồi trong vòng 5 giây do máy tính quá tải, hệ thống sẽ tự động kích hoạt chế độ Fallback của MVP 1 để đảm bảo an toàn tối đa cho người bệnh.

### E. Báo cáo Sức khỏe Thông minh (PDF Daily Report)
Hệ thống tự động biên soạn báo cáo PDF vào khung giờ đã cấu hình hoặc khi bạn yêu cầu thủ công:
* **Nội dung báo cáo**: Tổng quan hoạt động ngày, thời lượng có mặt/vắng phòng, nhịp tim trung bình/tối đa, biến thiên thân nhiệt, danh sách cảnh báo đã ghi nhận và lời khuyên sức khỏe chuyên sâu của AI dành riêng cho người thân của bạn.
* **Nơi lưu trữ**: File PDF báo cáo sẽ được lưu trực tiếp tại thư mục `desktop/data/reports/` dưới định dạng tên file chứa ngày tháng rõ ràng. Bạn có thể dễ dàng gửi file này qua Zalo, Email cho bác sĩ hoặc lưu trữ làm hồ sơ bệnh án gia đình.

---
*Mọi góp ý hoặc yêu cầu hỗ trợ kỹ thuật xin gửi về nhóm phát triển Wifi-Censor. Hãy cùng nhau mang lại sự an toàn và bình yên cho thế hệ cha mẹ, ông bà của chúng ta!*
