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
scanner.py — Wi-Fi RSSI scanner for Windows.

Strategy:
  1. Try pywifi (works without admin on some configs)
  2. Fallback: netsh wlan show networks (needs admin or Location Services)
  3. If both fail: Demo Mode with realistic synthetic RSSI data
"""

import subprocess
import re
import time
import threading
import queue
import math
import random
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum


class ScannerMode(Enum):
    REAL_PYWIFI = "pywifi"
    REAL_NETSH = "netsh"
    DEMO = "demo"


@dataclass
class WifiNetwork:
    ssid: str
    bssid: str
    rssi: int       # dBm, e.g. -65
    signal: int     # 0-100%
    frequency: int = 2400  # MHz


class WifiScanner:
    """
    Scans Wi-Fi networks and streams results to a queue.
    Auto-detects the best available method.
    """

    def __init__(self, interval_sec: float = 2.0):
        self.interval_sec = interval_sec
        self._queue: queue.Queue[list[WifiNetwork]] = queue.Queue(maxsize=50)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._mode = ScannerMode.DEMO
        self._error_message: str = ""
        self._demo_state = _DemoState()
        self._consecutive_failures = 0

        # Silence third-party pywifi logging completely (prevent propagation and remove active handlers)
        import logging
        pywifi_logger = logging.getLogger("pywifi")
        pywifi_logger.setLevel(logging.CRITICAL)
        pywifi_logger.propagate = False
        for h in list(pywifi_logger.handlers):
            pywifi_logger.removeHandler(h)

        # Detect best scanner
        self._mode = self._detect_mode()

    def _detect_mode(self) -> ScannerMode:
        # Try pywifi
        try:
            import pywifi  # noqa: F401
            import comtypes  # noqa: F401
            wifi = pywifi.PyWiFi()
            iface = wifi.interfaces()[0]
            iface.scan()
            time.sleep(0.5)
            results = iface.scan_results()
            if results is not None:
                return ScannerMode.REAL_PYWIFI
        except Exception:
            pass

        # Try netsh
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, text=True, timeout=5, encoding="utf-8",
                errors="replace", creationflags=0x08000000
            )
            if "SSID" in result.stdout and "Signal" in result.stdout:
                return ScannerMode.REAL_NETSH
            self._error_message = result.stdout[:200]
        except Exception as e:
            self._error_message = str(e)

        return ScannerMode.DEMO

    @property
    def mode(self) -> ScannerMode:
        return self._mode

    @property
    def is_demo(self) -> bool:
        return self._mode == ScannerMode.DEMO

    @property
    def error_message(self) -> str:
        return self._error_message

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def get_latest(self, timeout: float = 0.1) -> Optional[list[WifiNetwork]]:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _scan_loop(self):
        while not self._stop_event.is_set():
            networks = []
            try:
                if self._mode == ScannerMode.REAL_PYWIFI:
                    networks = self._scan_pywifi()
                    self._consecutive_failures = 0
                elif self._mode == ScannerMode.REAL_NETSH:
                    networks = self._scan_netsh()
                    self._consecutive_failures = 0
                else:
                    networks = self._scan_demo()
            except Exception as e:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 3 and self._mode != ScannerMode.DEMO:
                    from desktop.app.logger import get_logger
                    fallback_logger = get_logger("scanner")
                    fallback_logger.warning(
                        f"Thiết bị Wi-Fi gặp sự cố liên tục ({e}). "
                        f"Hệ thống tự động chuyển sang chế độ mô phỏng (Demo Mode) để duy trì hoạt động an toàn."
                    )
                    self._mode = ScannerMode.DEMO
                networks = self._scan_demo()

            if networks:
                # Drop oldest if full
                if self._queue.full():
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass
                self._queue.put(networks)

            self._stop_event.wait(self.interval_sec)

    def _scan_pywifi(self) -> list[WifiNetwork]:
        import pywifi
        wifi = pywifi.PyWiFi()
        iface = wifi.interfaces()[0]
        iface.scan()
        time.sleep(0.3)
        results = iface.scan_results()
        networks = []
        for r in results:
            rssi = int(r.signal)
            signal = _rssi_to_signal(rssi)
            ssid = r.ssid or "<hidden>"
            bssid = r.bssid or ""
            networks.append(WifiNetwork(ssid=ssid, bssid=bssid,
                                        rssi=rssi, signal=signal))
        return networks

    def _scan_netsh(self) -> list[WifiNetwork]:
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True, text=True, timeout=5, encoding="utf-8",
            errors="replace", creationflags=0x08000000
        )
        return _parse_netsh_output(result.stdout)

    def _scan_demo(self) -> list[WifiNetwork]:
        return self._demo_state.next_scan()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rssi_to_signal(rssi: int) -> int:
    """Convert dBm to 0-100% signal."""
    if rssi <= -100:
        return 0
    if rssi >= -50:
        return 100
    return 2 * (rssi + 100)


def _parse_netsh_output(text: str) -> list[WifiNetwork]:
    """Parse netsh wlan show networks mode=bssid output."""
    networks = []
    blocks = re.split(r"SSID \d+ :", text)[1:]
    for block in blocks:
        ssid_match = re.search(r"^\s*(.+)$", block, re.MULTILINE)
        ssid = ssid_match.group(1).strip() if ssid_match else "<unknown>"
        bssid_match = re.search(r"BSSID \d+\s*:\s*([0-9a-f:]{17})", block, re.I)
        bssid = bssid_match.group(1) if bssid_match else "00:00:00:00:00:00"
        sig_match = re.search(r"Signal\s*:\s*(\d+)%", block, re.I)
        signal = int(sig_match.group(1)) if sig_match else 50
        rssi = _signal_to_rssi(signal)
        networks.append(WifiNetwork(ssid=ssid, bssid=bssid, rssi=rssi, signal=signal))
    return networks


def _signal_to_rssi(signal_pct: int) -> int:
    """Convert 0-100% signal to approximate dBm."""
    return -100 + (signal_pct // 2)


# ── Demo Mode ─────────────────────────────────────────────────────────────────

class _DemoState:
    """Generates realistic synthetic RSSI data that mimics a person in a room."""

    NETWORKS = [
        ("HomeWifi-5G",  "AA:BB:CC:DD:EE:01", -52),
        ("HomeWifi-2.4", "AA:BB:CC:DD:EE:02", -68),
        ("Neighbor-AP",  "11:22:33:44:55:66", -82),
    ]

    def __init__(self):
        self._tick = 0
        self._phase = "present"  # present / absent / walking
        self._phase_timer = 0
        self._base_rssi = {b: r for _, b, r in self.NETWORKS}

    def next_scan(self) -> list[WifiNetwork]:
        self._tick += 1
        self._phase_timer += 1

        # Cycle phases: 60s present → 20s absent → 30s walking → repeat
        if self._phase == "present" and self._phase_timer > 30:
            self._phase = "walking"
            self._phase_timer = 0
        elif self._phase == "walking" and self._phase_timer > 15:
            self._phase = "absent"
            self._phase_timer = 0
        elif self._phase == "absent" and self._phase_timer > 10:
            self._phase = "present"
            self._phase_timer = 0

        networks = []
        for ssid, bssid, base_rssi in self.NETWORKS:
            noise = self._get_noise(bssid)
            rssi = base_rssi + noise
            signal = _rssi_to_signal(rssi)
            networks.append(WifiNetwork(ssid=ssid, bssid=bssid,
                                        rssi=rssi, signal=signal))
        return networks

    def _get_noise(self, bssid: str) -> float:
        if self._phase == "absent":
            return random.gauss(0, 0.3)     # Very stable = empty room
        elif self._phase == "walking":
            return random.gauss(0, 4.5)     # High variance = movement
        else:  # present stationary
            return random.gauss(0, 1.2)     # Mild variance = seated

    @property
    def phase(self) -> str:
        return self._phase
