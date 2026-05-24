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
logger.py — Hệ thống ghi nhật ký toàn cục cho Wifi-Censor.
Tạo các handlers ghi nhật ký ra console (stdout) và tệp tin xoay vòng (RotatingFileHandler)
tại desktop/data/wificensor.log.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Thư mục chứa logs
LOG_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = LOG_DIR / "wificensor.log"

# Đảm bảo thư mục tồn tại
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Khởi tạo định dạng log
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Tạo formatter chung
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# Cấu hình root logger
root_logger = logging.getLogger("wificensor")
root_logger.setLevel(logging.INFO)

# Tránh lặp handler nếu file bị nạp lại nhiều lần
if not root_logger.handlers:
    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Rotating File Handler (Ghi log xoay vòng - Tối đa 5MB/file, giữ lại 3 backup)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"[Logger] Không thể tạo file handler ghi log ra file: {e}", file=sys.stderr)


def get_logger(name: str) -> logging.Logger:
    """Trả về một logger con thuộc namespace wificensor."""
    # Đảm bảo định danh wificensor.name
    if not name.startswith("wificensor.") and name != "wificensor":
        return logging.getLogger(f"wificensor.{name}")
    return logging.getLogger(name)
