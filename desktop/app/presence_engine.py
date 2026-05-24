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
presence_engine.py — Presence Detection Engine using RSSI Variance.
Ports the Android algorithm (PresenceEngine.kt) to Python.
"""

import time
from collections import deque
from enum import Enum
from typing import List, Optional
from desktop.app.scanner import WifiNetwork
from desktop.app.config import get_config, get_config_manager


class PresenceState(Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"


class ActivityState(Enum):
    WALKING = "WALKING"
    STATIONARY = "STATIONARY"
    SLEEPING = "SLEEPING"
    MOVING = "MOVING"
    UNKNOWN = "UNKNOWN"


class PresenceResult:
    def __init__(self, presence: PresenceState, activity: ActivityState, confidence: float, rssi_variance: float, rssi_mean: float, dominant_bssid: str):
        self.presence = presence
        self.activity = activity
        self.confidence = confidence  # 0.0 to 1.0
        self.rssi_variance = rssi_variance
        self.rssi_mean = rssi_mean
        self.dominant_bssid = dominant_bssid

    def to_dict(self) -> dict:
        return {
            "presence": self.presence.value,
            "activity": self.activity.value,
            "confidence": self.confidence,
            "rssi_variance": self.rssi_variance,
            "rssi_mean": self.rssi_mean,
            "dominant_bssid": self.dominant_bssid
        }


class PresenceEngine:
    MIN_SAMPLES = 8

    def __init__(self):
        self.window_ms = 30_000  # 30-second window
        self.rssi_window = deque()  # stores (timestamp_ms, rssi)

        # Loaded from config
        self._load_config()

        self.calib_samples = []

    def _load_config(self):
        cfg = get_config()
        self.baseline_variance = cfg.baseline_variance if cfg.is_calibrated else 0.5
        self.calibrated = cfg.is_calibrated
        self.calibration_samples_required = cfg.calibration_samples
        self.sensitivity = cfg.sensitivity

        # Threshold multipliers (scaled by sensitivity)
        # Standard: presence = 3.0, moving = 8.0
        # If sensitivity > 1.0, thresholds decrease (easier to detect presence/movement)
        # If sensitivity < 1.0, thresholds increase (harder to detect)
        self.presence_threshold_multiplier = 3.0 / self.sensitivity
        self.moving_threshold_multiplier = 8.0 / self.sensitivity

    def process(self, scan_list: List[WifiNetwork]) -> PresenceResult:
        self._load_config()  # Dynamic config reload
        now_ms = int(time.time() * 1000)

        # Pick the target AP if configured, otherwise pick the strongest AP
        cfg = get_config()
        best: Optional[WifiNetwork] = None
        if cfg.target_bssid:
            for net in scan_list:
                if net.bssid.lower() == cfg.target_bssid.lower():
                    best = net
                    break
        
        # Fallback to strongest AP if no target or target AP not in list
        if best is None and scan_list:
            best = max(scan_list, key=lambda x: x.rssi)

        if best is None:
            return PresenceResult(PresenceState.UNKNOWN, ActivityState.UNKNOWN, 0.0, 0.0, 0.0, "")

        # Add to window
        self.rssi_window.append((now_ms, best.rssi))

        # Prune old samples outside the window
        while self.rssi_window and (now_ms - self.rssi_window[0][0]) > self.window_ms:
            self.rssi_window.popleft()

        # Need minimum samples
        if len(self.rssi_window) < self.MIN_SAMPLES:
            return PresenceResult(PresenceState.UNKNOWN, ActivityState.UNKNOWN, 0.0, 0.0, float(best.rssi), best.bssid)

        values = [float(x[1]) for x in self.rssi_window]
        mean = sum(values) / len(values)
        variance = self._compute_variance(values, mean)

        # Calibration phase: first N samples with no movement
        if not self.calibrated:
            self.calib_samples.append(variance)
            if len(self.calib_samples) >= self.calibration_samples_required:
                avg_var = sum(self.calib_samples) / len(self.calib_samples)
                self.baseline_variance = max(avg_var, 0.1)
                self.calibrated = True
                self.calib_samples.clear()
                # Save to config!
                get_config_manager().update(
                    baseline_variance=self.baseline_variance,
                    is_calibrated=True
                )
            return PresenceResult(PresenceState.UNKNOWN, ActivityState.UNKNOWN, 0.0, variance, mean, best.bssid)

        # Determine presence and activity
        presence_thresh = self.baseline_variance * self.presence_threshold_multiplier
        moving_thresh = self.baseline_variance * self.moving_threshold_multiplier
        # Ngưỡng phát hiện ngủ/nghỉ ngơi tĩnh lặng siêu nhạy
        sleep_thresh = self.baseline_variance * (1.2 / self.sensitivity)

        if variance >= moving_thresh:
            presence = PresenceState.PRESENT
            activity = ActivityState.WALKING
            confidence = self._compute_confidence(variance, moving_thresh, moving_thresh * 3.0)
        elif variance >= presence_thresh:
            presence = PresenceState.PRESENT
            activity = ActivityState.STATIONARY
            confidence = self._compute_confidence(variance, presence_thresh, moving_thresh)
            
            # Detect possible sleep (very low RSSI variance but present for a long time)
            if variance < presence_thresh * 1.5:
                activity = ActivityState.SLEEPING
        elif variance >= sleep_thresh:
            presence = PresenceState.PRESENT
            activity = ActivityState.SLEEPING
            confidence = self._compute_confidence(variance, sleep_thresh, presence_thresh)
        else:
            presence = PresenceState.ABSENT
            activity = ActivityState.UNKNOWN
            confidence = self._compute_confidence(sleep_thresh - variance, 0.0, sleep_thresh)

        # Coerce confidence between 0.3 and 0.99
        confidence = max(0.3, min(0.99, confidence))

        return PresenceResult(
            presence=presence,
            activity=activity,
            confidence=confidence,
            rssi_variance=variance,
            rssi_mean=mean,
            dominant_bssid=best.bssid
        )

    def calibration_progress(self) -> float:
        if self.calibrated:
            return 1.0
        if not self.calibration_samples_required:
            return 0.0
        return len(self.calib_samples) / self.calibration_samples_required

    def recalibrate(self):
        self.calibrated = False
        self.calib_samples.clear()
        self.rssi_window.clear()
        get_config_manager().update(is_calibrated=False, baseline_variance=0.0)

    def set_baseline(self, variance: float):
        self.baseline_variance = max(variance, 0.1)
        self.calibrated = True
        self.calib_samples.clear()
        get_config_manager().update(is_calibrated=True, baseline_variance=self.baseline_variance)

    def _compute_variance(self, values: List[float], mean: float) -> float:
        if len(values) < 2:
            return 0.0
        sum_sq = sum((x - mean) ** 2 for x in values)
        return sum_sq / len(values)

    def _compute_confidence(self, value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.5
        val = (value - low) / (high - low)
        return max(0.0, min(1.0, val))
