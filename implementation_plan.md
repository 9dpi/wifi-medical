# Wifi-Censor: Invisible Spatial Sensing System

Xây dựng một hệ thống cảm biến không gian vô hình (Invisible Spatial Sensing) sử dụng tín hiệu Wi-Fi có sẵn trong gia đình, chạy hoàn toàn cục bộ (local-first), không gửi dữ liệu ra cloud, không cần phần cứng chuyên dụng, triển khai qua một ứng dụng Android duy nhất.

---

## User Review Required

> [!IMPORTANT]
> Kiến trúc tổng thể của hệ thống chia làm **3 layer**:
> - **Layer 1 – Signal Layer**: Thu thập tín hiệu Wi-Fi (RSSI hoặc CSI)
> - **Layer 2 – AI/ML Layer**: Xử lý tín hiệu, trích xuất đặc trưng, nhận diện hành vi
> - **Layer 3 – Application Layer**: Dashboard Android, cảnh báo, báo cáo sức khỏe

> [!WARNING]
> **Giới hạn quan trọng của Android (không root)**:
> Truy cập CSI (Channel State Information) trực tiếp từ Android yêu cầu driver Wi-Fi cấp thấp. Một số thiết bị hỗ trợ (Nexus 5, Pixel series với custom firmware) nhưng KHÔNG phải tất cả. **Giải pháp thay thế khả thi hơn**: dùng **ESP32-S3 làm CSI collector** và điện thoại làm **dashboard + edge inference engine** (nhận data từ ESP32 qua local network).

> [!CAUTION]
> Giai đoạn MVP 1 chỉ dùng **RSSI** (Received Signal Strength Indicator) — đơn giản, khả thi 100% nhưng độ chính xác thấp hơn CSI. Cần cân nhắc kỳ vọng của người dùng ở giai đoạn đầu.

---

## Open Questions

> [!IMPORTANT]
> **Q1: Thiết bị mục tiêu là gì?**
> - Option A: Chỉ Android (dễ phát triển, tập trung)
> - Option B: Android + iOS (phạm vi rộng hơn nhưng phức tạp hơn)
> - Option C: Android + Web Dashboard (dễ demo, cross-platform)

> [!IMPORTANT]
> **Q2: Phần cứng ESP32 có chấp nhận không?**
> - Option A: Chỉ dùng điện thoại + router có sẵn (MVP 1 thuần RSSI, $0)
> - Option B: Cho phép thêm ESP32-S3 (~$9/chiếc, 3-6 node) để có CSI chính xác hơn
> - Quyết định này ảnh hưởng lớn đến roadmap và độ chính xác hệ thống

> [!IMPORTANT]
> **Q3: Phạm vi triển khai ban đầu?**
> - Option A: 1 phòng (chứng minh khái niệm)
> - Option B: Toàn bộ căn hộ (thực tế hơn nhưng phức tạp hơn)

---

## Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WIFI-CENSOR ARCHITECTURE                         │
├─────────────────┬───────────────────────┬───────────────────────────┤
│   SIGNAL LAYER  │      AI/ML LAYER      │     APPLICATION LAYER     │
│                 │                       │                           │
│  Router Wi-Fi   │  Feature Extraction   │   Android App             │
│  (TX – nguồn)   │  ├── STFT/Wavelet     │   ├── Live Dashboard      │
│       │         │  ├── Doppler shift    │   ├── Health Metrics      │
│       ▼         │  └── Phase velocity   │   ├── Alert System        │
│  Android/ESP32  │                       │   └── History Timeline    │
│  (RX – thu)     │  Inference Engine     │                           │
│  ├── RSSI       │  ├── Presence Detect  │   Notification            │
│  └── CSI        │  ├── Activity Class   │   ├── Zalo/Telegram       │
│                 │  ├── Vital Signs      │   ├── SMS                 │
│  Local Network  │  └── Fall Detection   │   └── In-app alert        │
│  (LAN only)     │  [TFLite / ONNX]      │                           │
└─────────────────┴───────────────────────┴───────────────────────────┘
         ↑ Toàn bộ dữ liệu xử lý LOCAL, không gửi cloud ↑
