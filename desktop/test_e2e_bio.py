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
test_e2e_bio.py — Script kiểm thử tự động End-to-End luồng xử lý và đồng bộ sinh hiệu.
Kiểm tra từ tính toán dữ liệu suy luận Wi-Fi, tích hợp cảm biến thực tế, đến xuất JSON và đồng bộ.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add root folder to sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from desktop.app.config import get_config_manager
from desktop.app.database import Database
from desktop.app.presence_engine import PresenceResult, PresenceState, ActivityState
from desktop.app.exporter import JsonExporter
from desktop.app.bio_estimator import BioSignalResult

def print_step(title):
    print(f"\n=======================================================")
    print(f" >>> {title}")
    print(f"=======================================================")

def run_test():
    # Force UTF-8 encoding for standard output to support emojis/diacritics in Windows console
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("BẮT ĐẦU KIỂM THỬ END-TO-END HỆ THỐNG WIFISENSOR BIO-SIGNALS\n")

    # 1. Khởi tạo Database test tạm thời
    print_step("Bước 1: Khởi tạo cơ sở dữ liệu tạm thời")
    db_path = root_dir / "desktop" / "data" / "wificensor_test.db"
    if db_path.exists():
        db_path.unlink()
    
    print(f"Tạo cơ sở dữ liệu SQLite test tại: {db_path}")
    db = Database(str(db_path))

    # 2. Khởi tạo JsonExporter
    print_step("Bước 2: Cấu hình hệ thống xuất dữ liệu (Exporter)")
    cfg_manager = get_config_manager()
    # Ghi đè cấu hình để trỏ đến file test tạm thời
    test_json_path = root_dir / "desktop" / "data" / "wificensor_status_test.json"
    if test_json_path.exists():
        test_json_path.unlink()
    
    cfg_manager.update(
        json_export_enabled=True,
        json_export_path=str(test_json_path),
        github_sync_enabled=False # Tắt sync github thực để tránh đẩy rác lên repo khi test
    )
    print(f"Cấu hình đường dẫn xuất snapshot: {test_json_path}")
    
    exporter = JsonExporter(db)
    bio_estimator = exporter.bio_estimator

    # 3. Test Luồng Suy luận Wi-Fi (Chế độ mặc định - Mô phỏng / Suy luận sóng)
    print_step("Bước 3: Kiểm tra luồng suy luận gián tiếp từ tín hiệu Wi-Fi")
    
    # Tạo dữ liệu giả lập quét được người đang ngồi nghỉ ngơi (Stationary)
    # Gửi liên tục vài mẫu để làm đầy cửa sổ EMA
    print("Giả lập: Có 1 người đang nghỉ ngơi trong phòng (Tín hiệu Wi-Fi biến động nhẹ)...")
    for i in range(10):
        mock_result = PresenceResult(
            presence=PresenceState.PRESENT,
            activity=ActivityState.STATIONARY,
            confidence=0.85,
            dominant_bssid="aa:bb:cc:dd:ee:ff",
            rssi_mean=-52.0,
            rssi_variance=2.8 # Biến động nhẹ của người ngồi yên
        )
        # Thực hiện cập nhật và xuất snapshot
        exporter.export_snapshot(mock_result)
        time.sleep(0.05)

    # Đọc lại file JSON snapshot vừa xuất ra để verify cấu trúc
    print(f"Đọc file JSON snapshot: {test_json_path}")
    with open(test_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Verify các trường bio
    assert "heartRate" in data, "LỖI: Thiếu trường heartRate trong JSON snapshot!"
    assert "bodyTemp" in data, "LỖI: Thiếu trường bodyTemp trong JSON snapshot!"
    assert "peopleCount" in data, "LỖI: Thiếu trường peopleCount trong JSON snapshot!"
    assert "spo2" in data, "LỖI: Thiếu trường spo2 trong JSON snapshot!"

    print("\n[HỢP LỆ] Đã tìm thấy đầy đủ các trường dữ liệu sinh hiệu trong JSON snapshot!")
    print(f" - Nhịp tim ước tính: {data['heartRate']['bpm']} BPM (Độ tin cậy: {data['heartRate']['confidence']})")
    print(f" - Nhiệt độ cơ thể: {data['bodyTemp']['celsius']} °C (Nguồn suy luận: {data['bodyTemp']['basis']})")
    print(f" - Số người ước tính: {data['peopleCount']['count']} người (Độ tin cậy: {data['peopleCount']['confidence']})")
    print(f" - Trạng thái SpO2: {data['spo2']['percent']}% (Nguồn: {data['spo2']['source']})")

    assert data['heartRate']['estimated'] == True, "LỖI: Nhịp tim phải được đánh dấu là estimated=True khi dùng sóng Wi-Fi!"
    assert data['bodyTemp']['estimated'] == True, "LỖI: Nhiệt độ phải được đánh dấu là estimated=True khi dùng sóng Wi-Fi!"
    assert data['peopleCount']['count'] == 1, f"LỖI: Số người dự đoán sai! Kỳ vọng 1, nhận được {data['peopleCount']['count']}"

    print("\n[OK] Xác minh chế độ SUY LUẬN SÓNG WI-FI thành công!")

    # 4. Test Luồng Kết nối cảm biến y tế (MAX30102 / MLX90614)
    print_step("Bước 4: Kiểm tra luồng tích hợp cảm biến phần cứng trực tiếp (Sensor Mode)")
    print("Mô phỏng: Kết nối phần cứng thành công qua cổng Serial. Gửi dữ liệu sinh hiệu thực tế:")
    print(" - Nhịp tim (BPM) từ MAX30102: 78.5 BPM")
    print(" - Nồng độ SpO2 từ MAX30102: 98.0%")
    print(" - Nhiệt độ hồng ngoại từ MLX90614: 36.8 °C")

    # Inject dữ liệu cảm biến trực tiếp
    bio_estimator.inject_sensor_data(
        heart_rate=78.5,
        spo2=98.0,
        temperature=36.8
    )

    # Xuất lại snapshot
    mock_result_sensor = PresenceResult(
        presence=PresenceState.PRESENT,
        activity=ActivityState.STATIONARY,
        confidence=0.99,
        dominant_bssid="aa:bb:cc:dd:ee:ff",
        rssi_mean=-50.0,
        rssi_variance=3.0
    )
    exporter.export_snapshot(mock_result_sensor)

    # Đọc lại file JSON và verify
    with open(test_json_path, "r", encoding="utf-8") as f:
        data_sensor = json.load(f)

    print("\n[HỢP LỆ] Đọc dữ liệu sau khi kết nối cảm biến thành công!")
    print(f" - Nhịp tim thực tế: {data_sensor['heartRate']['bpm']} BPM (Nguồn cảm biến: {data_sensor['heartRate']['source']})")
    print(f" - Nhiệt độ thực tế: {data_sensor['bodyTemp']['celsius']} °C (Nguồn cảm biến: {data_sensor['bodyTemp']['source']})")
    print(f" - Nồng độ oxy SpO2: {data_sensor['spo2']['percent']}% (Nguồn cảm biến: {data_sensor['spo2']['source']})")

    assert data_sensor['heartRate']['bpm'] == 78.5, f"LỖI: Sai lệch nhịp tim cảm biến! Nhận được: {data_sensor['heartRate']['bpm']}"
    assert data_sensor['heartRate']['estimated'] == False, "LỖI: Nhịp tim cảm biến phải được đánh dấu estimated=False!"
    assert data_sensor['bodyTemp']['celsius'] == 36.8, f"LỖI: Sai lệch nhiệt độ cảm biến!"
    assert data_sensor['bodyTemp']['estimated'] == False, "LỖI: Nhiệt độ cảm biến phải được đánh dấu estimated=False!"
    assert data_sensor['spo2']['percent'] == 98.0, f"LỖI: Sai lệch nồng độ oxy cảm biến!"
    assert data_sensor['spo2']['estimated'] == False, "LỖI: SpO2 cảm biến phải được đánh dấu estimated=False!"

    print("\n[OK] Xác minh chế độ ĐO ĐẠC QUA CẢM BIẾN TRỰC TIẾP thành công!")

    # 5. Dọn dẹp dữ liệu kiểm thử
    print_step("Bước 5: Dọn dẹp môi trường kiểm thử")
    db.close()
    if db_path.exists():
        db_path.unlink()
    if test_json_path.exists():
        test_json_path.unlink()
    print("Đã xóa hoàn toàn các file cơ sở dữ liệu và JSON snapshot tạm thời.")
    
    print("\n=======================================================")
    print(" KẾT QUẢ: KIỂM THỬ END-TO-END THÀNH CÔNG RỰC RỠ 100%!")
    print("=======================================================")

if __name__ == "__main__":
    run_test()
