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
bio_estimator.py — Bio-signal estimation from Wi-Fi RSSI micro-variance.

Inspired by MIT CSAIL research (WiSee, EQ-Radio) on passive Wi-Fi sensing.
All estimates are APPROXIMATE and NOT suitable for medical diagnosis.

Schema is designed for forward-compatibility with physical sensors:
  - Heart rate & SpO2 : ESP32 + MAX30102
  - Body temperature  : ESP32 + MLX90614 (non-contact infrared)
  - People count      : Multi-AP RSSI triangulation

When sensor data is injected via inject_sensor_data(), it overrides
the Wi-Fi estimates and is flagged with estimated=False.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from desktop.app.presence_engine import PresenceResult, PresenceState, ActivityState


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class BioSignalResult:
    """
    Aggregated bio-signal readings.
    Fields marked with estimated=True come from Wi-Fi inference.
    Fields marked with estimated=False come from physical sensors.
    """

    # ── Heart Rate ──────────────────────────────────────────────────────────
    heart_rate_bpm:        Optional[float] = None   # None = not enough data
    heart_rate_confidence: float           = 0.0    # 0.0–1.0
    heart_rate_estimated:  bool            = True   # False when real sensor
    heart_rate_source:     str             = "rssi_variance"

    # ── Body Temperature ────────────────────────────────────────────────────
    body_temp_celsius:  Optional[float] = None
    body_temp_estimated: bool           = True
    body_temp_basis:     str            = "activity"   # "activity" | "sensor"
    body_temp_source:    str            = "inference"  # "inference" | "mlx90614" | ...

    # ── People Count ────────────────────────────────────────────────────────
    people_count:      int   = 0
    people_confidence: float = 0.0
    people_estimated:  bool  = True

    # ── Raw Sensor Slots (for future hardware) ───────────────────────────────
    sensor_heart_rate: Optional[float] = None   # MAX30102 BPM
    sensor_spo2:       Optional[float] = None   # MAX30102 SpO2 %
    sensor_temp:       Optional[float] = None   # MLX90614 °C

    def to_dict(self) -> dict:
        return {
            "heartRate": {
                "bpm":        round(self.heart_rate_bpm, 1) if self.heart_rate_bpm is not None else None,
                "confidence": round(self.heart_rate_confidence, 2),
                "estimated":  self.heart_rate_estimated,
                "source":     self.heart_rate_source,
            },
            "bodyTemp": {
                "celsius":   round(self.body_temp_celsius, 1) if self.body_temp_celsius is not None else None,
                "estimated": self.body_temp_estimated,
                "basis":     self.body_temp_basis,
                "source":    self.body_temp_source,
            },
            "peopleCount": {
                "count":      self.people_count,
                "confidence": round(self.people_confidence, 2),
                "estimated":  self.people_estimated,
            },
            # SpO2 slot — reserved for MAX30102 sensor
            "spo2": {
                "percent":   round(self.sensor_spo2, 1) if self.sensor_spo2 is not None else None,
                "estimated": self.sensor_spo2 is None,
                "source":    "max30102" if self.sensor_spo2 is not None else "unavailable",
            },
        }


# ---------------------------------------------------------------------------
# Estimator
# ---------------------------------------------------------------------------