```

---

## Proposed Changes

### Phase 1 — MVP 1: RSSI-based Presence Detection (2 tuần)

**Mục tiêu**: Chứng minh khái niệm. Phát hiện có người/không có người trong phòng với độ chính xác >85%.

**Công nghệ**: RSSI (luôn khả dụng trên Android không cần root)

---

#### [NEW] Android App Core (`/app`)

##### [NEW] `MainActivity.kt`
- Entry point của ứng dụng
- Khởi tạo Wi-Fi Scanner service
- Navigation giữa các màn hình

##### [NEW] `WifiScannerService.kt`
- Background service thu thập RSSI từ tất cả Access Points trong tầm
- Tần suất: 1-4 lần/giây (giới hạn bởi Android API)
- Lưu vào local SQLite/Room database

##### [NEW] `PresenceDetectorV1.kt`
- Thuật toán phát hiện hiện diện dựa trên RSSI variance
- Logic: Khi có người → RSSI dao động; Không có người → RSSI ổn định
- Output: `PRESENT` / `ABSENT` / `UNKNOWN`

##### [NEW] `DashboardFragment.kt`
- Màn hình chính hiển thị trạng thái thời gian thực
- Indicator: 🟢 Có người / ⚪ Vắng / 🔴 Bất thường

##### [NEW] `RoomDatabase.kt` (Room/SQLite)
- Schema lưu RSSI samples (timestamp, BSSID, RSSI, channel)
- Schema lưu presence events
- Data retention: 30 ngày

---

### Phase 2 — MVP 2: CSI Collection với ESP32-S3 (1 tháng)

**Mục tiêu**: Nâng độ chính xác lên >95%. Thu thập CSI raw data 40+ Hz.

**Công nghệ**: ESP32-S3 (firmware esp-csi), local MQTT broker trên Android

---

#### [NEW] ESP32 Firmware (`/firmware`)

##### [NEW] `esp32_csi_collector/main.c`
- Firmware cho ESP32-S3 dựa trên esp-csi library
- Thu thập CSI với tần suất 40-100 Hz
- Gửi data qua MQTT/UDP về Android app
- Deep sleep mode khi không hoạt động (tiết kiệm điện)

##### [NEW] `esp32_csi_collector/config.h`
- Cấu hình: SSID/Password Wi-Fi
- MQTT broker address (IP của Android trên LAN)
- Sampling rate, channel, bandwidth

---

#### [MODIFY] Android App — CSI Processing (`/app`)

##### [NEW] `MqttBrokerService.kt`
- Embedded MQTT broker (HiveMQ CE hoặc Moquette)
- Nhận CSI streams từ các ESP32 nodes
- Parse và validate CSI packets

##### [NEW] `CsiProcessor.kt`
- Xử lý raw CSI: loại bỏ nhiễu (Hampel filter)
- STFT (Short-Time Fourier Transform) để phân tích tần số
- Trích xuất Doppler shift để phát hiện chuyển động

##### [NEW] `VitalSignsEstimator.kt`
- Phân tích tần số 0.1-0.5 Hz → nhịp thở (6-30 lần/phút)
- Phân tích tần số 0.8-2.0 Hz → nhịp tim (48-120 bpm)
- Output: BPM estimates với confidence score

---

### Phase 3 — MVP 3: AI Edge Inference (1-2 tháng)

**Mục tiêu**: Phân loại hoạt động, phát hiện té ngã, theo dõi vị trí.

**Công nghệ**: TensorFlow Lite (Android), mô hình CNN/LSTM nhỏ gọn

---

#### [NEW] AI/ML Models (`/models`)

##### [NEW] `activity_classifier/`
- Dataset: Thu thập từ ESP32 nodes trong môi trường thực
- Model: 1D-CNN hoặc MobileNet adapted cho time-series
- Labels: `walking`, `sitting`, `lying`, `standing`, `falling`
- Target size: <5MB để chạy trên điện thoại

##### [NEW] `fall_detector/`
- Model riêng biệt tối ưu cho fall detection
- Kết hợp CSI + accelerometer (nếu có thiết bị đeo thêm)
- Latency target: <500ms để cảnh báo kịp thời

##### [NEW] `training/train_pipeline.py`
- Python pipeline để train/fine-tune models
- Convert sang TFLite với quantization (INT8)
- Benchmark accuracy vs. model size

---

#### [NEW] Android — Inference Engine (`/app`)

##### [NEW] `TFLiteInferenceEngine.kt`
- Wrapper cho TensorFlow Lite Interpreter
- Load model từ assets
- Batch inference với sliding window

##### [NEW] `FallDetectionService.kt`
- Foreground service chạy 24/7
- Gửi alert ngay khi phát hiện té ngã
- Notification với nút gọi khẩn cấp

---

### Phase 4 — MVP 4: Dashboard & Alerting (song song)

**Mục tiêu**: UI/UX hoàn chỉnh, hệ thống cảnh báo đa kênh.

---

#### [NEW] Android UI (`/app/ui`)

##### [NEW] `HealthDashboardScreen.kt`
- Real-time vital signs display
- Timeline graph: 24h activity history
- Status indicator: 🟢 Tốt / 🟡 Cảnh báo / 🔴 Cấp cứu

##### [NEW] `AlertConfigScreen.kt`
- Cấu hình ngưỡng cảnh báo (bất động >30 phút, etc.)
- Thêm số điện thoại/Telegram người thân
- Lịch trình "giờ ngủ" để giảm false alerts

##### [NEW] `AlertDispatcher.kt`
- Gửi thông báo qua nhiều kênh:
  - Telegram Bot API (local processing, chỉ gửi notification text)
  - SMS (Android SMS API)
  - In-app push notification

##### [NEW] `FloorPlanMapper.kt`
- Vẽ bản đồ 2D đơn giản của nhà
- Hiển thị vị trí ước tính của người dùng theo thời gian thực
- Dựa trên fingerprinting RSSI/CSI từ nhiều nodes

---

## Tech Stack

| Layer | Công nghệ | Lý do chọn |
|-------|-----------|------------|
| Android App | Kotlin + Jetpack Compose | Modern, declarative UI |
| Local DB | Room (SQLite) | Offline-first |
| Signal Processing | Apache Commons Math / custom DSP | FFT, filtering |
| AI Inference | TensorFlow Lite | Chạy tốt trên Android, không cần internet |
| ESP32 Firmware | esp-idf + esp-csi | Official CSI support từ Espressif |
| Local Messaging | MQTT (Moquette embedded) | Lightweight, phù hợp IoT |
| Alert | Telegram Bot API + SMS | Không cần app riêng cho người thân |
| Build | Gradle + CMake (cho JNI nếu cần) | Standard Android |

---

## Verification Plan

### Phase 1 — RSSI Testing
- **Unit test**: `PresenceDetectorV1` với dataset RSSI mẫu
- **Field test**: Đo accuracy trong 1 phòng, 5 kịch bản khác nhau (có người/vắng/di chuyển)
- **Target**: Precision >85%, Recall >90%

### Phase 2 — CSI Testing
- **Integration test**: ESP32 → MQTT → Android pipeline
- **Signal test**: Kiểm tra CSI data quality (SNR, sampling rate)
- **Vital signs test**: So sánh nhịp thở ước tính với smartwatch reference

### Phase 3 — AI Testing
- **Model benchmark**: Latency <100ms trên mid-range Android
- **Fall detection test**: 50+ simulated falls, target F1 >0.90
- **Battery test**: <5% battery drain/giờ ở chế độ monitoring

### Phase 4 — E2E Testing
- **Alert pipeline test**: Thời gian từ event → Telegram notification <3 giây
- **UI/UX test**: Test với người dùng 60+ tuổi (target audience)
- **Stability test**: 72 giờ chạy liên tục không crash

---

## Lộ Trình Tổng Thể

```
Tuần 1-2:   [Phase 1] RSSI Collection + Basic Presence Detection
Tuần 3-4:   [Phase 1] Dashboard UI + Alert System cơ bản
Tuần 5-6:   [Phase 2] ESP32 Firmware + MQTT Integration
Tuần 7-8:   [Phase 2] CSI Processing + Vital Signs Estimation
Tuần 9-12:  [Phase 3] Dataset Collection + Model Training
Tuần 13-14: [Phase 3] TFLite Inference + Fall Detection
Tuần 15-16: [Phase 4] Full Dashboard + Multi-channel Alerts
Tuần 17+:   Beta Testing + Optimization
```

---

## Cấu Trúc Thư Mục Dự Án

```
Wifi-Censor/
├── app/                          # Android application
│   ├── src/main/
│   │   ├── java/com/wificensor/
│   │   │   ├── ui/               # Jetpack Compose screens
│   │   │   ├── sensing/          # RSSI/CSI collection
│   │   │   ├── processing/       # Signal processing
│   │   │   ├── inference/        # TFLite models
│   │   │   ├── alerts/           # Alert dispatching
│   │   │   └── data/             # Room DB, repositories
│   │   └── res/                  # Resources
│   └── build.gradle
├── firmware/                     # ESP32 firmware
│   └── esp32_csi_collector/
├── models/                       # ML model training (Python)
│   ├── activity_classifier/
│   ├── fall_detector/
│   └── training/
├── docs/                         # Documentation
│   ├── architecture.md
│   ├── esp32_setup.md
│   └── research_references.md
└── README.md
```
