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
config.py — Portable JSON configuration manager.
Stores settings in the same directory as the app (portable mode).
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict


def _get_config_dir() -> Path:
    """Portable mode: config sits next to main.py (desktop/ folder)."""
    return Path(__file__).parent.parent


@dataclass
class AppConfig:
    # Scanning
    scan_interval_sec: float = 2.0
    target_bssid: str = ""          # Empty = use strongest AP
    target_ssid: str = ""

    # Detection thresholds
    sensitivity: float = 1.0        # Multiplier: 1.0 = default, >1 = more sensitive
    immobility_threshold_min: int = 30
    calibration_samples: int = 30

    # Computed thresholds (set after calibration)
    baseline_variance: float = 0.0
    is_calibrated: bool = False

    # Export
    json_export_enabled: bool = True
    json_export_path: str = ""      # Default: desktop/data/wificensor_status.json

    # GitHub Sync
    github_sync_enabled: bool = False
    github_token: str = ""
    github_username: str = ""
    github_repo: str = ""
    github_branch: str = "main"
    github_device_id: str = "desktop"

    # UI
    window_width: int = 1200
    window_height: int = 800
    start_minimized: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AppConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ConfigManager:
    CONFIG_FILE = "wificensor_config.json"

    def __init__(self):
        self._config_path = _get_config_dir() / self.CONFIG_FILE
        self._config = self._load()

    def _load(self) -> AppConfig:
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return AppConfig.from_dict(data)
            except Exception:
                pass
        return AppConfig()

    def save(self):
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)

    @property
    def config(self) -> AppConfig:
        return self._config

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self._config, k):
                setattr(self._config, k, v)
        self.save()

    def get_export_path(self) -> Path:
        if self._config.json_export_path:
            return Path(self._config.json_export_path)
        data_dir = _get_config_dir() / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / "wificensor_status.json"

    def get_db_path(self) -> Path:
        data_dir = _get_config_dir() / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / "wificensor.db"


# Global singleton
_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager


def get_config() -> AppConfig:
    return get_config_manager().config
