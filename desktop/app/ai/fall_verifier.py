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
fall_verifier.py — Xác nhận té ngã bằng AI để giảm false positive.

Luồng hoạt động:
  1. AnomalyTracker phát hiện RSSI drop đột ngột → gọi FallVerifier.on_suspected_fall()
  2. FallVerifier thu thập buffer RSSI 10 giây sau khi drop
  3. Gửi toàn bộ context cho AI Agent để phán quyết
  4. AI trả về: "fall" | "false_alarm" | "uncertain"
  5. Chỉ khi AI xác nhận "fall" hoặc timeout 5s → trigger cảnh báo thực

Timeout fallback: Nếu AI không trả lời trong 5 giây → kích hoạt cảnh báo ngay
để không bao giờ bỏ sót té ngã thực.
"""

import time
import threading
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from desktop.app.ai.agent import WifiCensorAgent


@dataclass
class FallCandidate:
    """Dữ liệu context xung quanh một sự kiện nghi ngờ té ngã."""
    timestamp: float
    rssi_before: List[float]         # 5 samples trước drop (10s)
    variance_before: float
    variance_after_peak: float       # Variance tại thời điểm drop
    activity_before: str             # WALKING / STATIONARY / SLEEPING
    bio_bpm: Optional[float]         # Nhịp tim ước tính lúc đó
    hour_of_day: int                 # Giờ trong ngày (3h sáng nguy hiểm hơn)
    rssi_after: List[float] = field(default_factory=list)   # Được điền sau 10s


class FallVerifier:
    """
    Xác nhận sự kiện té ngã bằng AI trước khi gửi cảnh báo chính thức.
    Thay thế trigger cứng trong AnomalyTracker.
    """

    BUFFER_DURATION_S = 10   # Thu thập thêm 10s RSSI sau khi drop
    AI_TIMEOUT_S = 5         # Timeout AI phán quyết — fallback kích hoạt ngay
    RSSI_BUFFER_SIZE = 30    # Số samples giữ trong sliding buffer

    def __init__(self):
        self._rssi_buffer: deque = deque(maxlen=self.RSSI_BUFFER_SIZE)
        self._pending: Optional[FallCandidate] = None
        self._lock = threading.Lock()
        self._agent: Optional["WifiCensorAgent"] = None
        self._alert_callback: Optional[Callable] = None

    def set_agent(self, agent: "WifiCensorAgent") -> None:
        """Kết nối AI Agent vào verifier."""
        self._agent = agent

    def set_alert_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """
        Đặt callback để gửi cảnh báo khi AI xác nhận fall.
        Signature: callback(alert_type, title, message)
        """
        self._alert_callback = callback

    def push_rssi(self, rssi: float, variance: float, activity: str) -> None:
        """
        Gọi mỗi lần có kết quả scan mới để duy trì sliding buffer.
        Phải được gọi từ poll_scanner() trong app_window.py.
        """
        with self._lock:
            self._rssi_buffer.append({
                "rssi": rssi,
                "variance": variance,
                "activity": activity,
                "ts": time.time()
            })

            # Nếu đang chờ thu thập buffer sau drop — thêm vào rssi_after
            if self._pending is not None:
                elapsed = time.time() - self._pending.timestamp
                if elapsed <= self.BUFFER_DURATION_S:
                    self._pending.rssi_after.append(rssi)

    def on_suspected_fall(
        self,
        variance_at_drop: float,
        activity_before: str,
        bio_bpm: Optional[float],
        alert_callback: Callable
    ) -> None:
        """
        Được gọi bởi AnomalyTracker khi phát hiện RSSI drop nghi ngờ.
        Bắt đầu quá trình xác nhận AI — KHÔNG trigger ngay.
        """
        with self._lock:
            if self._pending is not None:
                # Đã có sự kiện đang chờ xử lý — bỏ qua
                return

            # Lấy 5 samples RSSI gần nhất trước drop
            recent = list(self._rssi_buffer)
            rssi_before = [s["rssi"] for s in recent[-5:]]
            avg_var_before = (
                sum(s["variance"] for s in recent[-5:]) / len(recent[-5:])
                if recent else variance_at_drop
            )

            candidate = FallCandidate(
                timestamp=time.time(),
                rssi_before=rssi_before,
                variance_before=avg_var_before,
                variance_after_peak=variance_at_drop,
                activity_before=activity_before,
                bio_bpm=bio_bpm,
                hour_of_day=time.localtime().tm_hour,
            )
            self._pending = candidate

        self._alert_callback = alert_callback

        # Bắt đầu timer: thu thập 10s rồi gửi AI phán quyết
        timer = threading.Timer(self.BUFFER_DURATION_S, self._analyze_candidate)
        timer.daemon = True
        timer.start()

    def _analyze_candidate(self) -> None:
        """
        Được gọi sau BUFFER_DURATION_S giây.
        Gửi context cho AI và chờ phán quyết với timeout.
        """
        with self._lock:
            candidate = self._pending
            self._pending = None

        if candidate is None:
            return

        # Nếu không có AI agent → fallback kích hoạt ngay
        if self._agent is None or not hasattr(self._agent, 'ask_sync'):
            print("[FallVerifier] Không có AI agent — fallback trigger ngay.")
            self._do_trigger()
            return

        # Xây dựng prompt phân tích
        hour = candidate.hour_of_day
        time_risk = "cao (ban đêm)" if 0 <= hour < 6 else "bình thường"

        prompt = f"""Phân tích sự kiện nghi ngờ té ngã xảy ra lúc {hour}:00 (rủi ro theo giờ: {time_risk}).

