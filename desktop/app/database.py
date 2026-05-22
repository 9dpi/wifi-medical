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
database.py — SQLite3 local storage layer (thread-safe).
Tables: rssi_snapshots, presence_events, alert_events
Retention: 30 days auto-purge.
"""

import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RssiSnapshot:
    id: int
    timestamp: float
    bssid: str
    ssid: str
    rssi: int
    variance: float
    presence_label: str   # PRESENT | ABSENT | WALKING | SLEEPING | CALIBRATING


@dataclass
class PresenceEvent:
    id: int
    start_time: float
    end_time: Optional[float]
    event_type: str       # PRESENT | ABSENT | FALL_SUSPECTED | IMMOBILITY_ALERT
    confidence: float
    notes: str = ""


@dataclass
class AlertEvent:
    id: int
    timestamp: float
    alert_type: str       # FALL | IMMOBILITY | INTRUSION
    message: str
    acknowledged: bool = False


class Database:
    RETENTION_DAYS = 30

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_db(self):
        with self._lock:
            conn = self._conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS rssi_snapshots (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL    NOT NULL,
                    bssid     TEXT    NOT NULL,
                    ssid      TEXT    NOT NULL DEFAULT '',
                    rssi      INTEGER NOT NULL,
                    variance  REAL    NOT NULL DEFAULT 0.0,
                    presence_label TEXT NOT NULL DEFAULT 'UNKNOWN'
                );
                CREATE INDEX IF NOT EXISTS idx_rssi_ts ON rssi_snapshots(timestamp);

                CREATE TABLE IF NOT EXISTS presence_events (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time REAL    NOT NULL,
                    end_time   REAL,
                    event_type TEXT    NOT NULL,
                    confidence REAL    NOT NULL DEFAULT 0.0,
                    notes      TEXT    NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_pe_ts ON presence_events(start_time);

                CREATE TABLE IF NOT EXISTS alert_events (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp    REAL NOT NULL,
                    alert_type   TEXT NOT NULL,
                    message      TEXT NOT NULL DEFAULT '',
                    acknowledged INTEGER NOT NULL DEFAULT 0
                );
            """)
            conn.commit()

    # ── RSSI ──────────────────────────────────────────────────────────────────

    def insert_rssi(self, ts: float, bssid: str, ssid: str, rssi: int,
                    variance: float, label: str):
        with self._lock:
            self._conn().execute(
                "INSERT INTO rssi_snapshots(timestamp,bssid,ssid,rssi,variance,presence_label)"
                " VALUES(?,?,?,?,?,?)",
                (ts, bssid, ssid, rssi, variance, label)
            )
            self._conn().commit()

    def get_rssi_last_n(self, n: int = 120) -> list[RssiSnapshot]:
        with self._lock:
            rows = self._conn().execute(
                "SELECT * FROM rssi_snapshots ORDER BY timestamp DESC LIMIT ?", (n,)
            ).fetchall()
        return [RssiSnapshot(**dict(r)) for r in reversed(rows)]

    def get_rssi_since(self, since_ts: float) -> list[RssiSnapshot]:
        with self._lock:
            rows = self._conn().execute(
                "SELECT * FROM rssi_snapshots WHERE timestamp >= ? ORDER BY timestamp",
                (since_ts,)
            ).fetchall()
        return [RssiSnapshot(**dict(r)) for r in rows]

    # ── Presence Events ────────────────────────────────────────────────────────

    def insert_presence_event(self, start: float, event_type: str,
                               confidence: float, notes: str = "") -> int:
        with self._lock:
            cur = self._conn().execute(
                "INSERT INTO presence_events(start_time,event_type,confidence,notes)"
                " VALUES(?,?,?,?)",
                (start, event_type, confidence, notes)
            )
            self._conn().commit()
            return cur.lastrowid

    def close_presence_event(self, event_id: int, end_time: float):
        with self._lock:
            self._conn().execute(
                "UPDATE presence_events SET end_time=? WHERE id=?",
                (end_time, event_id)
            )
            self._conn().commit()

    def get_presence_events_since(self, since_ts: float) -> list[PresenceEvent]:
        with self._lock:
            rows = self._conn().execute(
                "SELECT * FROM presence_events WHERE start_time >= ? ORDER BY start_time",
                (since_ts,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            result.append(PresenceEvent(**d))
        return result

    def get_today_stats(self) -> dict:
        """Returns present_min, absent_min for today."""
        midnight = time.time() - (time.time() % 86400)
        events = self.get_presence_events_since(midnight)
        present_sec = 0.0
        absent_sec = 0.0
        for e in events:
            duration = ((e.end_time or time.time()) - e.start_time)
            if e.event_type == "PRESENT":
                present_sec += duration
            elif e.event_type == "ABSENT":
                absent_sec += duration
        return {
            "present_min": int(present_sec / 60),
            "absent_min": int(absent_sec / 60),
        }

    # ── Alerts ─────────────────────────────────────────────────────────────────

    def insert_alert(self, ts: float, alert_type: str, message: str) -> int:
        with self._lock:
            cur = self._conn().execute(
                "INSERT INTO alert_events(timestamp,alert_type,message) VALUES(?,?,?)",
                (ts, alert_type, message)
            )
            self._conn().commit()
            return cur.lastrowid

    def get_recent_alerts(self, limit: int = 10) -> list[AlertEvent]:
        with self._lock:
            rows = self._conn().execute(
                "SELECT * FROM alert_events ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return [AlertEvent(**dict(r)) for r in rows]

    def acknowledge_alert(self, alert_id: int):
        with self._lock:
            self._conn().execute(
                "UPDATE alert_events SET acknowledged=1 WHERE id=?", (alert_id,)
            )
            self._conn().commit()

    # ── Purge ──────────────────────────────────────────────────────────────────

    def purge_old_data(self):
        cutoff = time.time() - self.RETENTION_DAYS * 86400
        with self._lock:
            self._conn().execute(
                "DELETE FROM rssi_snapshots WHERE timestamp < ?", (cutoff,))
            self._conn().execute(
                "DELETE FROM presence_events WHERE start_time < ?", (cutoff,))
            self._conn().execute(
                "DELETE FROM alert_events WHERE timestamp < ?", (cutoff,))
            self._conn().commit()

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
