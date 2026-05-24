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
tools.py — Các hàm Python mà AI Agent có thể gọi thông qua tool calling.

Mỗi tool được định nghĩa theo chuẩn Ollama function calling:
  - TOOL_DEFINITIONS: List[dict] — mô tả schema để gửi cho Ollama
  - Hàm Python tương ứng nhận và trả về kết quả cho Agent

Danh sách tools:
  1. query_health       — Lấy thông tin sức khỏe & hoạt động trong N phút gần nhất
  2. get_trend          — Xu hướng chỉ số (BPM, activity) trong N ngày
  3. alert_family       — Gửi cảnh báo lên GitHub Sync / Web Dashboard
  4. adjust_sensitivity — Thay đổi ngưỡng phát hiện của PresenceEngine
  5. explain_event      — Giải thích lý do một cảnh báo được kích hoạt
"""

import time
import json
import re
import requests
from urllib.parse import quote_plus
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from desktop.app.logger import get_logger

logger = get_logger("tools")

if TYPE_CHECKING:
    from desktop.app.database import Database
    from desktop.app.exporter import JsonExporter
    from desktop.app.config import ConfigManager


# ── Tool Schema Definitions (gửi cho Ollama) ──────────────────────────────────

BASE_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "query_health",
            "description": (
                "Lấy tóm tắt thông tin sức khỏe và hoạt động trong khoảng thời gian gần đây. "
                "Bao gồm: nhịp tim trung bình (BPM), thân nhiệt, số người, trạng thái hoạt động, "
                "và các cảnh báo gần nhất. Dùng khi người dùng hỏi về tình trạng sức khỏe."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "time_range_min": {
                        "type": "integer",
                        "description": "Số phút gần nhất cần tra cứu (ví dụ: 30 = 30 phút gần nhất). Mặc định: 60."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend",
            "description": (
                "Phân tích xu hướng tăng/giảm của một chỉ số sức khỏe trong N ngày gần đây. "
                "So sánh hôm nay với ngày hôm qua hoặc tuần trước. "
                "Dùng khi người dùng hỏi về 'xu hướng', 'tăng/giảm', 'so với hôm qua'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "Chỉ số cần phân tích: 'heart_rate' | 'activity' | 'presence_time' | 'alerts'",
                        "enum": ["heart_rate", "activity", "presence_time", "alerts"]
                    },
                    "days": {
                        "type": "integer",
                        "description": "Số ngày gần nhất để phân tích (ví dụ: 7 = 7 ngày). Mặc định: 7."
                    }
                },
                "required": ["metric"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "alert_family",
            "description": (
                "Gửi một tin nhắn cảnh báo đến gia đình hoặc người thân thông qua Web Dashboard. "
                "Chỉ dùng khi có tình huống cần thông báo khẩn cấp hoặc quan trọng."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Nội dung tin nhắn cảnh báo bằng tiếng Việt."
                    },
                    "severity": {
                        "type": "string",
                        "description": "Mức độ cảnh báo: 'info' (thông tin) | 'warn' (cần chú ý) | 'danger' (khẩn cấp)",
                        "enum": ["info", "warn", "danger"]
                    }
                },
                "required": ["message", "severity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_sensitivity",
            "description": (
                "Thay đổi độ nhạy của hệ thống phát hiện té ngã và bất động. "
                "Tăng độ nhạy nếu hệ thống bỏ sót cảnh báo, giảm nếu quá nhiều báo sai. "
                "Chỉ dùng khi người dùng yêu cầu điều chỉnh hoặc có nhiều báo sai."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Mức độ nhạy: 'low' (thấp, ít báo sai) | 'medium' (cân bằng) | 'high' (cao, nhạy nhất)",
                        "enum": ["low", "medium", "high"]
                    }
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_event",
            "description": (
                "Giải thích chi tiết lý do một cảnh báo cụ thể được kích hoạt. "
                "Phân tích dữ liệu sóng Wi-Fi và sinh hiệu xung quanh thời điểm xảy ra sự kiện. "
                "Dùng khi người dùng hỏi 'tại sao lại báo động lúc X?' hoặc 'cảnh báo X có chính xác không?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID của sự kiện cảnh báo cần giải thích (lấy từ lịch sử cảnh báo)."
                    }
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_anomaly_report",
            "description": (
                "Ghi nhận một báo cáo sai lệch dữ liệu, báo động sai, hoặc lỗi hệ thống từ người dùng. "
                "Lưu thông tin chi tiết vào tệp tin báo cáo lỗi cục bộ để người dùng có thể xem lại hoặc gửi cho kỹ thuật viên. "
                "Dùng khi người dùng yêu cầu 'lưu lỗi', 'ghi nhận sai lệch', 'tạo báo cáo lỗi' hoặc phản ánh dữ liệu không chính xác."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Mô tả chi tiết về sai số, lỗi dữ liệu hoặc hành vi bất thường của hệ thống bằng tiếng Việt."
                    },
                    "timestamp_info": {
                        "type": "string",
                        "description": "Thời điểm hoặc khoảng thời gian xảy ra lỗi (ví dụ: '02:05 sáng', 'hôm qua lúc 21:00')."
                    },
                    "expected_behavior": {
                        "type": "string",
                        "description": "Hành vi đúng hoặc mong đợi của hệ thống (ví dụ: 'chỉ nên báo 1 người', 'không nên phát cảnh báo té ngã')."
                    }
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": (
                "Tìm kiếm thông tin thời gian thực, kiến thức y tế, tin tức mới từ internet. "
                "Sử dụng khi người dùng hỏi các câu hỏi chung, kiến thức bệnh học, hướng dẫn chăm sóc y tế "
                "hoặc bất kỳ thông tin thời gian thực nào không có sẵn trong hệ thống cục bộ."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm bằng tiếng Việt hoặc tiếng Anh."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# ── Tool Executor Class ────────────────────────────────────────────────────────

class ToolExecutor:
    """
    Thực thi các tool calls từ AI Agent.
    Được khởi tạo với tham chiếu đến Database, Exporter, ConfigManager.
    """

    def __init__(self, db: "Database", exporter: "JsonExporter", cfg_manager: "ConfigManager"):
        self.db = db
        self.exporter = exporter
        self.cfg_manager = cfg_manager

    def get_definitions(self) -> list:
        """Trả về toàn bộ định nghĩa tool (bao gồm tool hệ thống và kỹ năng tự định nghĩa)."""
        definitions = list(BASE_TOOL_DEFINITIONS)
        try:
            skills_file = self.cfg_manager.get_db_path().parent / "custom_skills.json"
            if skills_file.exists():
                with open(skills_file, "r", encoding="utf-8") as f:
                    skills = json.load(f)
                    for s in skills:
                        name = s.get("name", "").strip()
                        desc = s.get("description", "").strip()
                        if name and desc:
                            definitions.append({
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "description": desc,
                                    "parameters": {
                                        "type": "object",
                                        "properties": {},
                                        "required": []
                                    }
                                }
                            })
        except Exception as e:
            logger.error(f"Lỗi khi nạp kỹ năng tự định nghĩa vào schema: {e}")
        return definitions

    def execute(self, tool_name: str, arguments: dict) -> str:
        """
        Điều phối tool_name đến hàm tương ứng.
        Trả về chuỗi kết quả (JSON string hoặc plain text tiếng Việt).
        """
        try:
            # 1. Kiểm tra nếu là các tool hệ thống chính thức
            if tool_name == "query_health":
                return self._query_health(**arguments)
            elif tool_name == "get_trend":
                return self._get_trend(**arguments)
            elif tool_name == "alert_family":
                return self._alert_family(**arguments)
            elif tool_name == "adjust_sensitivity":
                return self._adjust_sensitivity(**arguments)
            elif tool_name == "explain_event":
                return self._explain_event(**arguments)
            elif tool_name == "record_anomaly_report":
                return self._record_anomaly_report(**arguments)
            elif tool_name == "search_internet":
                return self._search_internet(**arguments)
                
            # 2. Kiểm tra nếu là kỹ năng tự định nghĩa (Skills)
            skills_file = self.cfg_manager.get_db_path().parent / "custom_skills.json"
            if skills_file.exists():
                with open(skills_file, "r", encoding="utf-8") as f:
                    skills = json.load(f)
                    for s in skills:
                        if s.get("name") == tool_name:
                            logger.info(f"Kích hoạt kỹ năng tự định nghĩa '{tool_name}' thành công.")
                            return s.get("response", "Kỹ năng rỗng.")

            return f"[Lỗi] Tool '{tool_name}' không tồn tại."
        except Exception as e:
            return f"[Lỗi khi thực thi {tool_name}]: {str(e)}"

    def _search_internet(self, query: str) -> str:
        """Tìm kiếm thông tin thời gian thực từ internet qua Yahoo Search."""
        logger.info(f"Đang thực hiện tìm kiếm internet cho truy vấn: '{query}'...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
        try:
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code != 200:
                return f"Lỗi: Không thể kết nối tới Yahoo Search (HTTP {resp.status_code})"
            
            html_content = resp.text
            results = []
            
            # Trích xuất kết quả bằng Regex
            blocks = re.findall(r'<div[^>]*class="[^"]*algo[^"|a-zA-Z-]*sr[^"]*"[^>]*>.*?</div>\s*</div>\s*</li>', html_content, re.DOTALL)
            if not blocks:
                blocks = re.findall(r'<div[^>]*class="[^"]*algo[^"]*"[^>]*>.*?</div>\s*</div>\s*</li>', html_content, re.DOTALL)
            if not blocks:
                blocks = re.findall(r'<div[^>]*class="[^"]*algo[^"]*"[^>]*>.*?</div>\s*</div>', html_content, re.DOTALL)
                
            import html as html_lib
            import urllib.parse
            
            for block in blocks[:5]:
                # Trích xuất URL
                href_match = re.search(r'<a[^>]*href="([^"]+)"', block)
                url_str = href_match.group(1) if href_match else "Không nguồn"
                
                # Làm sạch URL chuyển hướng của Yahoo
                if "/RU=" in url_str:
                    try:
                        url_str = urllib.parse.unquote(url_str.split("/RU=")[1].split("/")[0])
                    except Exception:
                        pass
                
                # Trích xuất Title
                title = "Không tiêu đề"
                h3_match = re.search(r'<h3[^>]*>(.*?)</h3>', block, re.DOTALL)
                if h3_match:
                    title = re.sub(r'<[^>]+>', '', h3_match.group(1)).strip()
                    
                # Trích xuất Snippet
                snippet = "Không tóm tắt"
                snippet_match = re.search(r'<div[^>]*class="[^"]*compText[^"]*"[^>]*>(.*?)</div>', block, re.DOTALL)
                if snippet_match:
                    snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                
                title = html_lib.unescape(title)
                snippet = html_lib.unescape(snippet)
                
                # Làm sạch các ký tự HTML thô sơ khác
                title = title.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
                snippet = snippet.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
                
                results.append(f"- **{title}**\n  Nguồn: {url_str}\n  Tóm tắt: {snippet}")
                
            if results:
                summary = "\n\n".join(results)
                logger.info("Tìm kiếm internet thành công, trả kết quả về cho Agent.")
                return summary
            else:
                logger.warning("Không tìm thấy kết quả tìm kiếm nào trên Yahoo Search.")
                return "Không tìm thấy kết quả tìm kiếm nào phù hợp trên internet."
        except Exception as e:
            logger.error(f"Gặp lỗi khi tìm kiếm internet: {e}")
            return f"Gặp lỗi hệ thống khi kết nối tìm kiếm: {str(e)}"

    # ── Tool 1: query_health ──────────────────────────────────────────────────

    def _query_health(self, time_range_min: int = 60) -> str:
        """Tổng hợp thông tin sức khỏe trong N phút gần nhất."""
        now = time.time()
        since = now - time_range_min * 60

        # Lấy RSSI snapshots
        snapshots = self.db.get_rssi_since(since)
        # Lấy cảnh báo gần nhất (5 cảnh báo)
        recent_alerts = self.db.get_recent_alerts(limit=5)
        # Lấy bio estimator state
        bio = self.exporter.bio_estimator.last_result

        # Tính trạng thái trung bình
        if snapshots:
            avg_rssi = sum(s.rssi for s in snapshots) / len(snapshots)
            avg_variance = sum(s.variance for s in snapshots) / len(snapshots)
            labels = [s.presence_label for s in snapshots]
            # Trạng thái phổ biến nhất
            dominant_label = max(set(labels), key=labels.count)
        else:
            avg_rssi = 0
            avg_variance = 0
            dominant_label = "UNKNOWN"

        # Format kết quả
        result = {
            "khoang_thoi_gian": f"{time_range_min} phút gần nhất",
            "so_mau_du_lieu": len(snapshots),
            "rssi_trung_binh": round(avg_rssi, 1),
            "bien_dong_song": round(avg_variance, 3),
            "trang_thai_chu_yeu": dominant_label,
        }

        # Thêm bio signals nếu có
        if bio:
            result["sinh_hieu"] = {
                "nhip_tim": f"{bio.heart_rate_bpm} BPM" if bio.heart_rate_bpm else "Chưa có",
                "nhip_tim_nguon": "Ước tính" if bio.heart_rate_estimated else bio.heart_rate_source,
                "than_nhiet": f"{bio.body_temp_celsius} °C" if bio.body_temp_celsius else "Chưa có",
                "so_nguoi_uoc_tinh": bio.people_count,
                "do_tin_cay_so_nguoi": f"{int(bio.people_confidence * 100)}%",
            }

        # Thêm cảnh báo gần nhất
        if recent_alerts:
            latest = recent_alerts[0]
            alert_time = datetime.fromtimestamp(latest.timestamp).strftime("%H:%M")
            result["canh_bao_gan_nhat"] = {
                "loai": latest.alert_type,
                "luc": alert_time,
                "noi_dung": latest.message,
                "da_xu_ly": "Có" if latest.acknowledged else "Chưa",
            }
        else:
            result["canh_bao_gan_nhat"] = "Không có cảnh báo nào."

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    # ── Tool 2: get_trend ─────────────────────────────────────────────────────

    def _get_trend(self, metric: str, days: int = 7) -> str:
        """Phân tích xu hướng chỉ số trong N ngày."""
        now = time.time()
        midnight_today = now - (now % 86400)

        # Thu thập dữ liệu từng ngày
        daily_data = []
        for day_offset in range(days - 1, -1, -1):
            day_start = midnight_today - day_offset * 86400
            day_end = day_start + 86400
            day_label = datetime.fromtimestamp(day_start).strftime("%d/%m")

            snapshots = self.db.get_rssi_since(day_start)
            snapshots = [s for s in snapshots if s.timestamp < day_end]

            if metric == "heart_rate":
                # Lấy bio estimate trung bình từ variance
                variances = [s.variance for s in snapshots]
                if variances:
                    avg_var = sum(variances) / len(variances)
                    # Ước tính BPM từ variance (công thức đơn giản từ BioEstimator)
                    est_bpm = round(72.0 + (avg_var / 12.0) * 8.0, 1)
                    daily_data.append({"ngay": day_label, "gia_tri": est_bpm, "don_vi": "BPM"})
                else:
                    daily_data.append({"ngay": day_label, "gia_tri": None, "don_vi": "BPM"})

            elif metric == "activity":
                labels = [s.presence_label for s in snapshots]
                active = sum(1 for l in labels if l in ("WALKING", "PRESENT"))
                total = len(labels) or 1
                pct = round(active / total * 100, 1)
                daily_data.append({"ngay": day_label, "gia_tri": pct, "don_vi": "% thời gian hoạt động"})

            elif metric == "presence_time":
                events = self.db.get_presence_events_since(day_start)
                events = [e for e in events if e.start_time < day_end]
                present_sec = sum(
                    ((e.end_time or now) - e.start_time)
                    for e in events if e.event_type == "PRESENT"
                )
                daily_data.append({"ngay": day_label, "gia_tri": round(present_sec / 60), "don_vi": "phút có người"})

            elif metric == "alerts":
                alerts = self.db.get_recent_alerts(limit=100)
                count = sum(1 for a in alerts if day_start <= a.timestamp < day_end)
                daily_data.append({"ngay": day_label, "gia_tri": count, "don_vi": "cảnh báo"})

        # Tính xu hướng (so sánh nửa đầu và nửa sau)
        valid = [d for d in daily_data if d["gia_tri"] is not None]
        trend_text = "Không đủ dữ liệu để phân tích xu hướng."
        if len(valid) >= 2:
            half = len(valid) // 2
            avg_first = sum(d["gia_tri"] for d in valid[:half]) / half
            avg_last = sum(d["gia_tri"] for d in valid[half:]) / (len(valid) - half)
            diff = avg_last - avg_first
            pct_change = (diff / avg_first * 100) if avg_first else 0
            unit = valid[0]["don_vi"]

            if abs(pct_change) < 5:
                trend_text = f"Ổn định, không thay đổi đáng kể (biến động <5%)."
            elif pct_change > 0:
                trend_text = f"Tăng {pct_change:.1f}% so với đầu kỳ ({avg_first:.1f} → {avg_last:.1f} {unit})."
            else:
                trend_text = f"Giảm {abs(pct_change):.1f}% so với đầu kỳ ({avg_first:.1f} → {avg_last:.1f} {unit})."

        import json
        return json.dumps({
            "chi_so": metric,
            "so_ngay_phan_tich": days,
            "xu_huong": trend_text,
            "du_lieu_hang_ngay": daily_data
        }, ensure_ascii=False, indent=2)

    # ── Tool 3: alert_family ──────────────────────────────────────────────────

    def _alert_family(self, message: str, severity: str = "info") -> str:
        """Đẩy thông báo lên Web Dashboard qua GitHub Sync."""
        try:
            cfg = self.cfg_manager.config
            if not cfg.github_sync_enabled:
                return "GitHub Sync chưa được bật. Thông báo chỉ hiển thị trên màn hình local."

            # Ghi vào snapshot data như một alert đặc biệt từ AI
            snapshot_patch = {
                "ai_message": {
                    "content": message,
                    "severity": severity,
                    "timestamp": datetime.now().isoformat(),
                    "source": "AI Agent"
                }
            }
            self.exporter.sync_manager.queue_status_upload(snapshot_patch)
            return f"✅ Đã gửi thông báo tới Web Dashboard: '{message[:50]}...'" if len(message) > 50 else f"✅ Đã gửi: '{message}'"
        except Exception as e:
            return f"❌ Không thể gửi thông báo: {str(e)}"

    # ── Tool 4: adjust_sensitivity ────────────────────────────────────────────

    def _adjust_sensitivity(self, level: str) -> str:
        """Thay đổi độ nhạy phát hiện."""
        level_map = {
            "low":    0.7,
            "medium": 1.0,
            "high":   1.5,
        }
        if level not in level_map:
            return f"Mức độ '{level}' không hợp lệ. Chọn: low / medium / high."

        sensitivity = level_map[level]
        self.cfg_manager.update(sensitivity=sensitivity)

        desc = {
            "low":    "Thấp — ít báo sai hơn, có thể bỏ sót một số sự kiện nhỏ.",
            "medium": "Trung bình — cân bằng giữa độ nhạy và độ chính xác.",
            "high":   "Cao — phát hiện mọi thay đổi nhỏ, có thể nhiều báo sai hơn.",
        }
        return f"✅ Đã đặt độ nhạy thành **{level}** ({sensitivity}x). {desc[level]}"

    # ── Tool 5: explain_event ─────────────────────────────────────────────────

    def _explain_event(self, event_id: int) -> str:
        """Giải thích chi tiết nguyên nhân một cảnh báo."""
        # Lấy cảnh báo cụ thể
        alerts = self.db.get_recent_alerts(limit=50)
        target = next((a for a in alerts if a.id == event_id), None)

        if not target:
            return f"Không tìm thấy cảnh báo với ID {event_id}. Vui lòng kiểm tra lại."

        alert_time = datetime.fromtimestamp(target.timestamp).strftime("%H:%M:%S ngày %d/%m/%Y")

        # Lấy RSSI data xung quanh thời điểm xảy ra (5 phút trước)
        window_start = target.timestamp - 300
        nearby_snapshots = self.db.get_rssi_since(window_start)
        nearby_snapshots = [s for s in nearby_snapshots if s.timestamp <= target.timestamp + 30]

        # Phân tích context
        if nearby_snapshots:
            rssi_values = [s.rssi for s in nearby_snapshots]
            variances = [s.variance for s in nearby_snapshots]
            labels = [s.presence_label for s in nearby_snapshots]

            context = {
                "thoi_diem": alert_time,
                "loai_canh_bao": target.alert_type,
                "noi_dung_canh_bao": target.message,
                "rssi_truoc_canh_bao": f"Trung bình {sum(rssi_values)/len(rssi_values):.1f} dBm",
                "bien_dong_song": f"Trung bình {sum(variances)/len(variances):.3f}",
                "trang_thai_hoat_dong": labels[-1] if labels else "Không xác định",
                "so_mau_phan_tich": len(nearby_snapshots),
            }

            if target.alert_type == "FALL":
                context["phan_tich"] = (
                    "Hệ thống phát hiện tín hiệu sóng biến mất đột ngột (<3 giây) "
                    "sau trạng thái PRESENT, điều này thường xảy ra khi người ngã "
                    "xuống sàn (làm thay đổi đột ngột hướng phản xạ sóng)."
                )
            elif target.alert_type == "IMMOBILITY":
                context["phan_tich"] = (
                    f"Hệ thống phát hiện người bất động liên tục trong thời gian dài "
                    f"(phương sai sóng thấp: {sum(variances)/len(variances):.3f}). "
                    "Đây có thể là ngủ sâu, ngồi thiền hoặc cần kiểm tra sức khỏe."
                )
        else:
            context = {
                "thoi_diem": alert_time,
                "loai_canh_bao": target.alert_type,
                "noi_dung_canh_bao": target.message,
                "phan_tich": "Không đủ dữ liệu RSSI xung quanh thời điểm này để phân tích chi tiết."
            }

        import json
        return json.dumps(context, ensure_ascii=False, indent=2)

    # ── Tool 6: record_anomaly_report ─────────────────────────────────────────

    def _record_anomaly_report(self, description: str, timestamp_info: str = "", expected_behavior: str = "") -> str:
        """Ghi nhận báo cáo sai sót dữ liệu từ người dùng."""
        try:
            import os
            import json
            import time
            from pathlib import Path
            
            data_dir = self.cfg_manager.get_db_path().parent
            data_dir.mkdir(parents=True, exist_ok=True)
            reports_file = data_dir / "anomaly_reports.json"
            
            reports = []
            if reports_file.exists():
                try:
                    with open(reports_file, "r", encoding="utf-8") as f:
                        reports = json.load(f)
                except Exception:
                    pass
            
            new_report = {
                "id": int(time.time()),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_info": timestamp_info or "Không xác định",
                "description": description,
                "expected_behavior": expected_behavior or "Không xác định",
                "status": "Chờ kỹ thuật xử lý"
            }
            reports.append(new_report)
            
            with open(reports_file, "w", encoding="utf-8") as f:
                json.dump(reports, f, indent=2, ensure_ascii=False)
                
            return (
                f"✅ Đã ghi nhận báo cáo lỗi thành công (Mã số: #{new_report['id']}).\n"
                f"Tệp báo cáo đã được lưu tại: `data/anomaly_reports.json`.\n"
                f"Bạn có thể mở tệp này để kiểm tra chéo hoặc gửi trực tiếp cho kỹ thuật viên."
            )
        except Exception as e:
            return f"❌ Lỗi khi lưu báo cáo: {str(e)}"
