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
report_generator.py — Tạo báo cáo sức khỏe thông minh cuối ngày.

Chức năng:
  - Tổng hợp dữ liệu hoạt động, cảnh báo, sinh hiệu của ngày hôm nay
  - Nhờ AI Agent đưa ra nhận xét và đề xuất bằng tiếng Việt
  - Xuất báo cáo dạng PDF (reportlab) vào desktop/data/reports/
  - Tự động kích hoạt vào giờ cài đặt (mặc định 21:00)
"""

import time
import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from desktop.app.ai.agent import WifiCensorAgent
    from desktop.app.database import Database
    from desktop.app.bio_estimator import BioSignalEstimator


class ReportGenerator:
    """
    Tạo báo cáo sức khỏe cuối ngày với nhận xét từ AI.
    """

    def __init__(
        self,
        db: "Database",
        bio_estimator: "BioSignalEstimator",
        reports_dir: Optional[Path] = None
    ):
        self.db = db
        self.bio_estimator = bio_estimator
        import sys
        if getattr(sys, "frozen", False):
            self.reports_dir = reports_dir or Path(sys.executable).parent / "data" / "reports"
        else:
            self.reports_dir = reports_dir or Path(__file__).parent.parent.parent / "data" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._agent: Optional["WifiCensorAgent"] = None
        self._scheduled_hour: int = 21  # 21:00
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_report_date: Optional[str] = None

    def set_agent(self, agent: "WifiCensorAgent") -> None:
        self._agent = agent

    def start_scheduler(self, hour: int = 21) -> None:
        """Bắt đầu scheduler kiểm tra mỗi phút, tạo báo cáo lúc `hour`:00."""
        self._scheduled_hour = hour
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        print(f"[ReportGenerator] Scheduler bắt đầu — sẽ tạo báo cáo lúc {hour:02d}:00 mỗi ngày.")

    def stop_scheduler(self) -> None:
        self._stop_event.set()

    def generate_now(self) -> Optional[Path]:
        """Tạo báo cáo ngay lập tức (gọi thủ công)."""
        return self._generate_report()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _scheduler_loop(self) -> None:
        while not self._stop_event.is_set():
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")

            # Kiểm tra đúng giờ cài đặt và chưa tạo báo cáo hôm nay
            if now.hour == self._scheduled_hour and self._last_report_date != today_str:
                self._last_report_date = today_str
                print("[ReportGenerator] Đến giờ tạo báo cáo ngày...")
                thread = threading.Thread(target=self._generate_report, daemon=True)
                thread.start()

            self._stop_event.wait(timeout=60)  # Kiểm tra mỗi phút

    def _collect_data(self) -> dict:
        """Thu thập dữ liệu của ngày hôm nay từ database."""
        now = time.time()
        midnight = now - (now % 86400)

        # Thống kê cơ bản
        stats = self.db.get_today_stats()
        recent_alerts = self.db.get_recent_alerts(limit=20)
        today_alerts = [a for a in recent_alerts if a.timestamp >= midnight]
        snapshots = self.db.get_rssi_since(midnight)

        # Phân tích cảnh báo
        fall_alerts = [a for a in today_alerts if a.alert_type == "FALL"]
        immobility_alerts = [a for a in today_alerts if a.alert_type == "IMMOBILITY"]
        confirmed_alerts = [a for a in today_alerts if a.acknowledged]
        false_alarms = len(confirmed_alerts)  # Đã xác nhận = người dùng xử lý

        # Phân tích sóng (bio estimates)
        bio = self.bio_estimator.last_result
        avg_bpm = None
        avg_temp = None

        if snapshots:
            # Ước tính BPM trung bình từ variance
            variances = [s.variance for s in snapshots]
            avg_var = sum(variances) / len(variances)
            avg_bpm = round(72.0 + (avg_var / 12.0) * 8.0, 1)

        if bio and bio.body_temp_celsius:
            avg_temp = bio.body_temp_celsius

        # Phân tích hoạt động
        labels = [s.presence_label for s in snapshots]
        total = len(labels) or 1
        walk_pct = round(sum(1 for l in labels if "WALK" in l) / total * 100, 1)
        stat_pct = round(sum(1 for l in labels if l in ("PRESENT", "STATIONARY", "SLEEPING")) / total * 100, 1)

        return {
            "ngay": datetime.now().strftime("%d/%m/%Y"),
            "thoi_gian_co_nguoi_phut": stats["present_min"],
            "thoi_gian_vang_phong_phut": stats["absent_min"],
            "tong_canh_bao": len(today_alerts),
            "canh_bao_te_nga": len(fall_alerts),
            "canh_bao_bat_dong": len(immobility_alerts),
            "da_xu_ly": false_alarms,
            "nhip_tim_trung_binh": avg_bpm,
            "than_nhiet": avg_temp,
            "phan_tram_di_lai": walk_pct,
            "phan_tram_nghi_ngoi": stat_pct,
            "so_mau_du_lieu": len(snapshots),
        }

    def _build_ai_prompt(self, data: dict) -> str:
        return f"""Dựa trên dữ liệu theo dõi của ngày {data['ngay']}, hãy viết một báo cáo sức khỏe ngắn gọn (3-5 câu):

Dữ liệu:
- Thời gian có người trong phòng: {data['thoi_gian_co_nguoi_phut']} phút
- Thời gian vắng phòng: {data['thoi_gian_vang_phong_phut']} phút
- Cảnh báo té ngã: {data['canh_bao_te_nga']} lần
- Cảnh báo bất động: {data['canh_bao_bat_dong']} lần
- Nhịp tim trung bình ước tính: {data['nhip_tim_trung_binh']} BPM
- Thân nhiệt: {data['than_nhiet']} °C
- % thời gian đi lại: {data['phan_tram_di_lai']}%
- % thời gian nghỉ ngơi: {data['phan_tram_nghi_ngoi']}%