Dữ liệu sóng Wi-Fi:
- RSSI trước sự kiện (5 mẫu cuối): {candidate.rssi_before} dBm
- Độ biến động sóng trước: {candidate.variance_before:.3f}
- Độ biến động sóng tại thời điểm drop: {candidate.variance_after_peak:.3f}
- RSSI sau sự kiện (10 giây): {candidate.rssi_after if candidate.rssi_after else "Không có tín hiệu"} dBm

Trạng thái hoạt động trước: {candidate.activity_before}
Nhịp tim ước tính: {f"{candidate.bio_bpm:.1f} BPM" if candidate.bio_bpm else "Không có dữ liệu"}

Căn cứ trên các chỉ số trên, hãy phán quyết:
- Nếu tín hiệu biến mất hoàn toàn sau drop và KHÔNG phục hồi trong 10s → khả năng cao là té ngã thực
- Nếu tín hiệu phục hồi nhanh (RSSI after có giá trị) → có thể là đặt đồ xuống, cúi người hoặc nhiễu
- Nếu variance_after_peak rất cao (>20) → biến động mạnh trước khi biến mất → khả năng cao là té ngã

Chỉ trả lời MỘT trong ba từ sau (không giải thích thêm):
fall | false_alarm | uncertain"""

        # Gọi AI với timeout
        result = {"verdict": None}
        done_event = threading.Event()

        def _ask():
            try:
                answer = self._agent.ask_sync(
                    prompt,
                    system_override=(
                        "Bạn là hệ thống phân tích dữ liệu y tế. "
                        "Trả lời ngắn gọn, chỉ một từ trong số: fall, false_alarm, uncertain."
                    )
                )
                # Normalize kết quả
                answer = answer.strip().lower()
                if "false" in answer or "false_alarm" in answer:
                    result["verdict"] = "false_alarm"
                elif "uncertain" in answer:
                    result["verdict"] = "uncertain"
                else:
                    result["verdict"] = "fall"
            except Exception as e:
                print(f"[FallVerifier] AI error: {e}")
                result["verdict"] = "fall"  # Fail-safe: nếu lỗi → kích hoạt
            finally:
                done_event.set()

        ai_thread = threading.Thread(target=_ask, daemon=True)
        ai_thread.start()

        # Chờ AI trong giới hạn timeout
        ai_answered = done_event.wait(timeout=self.AI_TIMEOUT_S)

        if not ai_answered:
            print("[FallVerifier] AI timeout — fallback kích hoạt cảnh báo.")
            result["verdict"] = "fall"

        verdict = result["verdict"]
        print(f"[FallVerifier] AI phán quyết: {verdict}")

        if verdict == "fall":
            self._do_trigger()
        elif verdict == "uncertain":
            # Uncertain → gửi cảnh báo nhẹ hơn (IMMOBILITY thay vì FALL)
            if self._alert_callback:
                self._alert_callback(
                    "IMMOBILITY",
                    "⚠️ Nghi ngờ té ngã (chưa xác định)",
                    "AI phát hiện sự kiện bất thường nhưng chưa xác định được. Vui lòng kiểm tra ngay."
                )
        else:
            print("[FallVerifier] AI xác nhận: Báo động giả — bỏ qua.")

    def _do_trigger(self) -> None:
        """Kích hoạt cảnh báo té ngã chính thức."""
        if self._alert_callback:
            self._alert_callback(
                "FALL",
                "🔴 Nghi ngờ té ngã",
                "AI đã xác nhận: Tín hiệu biến mất đột ngột. Có thể đã xảy ra té ngã! Kiểm tra ngay!"
            )
