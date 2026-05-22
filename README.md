# 📡 Wifi-Censor

> **Invisible Spatial Sensing** — Biến ngôi nhà thành môi trường cảm biến thông minh chỉ với điện thoại và router Wi-Fi có sẵn.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: Android](https://img.shields.io/badge/Platform-Android%208%2B-blue.svg)](https://developer.android.com)
[![Local-first](https://img.shields.io/badge/Privacy-Local--first-purple.svg)](docs/privacy.md)

---

## 🎯 Tính năng

| Tính năng | Trạng thái | Mô tả |
|-----------|-----------|-------|
| 🟢 Phát hiện hiện diện | ✅ MVP 1 | Phát hiện có/vắng người qua phương sai RSSI |
| 🚶 Phân loại hoạt động | ✅ MVP 1 | Đi lại / ngồi yên / ngủ |
| ⚠️ Cảnh báo bất động | ✅ MVP 1 | Alert khi bất động > 45 phút |
| 🔴 Phát hiện té ngã | ✅ MVP 1 | Phát hiện biến mất đột ngột tín hiệu |
| 🌐 Web Dashboard | ✅ MVP 1 | GitHub Pages + Google Drive sync |
| 💓 Nhịp tim/thở | 🚧 MVP 2 | Cần CSI (ESP32 hoặc thiết bị hỗ trợ) |

---

## 🏗️ Kiến trúc

```
📱 Android App (Kotlin + Compose)
├── WifiScanner          → Thu thập RSSI từ WifiManager
├── PresenceEngine       → Thuật toán phát hiện qua phương sai RSSI
├── AnomalyTracker       → Cảnh báo bất động, té ngã
├── SensingService       → Foreground service (chạy nền 24/7)
├── GoogleDriveSyncWorker → Xuất JSON → Google Drive mỗi 5 phút
└── Room DB              → Lưu lịch sử 30 ngày (local)

🌐 Web Dashboard (HTML/CSS/JS)
├── Fetch JSON từ Google Drive public link
├── Chart.js → Biểu đồ RSSI 24h
└── Auto-refresh mỗi 30-60 giây
```

---

## 🚀 Cài đặt nhanh

### Yêu cầu
- Android 8.0+ (API 26+)
- Wi-Fi đã kết nối
- Bật Location permission (bắt buộc để đọc Wi-Fi scan results trên Android 10+)

### Android App

1. Clone repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Wifi-Censor.git
   cd Wifi-Censor/app
   ```

2. Build APK:
   ```bash
   ./gradlew assembleDebug
   ```

3. Cài lên điện thoại:
   ```bash
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

4. Mở app → nhấn **Bắt đầu** → cấp quyền Location

### Web Dashboard

1. Enable GitHub Pages (chọn thư mục `/docs` trên nhánh `main`)
2. Hoặc mở `docs/index.html` trực tiếp trên browser

3. Cấu hình Google Drive:
   - Trên điện thoại: Settings → Bật Google Drive sync
   - Lấy link public của file `wificensor_status.json`
   - Dán vào ô "Google Drive JSON URL" trên Dashboard

---

## 📊 Thuật toán phát hiện hiện diện

**RSSI Variance Detection Method:**

```
Khi có người di chuyển:
  → Multipath interference → RSSI dao động mạnh (variance cao)

Khi phòng vắng:
  → Môi trường ổn định → RSSI ổn định (variance thấp)

Ngưỡng adaptive:
  1. Calibration 60 samples → học "baseline vắng phòng"
  2. PRESENT threshold = baseline × 3.0
  3. WALKING threshold  = baseline × 8.0
```

**Độ chính xác dự kiến:**
- Phòng 15-25m²: ~85-90%
- Phòng lớn hoặc nhiều vật cản: ~75-85%

---

## 📁 Cấu trúc thư mục

```
Wifi-Censor/
├── app/                          # Android application
│   ├── app/src/main/
│   │   ├── java/com/example/wificensor/
│   │   │   ├── sensing/
│   │   │   │   ├── WifiScanner.kt
│   │   │   │   ├── PresenceEngine.kt
│   │   │   │   ├── AnomalyTracker.kt
│   │   │   │   └── SensingService.kt
│   │   │   ├── data/
│   │   │   │   └── WifiCensorDatabase.kt
│   │   │   ├── sync/
│   │   │   │   └── GoogleDriveSyncWorker.kt
│   │   │   └── ui/
│   │   │       ├── DashboardScreen.kt
│   │   │       └── MainViewModel.kt
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
├── docs/                         # Web Dashboard (GitHub Pages)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       └── charts.js
└── README.md
```

---

## 🛡️ Quyền riêng tư

- ✅ **Local-first**: Tất cả xử lý trên thiết bị
- ✅ **No cloud**: Raw RSSI data không bao giờ rời khỏi điện thoại
- ✅ **Minimal sync**: Chỉ kết quả phân tích (JSON text) được sync — không có audio, video, location GPS
- ✅ **Open source**: Code hoàn toàn minh bạch

---

## 📜 License

MIT License — xem [LICENSE](LICENSE)