Hãy:
1. Tóm tắt tình trạng chung của ngày hôm nay (tốt/bình thường/cần chú ý)
2. Nhận xét cụ thể về một điểm nổi bật (ví dụ: nhịp tim, hoạt động, cảnh báo)
3. Đề xuất ngắn gọn cho gia đình hoặc nhân viên y tế

Viết bằng tiếng Việt, đơn giản, dễ hiểu."""

    def _generate_report(self) -> Optional[Path]:
        """Tạo báo cáo PDF hoặc text file."""
        try:
            data = self._collect_data()

            # Lấy nhận xét AI
            ai_comment = "Không có kết nối AI để phân tích."
            if self._agent:
                try:
                    ai_comment = self._agent.ask_sync(self._build_ai_prompt(data))
                except Exception as e:
                    ai_comment = f"Lỗi AI: {e}"

            # Thử xuất PDF, fallback sang text nếu không có reportlab
            try:
                return self._export_pdf(data, ai_comment)
            except ImportError:
                print("[ReportGenerator] reportlab chưa cài — xuất báo cáo dạng text.")
                return self._export_text(data, ai_comment)

        except Exception as e:
            print(f"[ReportGenerator] Lỗi tạo báo cáo: {e}")
            return None

    def _export_pdf(self, data: dict, ai_comment: str) -> Path:
        """Xuất báo cáo PDF dùng reportlab."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        filename = f"bao_cao_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        output_path = self.reports_dir / filename

        doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                     fontSize=16, textColor=colors.HexColor("#6366f1"),
                                     spaceAfter=10)
        body_style = ParagraphStyle("body", parent=styles["Normal"],
                                    fontSize=11, leading=16, spaceAfter=6)
        ai_style = ParagraphStyle("ai", parent=styles["Normal"],
                                  fontSize=11, leading=16,
                                  backColor=colors.HexColor("#f0f0ff"),
                                  borderPadding=8, spaceAfter=10)

        story = []
        story.append(Paragraph(f"📊 Báo Cáo Sức Khỏe — {data['ngay']}", title_style))
        story.append(Paragraph("Hệ thống Wifi-Censor | Giám sát an toàn phi tiếp xúc", body_style))
        story.append(Spacer(1, 0.5*cm))

        # Bảng thống kê
        table_data = [
            ["Chỉ số", "Giá trị"],
            ["Thời gian có người", f"{data['thoi_gian_co_nguoi_phut']} phút"],
            ["Thời gian vắng phòng", f"{data['thoi_gian_vang_phong_phut']} phút"],
            ["Cảnh báo té ngã", str(data['canh_bao_te_nga'])],
            ["Cảnh báo bất động", str(data['canh_bao_bat_dong'])],
            ["Nhịp tim ước tính", f"{data['nhip_tim_trung_binh']} BPM" if data['nhip_tim_trung_binh'] else "N/A"],
            ["Thân nhiệt", f"{data['than_nhiet']} °C" if data['than_nhiet'] else "N/A"],
            ["% Thời gian đi lại", f"{data['phan_tram_di_lai']}%"],
        ]

        table = Table(table_data, colWidths=[8*cm, 8*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5ff")]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))

        # Nhận xét AI
        story.append(Paragraph("🤖 Nhận xét từ Trợ lý AI:", title_style))
        story.append(Paragraph(ai_comment.replace("\n", "<br/>"), ai_style))

        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            f"Báo cáo được tạo tự động lúc {datetime.now().strftime('%H:%M:%S')} | Wifi-Censor v2.0",
            ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
        ))

        doc.build(story)
        print(f"[ReportGenerator] Đã xuất PDF: {output_path}")
        return output_path

    def _export_text(self, data: dict, ai_comment: str) -> Path:
        """Fallback: xuất báo cáo dạng text nếu không có reportlab."""
        filename = f"bao_cao_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        output_path = self.reports_dir / filename

        content = f"""
=======================================================
   BÁO CÁO SỨC KHỎE NGÀY {data['ngay']}
   Hệ thống Wifi-Censor | Giám sát an toàn phi tiếp xúc
=======================================================

📊 THỐNG KÊ HOẠT ĐỘNG:
  - Thời gian có người trong phòng : {data['thoi_gian_co_nguoi_phut']} phút
  - Thời gian vắng phòng           : {data['thoi_gian_vang_phong_phut']} phút
  - Cảnh báo té ngã                : {data['canh_bao_te_nga']} lần
  - Cảnh báo bất động              : {data['canh_bao_bat_dong']} lần

💓 SINH HIỆU (ƯỚC TÍNH):
  - Nhịp tim trung bình : {data['nhip_tim_trung_binh']} BPM
  - Thân nhiệt          : {data['than_nhiet']} °C
  - % Thời gian đi lại  : {data['phan_tram_di_lai']}%
  - % Thời gian nghỉ    : {data['phan_tram_nghi_ngoi']}%

🤖 NHẬN XÉT TỪ TRỢ LÝ AI:
{ai_comment}

=======================================================
  Tạo tự động lúc {datetime.now().strftime('%H:%M:%S')} | Wifi-Censor v2.0
=======================================================
""".strip()

        output_path.write_text(content, encoding="utf-8")
        print(f"[ReportGenerator] Đã xuất text report: {output_path}")
        return output_path
