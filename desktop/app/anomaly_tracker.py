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
anomaly_tracker.py — Anomaly detection engine (immobility and fall detection).
Ports the Android algorithm (AnomalyTracker.kt) to Python.

MVP 2 Update: Tích hợp FallVerifier — thay vì trigger FALL ngay khi RSSI drop,
hệ thống bây giờ gửi context cho AI Agent để xác nhận trước khi báo động.
Fallback về hành vi MVP 1 nếu AI không sẵn sàng (trong 5 giây).
"""

import time
from typing import Callable, Optional
from desktop.app.presence_engine import PresenceResult, PresenceState, ActivityState
from desktop.app.config import get_config


class AnomalyTracker:
    def __init__(self):
        self.stationary_start_ms: Optional[int] = None
        self.last_presence = PresenceState.UNKNOWN
        self.last_transition_ms = 0
        self.is_started = False
        self.suppress_until_ms = 0
        self._fall_verifier = None   # Được set bởi app_window sau khi AI Agent sẵn sàng

    def set_fall_verifier(self, verifier) -> None:
        """
        Kết nối FallVerifier vào tracker.
        Gọi từ app_window.py sau khi AI Agent được khởi tạo.
        """
        self._fall_verifier = verifier

    def start(self):
        self.is_started = True
        self.stationary_start_ms = None
        self.last_presence = PresenceState.UNKNOWN
        self.last_transition_ms = int(time.time() * 1000)
        self.suppress_until_ms = 0

    def on_result(self, result: PresenceResult, on_alert: Callable[[str, str, str], None],
                  bio_bpm: Optional[float] = None):
        """
        Processes new PresenceResult.
        Calls on_alert(alert_type, title, message) when anomaly is detected.
        alert_type: "IMMOBILITY" | "FALL"

        Args:
            result: Kết quả phân tích presence
            on_alert: Callback khi có cảnh báo
            bio_bpm: Nhịp tim ước tính (từ BioEstimator) — dùng để AI phân tích context fall
        """
        if not self.is_started:
            return

        now = int(time.time() * 1000)
        cfg = get_config()

        # ── Immobility Detection ─────────────────────────────────────
        # Triggers when room is PRESENT and state is STATIONARY or SLEEPING
        is_inactive = (result.presence == PresenceState.PRESENT and
                       result.activity in (ActivityState.STATIONARY, ActivityState.SLEEPING))

        if is_inactive:
            if self.stationary_start_ms is None:
                self.stationary_start_ms = now

            stationary_duration_ms = now - self.stationary_start_ms
            threshold_ms = cfg.immobility_threshold_min * 60 * 1000

            if stationary_duration_ms >= threshold_ms and now > self.suppress_until_ms:
                minutes = int(stationary_duration_ms / 60000)
                title = "⚠️ Bất động quá lâu"
                message = f"Phát hiện bất động {minutes} phút. Vui lòng kiểm tra."
                on_alert("IMMOBILITY", title, message)
                # Suppress next immobility alert for 15 minutes
                self.suppress_until_ms = now + 15 * 60 * 1000
        else:
            self.stationary_start_ms = None

        # ── Rapid Transition Fall Detection ──────────────────────────
        time_since_last_transition = now - self.last_transition_ms
        just_went_absent = (self.last_presence == PresenceState.PRESENT and
                            result.presence == PresenceState.ABSENT)

        if just_went_absent and time_since_last_transition < 3000:
            if self._fall_verifier is not None and cfg.ai_enabled:
                # MVP 2: Gửi cho AI xác nhận trước — KHÔNG trigger ngay
                self._fall_verifier.on_suspected_fall(
                    variance_at_drop=result.rssi_variance,
                    activity_before=self.last_presence.value,
                    bio_bpm=bio_bpm,
                    alert_callback=on_alert,
                )
            else:
                # Fallback MVP 1: Trigger ngay (AI chưa sẵn sàng hoặc bị tắt)
                title = "🔴 Nghi ngờ té ngã"
                message = "Tín hiệu biến mất đột ngột. Có thể đã xảy ra té ngã!"
                on_alert("FALL", title, message)

        # ── Transition Tracking ───────────────────────────────────────
        if result.presence != self.last_presence:
            self.last_transition_ms = now
            self.last_presence = result.presence