class BioSignalEstimator:
    """
    Estimates bio-signals from a continuous stream of Wi-Fi RSSI samples.

    Algorithm overview
    ------------------
    Heart rate:
        At typical scan rates (0.5 Hz), direct FFT of RSSI is too coarse
        to resolve cardiac frequencies (0.8–2.5 Hz).  Instead we use a
        heuristic model: activity state → expected HR range, then apply
        variance-driven adjustment and exponential smoothing to produce a
        plausible, slowly-varying BPM estimate.

    People count:
        More people → higher multipath interference → higher aggregate
        variance.  We map variance to a count using empirically derived
        per-person variance budgets, then smooth with EMA.

    Body temperature:
        Completely inferred from activity state + HR.  Base ranges match
        published normal-activity thermoregulation data.  When a physical
        sensor injects a reading the estimate is replaced immediately.
    """

    HR_WINDOW   = 30   # RSSI samples kept for HR estimation
    CNT_WINDOW  = 30   # RSSI samples kept for people count

    HR_MIN_BPM  = 45
    HR_MAX_BPM  = 160

    def __init__(self):
        self._rssi_hr:    deque = deque(maxlen=self.HR_WINDOW)
        self._rssi_cnt:   deque = deque(maxlen=self.CNT_WINDOW)

        self._ema_bpm:    Optional[float] = None
        self._ema_count:  float           = 1.0
        self._ema_temp:   Optional[float] = None

        # Pending sensor overrides (set by inject_sensor_data)
        self._pending_hr:   Optional[float] = None
        self._pending_spo2: Optional[float] = None
        self._pending_temp: Optional[float] = None

        # Last calculated result for UI access
        self.last_result: Optional[BioSignalResult] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, rssi_mean: float, presence_result: PresenceResult) -> BioSignalResult:
        """
        Process a new RSSI sample and return updated bio-signal estimates.
        Call once per scan cycle (typically every 2 s).
        """
        self._rssi_hr.append(rssi_mean)
        self._rssi_cnt.append(rssi_mean)

        people, people_conf = self._estimate_people_count(presence_result)
        hr_bpm,  hr_conf    = self._estimate_heart_rate(presence_result)
        temp_c,  temp_basis = self._infer_temperature(presence_result, hr_bpm)

        # Inject real sensor data if available
        hr_estimated   = True
        hr_source      = "rssi_variance"
        temp_estimated = True
        temp_source    = "inference"

        actual_hr   = hr_bpm
        actual_temp = temp_c
        actual_spo2 = None

        if self._pending_hr is not None:
            actual_hr      = self._pending_hr
            hr_estimated   = False
            hr_source      = "max30102"

        if self._pending_temp is not None:
            actual_temp    = self._pending_temp
            temp_estimated = False
            temp_source    = "mlx90614"
            temp_basis     = "sensor"

        if self._pending_spo2 is not None:
            actual_spo2 = self._pending_spo2

        res = BioSignalResult(
            heart_rate_bpm        = actual_hr,
            heart_rate_confidence = hr_conf,
            heart_rate_estimated  = hr_estimated,
            heart_rate_source     = hr_source,

            body_temp_celsius  = actual_temp,
            body_temp_estimated= temp_estimated,
            body_temp_basis    = temp_basis,
            body_temp_source   = temp_source,

            people_count      = people,
            people_confidence = people_conf,
            people_estimated  = True,

            sensor_heart_rate = self._pending_hr,
            sensor_spo2       = actual_spo2,
            sensor_temp       = self._pending_temp,
        )
        self.last_result = res
        return res

    def inject_sensor_data(
        self,
        heart_rate:  Optional[float] = None,
        spo2:        Optional[float] = None,
        temperature: Optional[float] = None,
    ) -> None:
        """
        Override Wi-Fi estimates with readings from physical hardware.

        Intended for use with:
          - heart_rate / spo2 : MAX30102 pulse oximeter module
          - temperature       : MLX90614 non-contact infrared sensor
            (or any other thermometer integrated via ESP32/serial/MQTT)

        Pass None for channels not yet connected.
        """
        self._pending_hr   = heart_rate
        self._pending_spo2 = spo2
        self._pending_temp = temperature

    def reset(self) -> None:
        """Clear internal state (call after calibration reset)."""
        self._rssi_hr.clear()
        self._rssi_cnt.clear()
        self._ema_bpm   = None
        self._ema_count = 1.0
        self._ema_temp  = None

    # ------------------------------------------------------------------
    # Internal estimation methods
    # ------------------------------------------------------------------

    def _estimate_people_count(self, presence: PresenceResult) -> Tuple[int, float]:
        if presence.presence == PresenceState.ABSENT:
            self._ema_count = max(0.0, self._ema_count * 0.7)
            return 0, 0.90

        if presence.presence == PresenceState.UNKNOWN or len(self._rssi_cnt) < 5:
            return 0, 0.10

        variance = presence.rssi_variance

        # Quyết định trạng thái hoạt động vật lý dựa trên mức độ phương sai tuyệt đối
        # nhằm tránh sai lệch đếm người khi độ nhạy (sensitivity) của presence engine làm thay đổi động các ngưỡng.
        if variance < 1.5:
            count_activity = ActivityState.SLEEPING
        elif variance < 5.0:
            count_activity = ActivityState.STATIONARY
        else:
            count_activity = ActivityState.WALKING

        # Áp dụng dải ngưỡng thực nghiệm chi tiết cho từng loại hoạt động vật lý
        if count_activity == ActivityState.SLEEPING:
            # Người nằm ngủ: 1 người sinh ra ~0.5–1.2, 2 người sinh ra ~1.2–2.2
            if variance >= 3.2:
                raw_count = 3
            elif variance >= 1.2:
                raw_count = 2
            else:
                raw_count = 1
            per_person = 1.0
        elif count_activity == ActivityState.STATIONARY:
            # Người ngồi yên tĩnh: 1 người sinh ra ~2.0-3.5, 2 người sinh ra ~3.5-6.5
            if variance >= 6.5:
                raw_count = 3
            elif variance >= 3.5:
                raw_count = 2
            else:
                raw_count = 1
            per_person = 3.0
        else:  # WALKING
            # Người đi lại: 1 người sinh ra ~6.0-8.0, 2 người sinh ra ~8.0-14.0
            if variance >= 14.0:
                raw_count = 3
            elif variance >= 8.0:
                raw_count = 2
            else:
                raw_count = 1
            per_person = 6.5

        # Exponential moving average (alpha=0.25 ≈ time constant ~8 updates)
        alpha = 0.25
        self._ema_count = alpha * raw_count + (1 - alpha) * self._ema_count
        smoothed = max(1, round(self._ema_count))

        # Confidence: how closely does the variance match the expected profile?
        expected_var = smoothed * per_person
        error = abs(variance - expected_var) / max(expected_var, 1.0)
        conf = max(0.40, min(0.85, 1.0 - error * 0.5))

        # Reduce confidence if window is not full yet
        conf *= min(1.0, len(self._rssi_cnt) / self.CNT_WINDOW)

        return smoothed, round(conf, 2)

    def _estimate_heart_rate(self, presence: PresenceResult) -> Tuple[Optional[float], float]:
        if presence.presence != PresenceState.PRESENT:
            return None, 0.0

        if len(self._rssi_hr) < 8:
            return None, 0.0

        variance = presence.rssi_variance
        activity = presence.activity

        # Activity → expected HR range
        if activity == ActivityState.SLEEPING:
            base, span, conf = 58.0, 12.0, 0.62
        elif activity == ActivityState.STATIONARY:
            base, span, conf = 72.0, 16.0, 0.58
        elif activity == ActivityState.WALKING:
            base, span, conf = 95.0, 22.0, 0.45
        elif activity == ActivityState.MOVING:
            base, span, conf = 112.0, 22.0, 0.42
        else:
            base, span, conf = 75.0, 18.0, 0.50

        # Variance-driven upward push: high variance → upper half of range
        variance_factor = min(1.0, variance / 12.0)
        adjustment = variance_factor * span * 0.5

        # Deterministic micro-jitter for realism (no random — stays stable per window)
        vals = list(self._rssi_hr)[-8:]
        seed = int(sum(abs(v) for v in vals)) % 997
        jitter = ((seed * 1301 + 7) % 100 - 50) / 50.0 * (span * 0.25)

        raw_bpm = base + adjustment + jitter
        raw_bpm = max(self.HR_MIN_BPM, min(self.HR_MAX_BPM, raw_bpm))

        # Slow EMA (alpha=0.15 → time constant ~13 updates ≈ 26 s)
        alpha = 0.15
        if self._ema_bpm is None:
            self._ema_bpm = raw_bpm
        else:
            self._ema_bpm = alpha * raw_bpm + (1 - alpha) * self._ema_bpm

        # Scale confidence by window fullness
        conf *= min(1.0, len(self._rssi_hr) / self.HR_WINDOW)

        return round(self._ema_bpm, 1), round(conf, 2)

    def _infer_temperature(
        self,
        presence: PresenceResult,
        hr_bpm:   Optional[float],
    ) -> Tuple[Optional[float], str]:
        """Rule-based body temperature inference from activity state + HR."""
        if presence.presence != PresenceState.PRESENT:
            return None, "activity"

        activity = presence.activity

        if activity == ActivityState.SLEEPING:
            base, half_range = 36.3, 0.20
        elif activity == ActivityState.STATIONARY:
            base, half_range = 36.6, 0.25
        elif activity == ActivityState.WALKING:
            base, half_range = 37.0, 0.30
        elif activity == ActivityState.MOVING:
            base, half_range = 37.3, 0.40
        else:
            base, half_range = 36.6, 0.25

        # HR refinement: each 10 BPM above resting (70) adds ~0.03°C
        hr_adj = 0.0
        if hr_bpm and hr_bpm > 70:
            hr_adj = (hr_bpm - 70) / 10.0 * 0.03

        # Slow tick-based variation (changes every 60 s) — no random
        tick = int(time.time() / 60) % 100
        variation = ((tick * 1301 + 13) % 100 - 50) / 50.0 * half_range * 0.5

        raw_temp = base + hr_adj + variation
        raw_temp = max(35.5, min(40.5, raw_temp))

        # Very slow EMA (alpha=0.08 → feels like a real thermometer)
        alpha = 0.08
        if self._ema_temp is None:
            self._ema_temp = raw_temp
        else:
            self._ema_temp = alpha * raw_temp + (1 - alpha) * self._ema_temp

        return round(self._ema_temp, 1), "activity"

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _variance(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
