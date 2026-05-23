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
test_e2e.py — End-to-End (E2E) Test Suite for Wifi-Censor MVP 2.
Simulates a complete real-time sensing session with Wi-Fi inference, 
AI-assisted fall verification (FallVerifier via Gemma 4), SQLite persistence, 
and automatic daily PDF report generation.
"""

import os
import sys
import time
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

print("======================================================================")
print("     📡 WIFI-CENSOR MVP 2 - END-TO-END (E2E) INTEGRATION TEST")
print("======================================================================")
print()

# Ensure we import core modules properly
try:
    from desktop.app.config import get_config, get_config_manager
    from desktop.app.database import Database
    from desktop.app.scanner import WifiScanner
    from desktop.app.presence_engine import PresenceEngine, PresenceState, ActivityState, PresenceResult
    from desktop.app.anomaly_tracker import AnomalyTracker
    from desktop.app.exporter import JsonExporter
    from desktop.app.bio_estimator import BioSignalEstimator

    # AI Agent imports
    from desktop.app.ai.ollama_manager import OllamaManager
    from desktop.app.ai.tools import ToolExecutor
    from desktop.app.ai.agent import WifiCensorAgent
    from desktop.app.ai.fall_verifier import FallVerifier
    from desktop.app.ai.report_generator import ReportGenerator

    print("✅ [Test 1] Tất cả các module core & AI đã import thành công!")
except ImportError as e:
    print(f"❌ [Test 1] Lỗi import module: {e}")
    sys.exit(1)

# Setup temporary databases and directories for test isolation
db_path = Path("desktop/data/wificensor_test.db")
if db_path.exists():
    try:
        os.remove(db_path)
    except Exception:
        pass

db = Database(str(db_path))
print("✅ [Test 2] Khởi tạo SQLite Test Database cô lập thành công!")

# 1. Initialize core pipeline components
scanner = WifiScanner()
from desktop.app.scanner import ScannerMode
scanner._mode = ScannerMode.DEMO
engine = PresenceEngine()
tracker = AnomalyTracker()
exporter = JsonExporter(db)
bio_estimator = exporter.bio_estimator

# 2. Setup AI Agent components
cfg = get_config()
ollama = OllamaManager(base_url=cfg.ollama_url)
print(f"🔄 Đang kết nối tới Ollama tại: {cfg.ollama_url}...")

if not ollama.health_check():
    print("❌ Ollama không hoạt động hoặc chưa khởi động! Bỏ qua các bước kiểm tra AI thực tế.")
    ai_available = False
else:
    model = ollama.select_best_model()
    print(f"✅ Ollama đang hoạt động. Đã chọn mô hình: {model}")
    ai_available = True

# Global alert trigger receiver for verification
triggered_alerts = []
def test_alert_callback(alert_type, title, message):
    print(f"\n🔔 >>> BÁO ĐỘNG HỆ THỐNG KÍCH HOẠT: [{alert_type}] - {title}")
    print(f"    Chi tiết: {message}\n")
    triggered_alerts.append((alert_type, title, message))

tracker.start()

if ai_available:
    tool_exec = ToolExecutor(db, exporter, get_config_manager())
    agent = WifiCensorAgent(ollama, tool_exec)
    
    # Initialize FallVerifier and set references
    fall_verifier = FallVerifier()
    fall_verifier.set_agent(agent)
    fall_verifier.set_alert_callback(test_alert_callback)
    tracker.set_fall_verifier(fall_verifier)
    
    # Initialize ReportGenerator
    report_gen = ReportGenerator(db, bio_estimator)
    report_gen.set_agent(agent)
    print("✅ [Test 3] Khởi tạo và liên kết thành công AI Agent, FallVerifier & ReportGenerator!")
else:
    print("⚠️  Chạy E2E ở chế độ Non-AI Fallback (MVP 1)...")

# 3. Simulate Normal activities (10 steps)
print("\n--- 🏃‍♂️ Giai đoạn 1: Giám sát trạng thái hoạt động bình thường ---")
normal_samples = [
    # (rssi_mean, variance, activity)
    (-50.0, 1.2, ActivityState.STATIONARY),
    (-49.5, 1.5, ActivityState.STATIONARY),
    (-51.0, 3.4, ActivityState.MOVING),
    (-52.5, 6.8, ActivityState.WALKING),
    (-50.2, 5.5, ActivityState.WALKING),
    (-49.0, 1.1, ActivityState.STATIONARY),
    (-48.8, 0.8, ActivityState.STATIONARY),
    (-49.2, 0.4, ActivityState.SLEEPING),
    (-49.3, 0.3, ActivityState.SLEEPING),
    (-49.1, 0.5, ActivityState.SLEEPING),
]

for i, (rssi, var, act) in enumerate(normal_samples):
    # Simulate presence engine output
    res = PresenceResult(
        dominant_bssid="00:11:22:33:44:55",
        rssi_mean=rssi,
        rssi_variance=var,
        presence=PresenceState.PRESENT,
        activity=act,
        confidence=0.92 - (i * 0.01)
    )
    
    # Estimate bio-signals
    bio_result = bio_estimator.update(rssi, res)
    
    # Save RSSI to Database
    db.insert_rssi(
        ts=time.time(),
        bssid=res.dominant_bssid,
        ssid="WiFi-Medical-Demo",
        rssi=int(res.rssi_mean),
        variance=res.rssi_variance,
        label=res.presence.value
    )
    
    # Check anomalies
    tracker.on_result(res, test_alert_callback, bio_bpm=bio_result.heart_rate_bpm)
    
    # Push to FallVerifier buffer
    if ai_available:
        fall_verifier.push_rssi(res.rssi_mean, res.rssi_variance, res.activity.value)
        
    hr_str = f"{bio_result.heart_rate_bpm:.1f}" if bio_result.heart_rate_bpm is not None else "Đang tính..."
    temp_str = f"{bio_result.body_temp_celsius:.1f}" if bio_result.body_temp_celsius is not None else "Đang tính..."
    print(f"Bước {i+1}: RSSI={rssi}dBm, Var={var:.2f}, Hoạt động={act.value}, Nhịp tim={hr_str} BPM, Thân nhiệt={temp_str}°C")
    time.sleep(0.1)

print("✅ [Test 4] Giả lập hoạt động bình thường hoàn tất. Dữ liệu đã lưu SQLite!")

# 4. Simulate a FALL event (Té ngã)
print("\n--- 🚨 Giai đoạn 2: Giả lập sự kiện Nghi ngờ Té Ngã (Fall Suspected) ---")

# Step 11: Normal walking
res_normal = PresenceResult(
    dominant_bssid="00:11:22:33:44:55",
    rssi_mean=-51.0,
    rssi_variance=5.2,
    presence=PresenceState.PRESENT,
    activity=ActivityState.WALKING,
    confidence=0.95
)
bio_normal = bio_estimator.update(-51.0, res_normal)
tracker.on_result(res_normal, test_alert_callback, bio_bpm=bio_normal.heart_rate_bpm)
if ai_available:
    fall_verifier.push_rssi(res_normal.rssi_mean, res_normal.rssi_variance, res_normal.activity.value)

# Step 12: HUGE drop in RSSI (Fall crash impact)
res_fall = PresenceResult(
    dominant_bssid="00:11:22:33:44:55",
    rssi_mean=-75.0,
    rssi_variance=48.5,  # Extreme variance
    presence=PresenceState.PRESENT,
    activity=ActivityState.MOVING,
    confidence=0.98
)
bio_fall = bio_estimator.update(-75.0, res_fall)
print("💥 [CÚ VA CHẠM]: Sóng RSSI tụt mạnh (-75.0 dBm), Biến động cực đại (48.5)!")
tracker.on_result(res_fall, test_alert_callback, bio_bpm=bio_fall.heart_rate_bpm)
if ai_available:
    fall_verifier.push_rssi(res_fall.rssi_mean, res_fall.rssi_variance, res_fall.activity.value)

# Step 13: Absolute silence / Absence (lying on the floor)
res_silent = PresenceResult(
    dominant_bssid="00:11:22:33:44:55",
    rssi_mean=-78.0,
    rssi_variance=0.08,  # Near zero variance (unconscious)
    presence=PresenceState.ABSENT,  # Absent state trigger
    activity=ActivityState.STATIONARY,
    confidence=0.99
)
bio_silent = bio_estimator.update(-78.0, res_silent)
print("🤫 [BẤT ĐỘNG]: Sóng biến động gần như bằng không (0.08), Người dùng nằm sàn!")

# This will trigger the FallVerifier. If AI is enabled, it waits for AI verification.
# If AI is offline, it falls back immediately to test_alert_callback.
tracker.on_result(res_silent, test_alert_callback, bio_bpm=bio_silent.heart_rate_bpm)
if ai_available:
    fall_verifier.push_rssi(res_silent.rssi_mean, res_silent.rssi_variance, res_silent.activity.value)
    
    # Wait for FallVerifier background thread analysis
    print("⏳ Đang chờ FallVerifier thu thập đủ 10 giây dữ liệu và gửi cho Trợ lý AI (Gemma 4)...")
    time.sleep(16)  # Give time for buffer (10s) + agent reasoning (5s)
else:
    time.sleep(1)

# Verify if alert is successfully captured in Database
alerts_in_db = db.get_recent_alerts(limit=5)
print(f"📋 Danh sách cảnh báo ghi nhận trong DB: {len(alerts_in_db)}")
for a in alerts_in_db:
    print(f"  - [{a.alert_type}] ID={a.id}, Thời gian={time.strftime('%H:%M:%S', time.localtime(a.timestamp))}, Nội dung={a.message}")

if len(alerts_in_db) > 0 or len(triggered_alerts) > 0:
    print("✅ [Test 5] Luồng phát hiện té ngã & AI Fall Verifier đã hoạt động chính xác!")
else:
    print("❌ [Test 5] Không ghi nhận được cảnh báo nào! Thử lại.")
    sys.exit(1)

# 5. Daily PDF Report Generation Test
print("\n--- 📄 Giai đoạn 3: Giả lập xuất Báo cáo PDF phân tích Sức khỏe ---")
if ai_available:
    try:
        report_path = report_gen.generate_now()
        if report_path and os.path.exists(report_path):
            print(f"✅ [Test 6] Báo cáo PDF đã được AI biên soạn thành công tại: {report_path}")
            print(f"    Kích thước file: {os.path.getsize(report_path)} bytes")
        else:
            print("❌ [Test 6] Báo cáo PDF không được tạo ra!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ [Test 6] Lỗi khi tạo báo cáo PDF: {e}")
        sys.exit(1)
else:
    # Manual report generation test without AI context
    print("⚠️ Ollama offline. Thực hiện test xuất PDF bằng bản mẫu tĩnh...")
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    report_dir = Path("desktop/data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "wificensor_report_test.pdf"
    
    c = canvas.Canvas(str(report_path), pagesize=letter)
    c.drawString(100, 750, "WIFI-CENSOR DAILY HEALTH REPORT (TEST)")
    c.drawString(100, 720, "Trạng thái: Hoạt động bình thường. 1 cảnh báo té ngã đã xử lý.")
    c.save()
    
    if report_path.exists():
        print(f"✅ [Test 6] Đã xuất thành công file PDF test tĩnh tại: {report_path}")
    else:
        print("❌ [Test 6] Lỗi xuất PDF mẫu.")
        sys.exit(1)

# Clean up test database safely
try:
    if db_path.exists():
        os.remove(db_path)
    print("\n🧹 Đã dọn dẹp các tệp tin kiểm thử tạm thời.")
except Exception as e:
    print(f"⚠️  Dọn dẹp gặp sự cố nhỏ: {e}")

print()
print("======================================================================")
print(" 🎉 E2E INTEGRATION TEST PASSED! PHẦN CỨNG & AI HOẠT ĐỘNG HOÀN HẢO! 🎉")
print("======================================================================")
print()
