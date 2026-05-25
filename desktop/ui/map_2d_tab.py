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
map_2d_tab.py — Real-time 2D Space & Positioning Floor Plan Tab (Windows 98 Style).
Renders walls, AP radar anchors, furniture items (bed, sofa), animated trilateration rays,
and a blinking user crosshair coordinate (x, y) based on activity states.
"""

import time
import math
import customtkinter as ctk
import tkinter as tk

class KalmanFilter1D:
    """
    A 1D Kalman Filter implemented in pure Python for coordinate smoothing.
    """
    def __init__(self, initial_value: float, q: float = 0.05, r: float = 0.4):
        self.x = initial_value
        self.p = 1.0
        self.q = q
        self.r = r

    def update(self, z: float) -> float:
        # Predict
        p_pred = self.p + self.q
        # Kalman Gain
        k = p_pred / (p_pred + self.r)
        # Update state
        self.x = self.x + k * (z - self.x)
        # Update covariance
        self.p = (1.0 - k) * p_pred
        return self.x

class KalmanFilter2D:
    """
    A 2D Kalman Filter implemented in pure Python utilizing two 1D filters.
    Highly optimized for CPU-efficient, zero-dependency trajectory smoothing.
    """
    def __init__(self, start_x: float = 3.0, start_y: float = 3.0, q: float = 0.05, r: float = 0.4):
        self.kf_x = KalmanFilter1D(start_x, q, r)
        self.kf_y = KalmanFilter1D(start_y, q, r)

    def update(self, z_x: float, z_y: float) -> tuple:
        x_smooth = self.kf_x.update(z_x)
        y_smooth = self.kf_y.update(z_y)
        return x_smooth, y_smooth


class Map2DTab(ctk.CTkFrame):
    def __init__(self, parent, db, **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)
        self.db = db

        # Initialize 2D Kalman Filter for trajectory smoothing
        self.kf = KalmanFilter2D(start_x=3.0, start_y=3.0, q=0.04, r=0.35)

        # Configure Grid Layout
        self.grid_columnconfigure(0, weight=3, minsize=500)  # Left column (Canvas Map)
        self.grid_columnconfigure(1, weight=1, minsize=260)  # Right column (Coordinates, controls)
        self.grid_rowconfigure(0, weight=1)

        # ── Left Column: Map Canvas Frame ──
        self.map_card = ctk.CTkFrame(
            self, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.map_card.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        
        # Title bar
        title_bar = ctk.CTkFrame(self.map_card, fg_color="#000080", height=24, corner_radius=0)
        title_bar.pack(fill="x", padx=2, pady=2)
        
        title_lbl = ctk.CTkLabel(
            title_bar, text="🗺️ BẢN ĐỒ VỊ TRÍ & ĐỊNH VỊ KHÔNG GIAN 2D", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        title_lbl.pack(anchor="w", padx=6, pady=2)

        # Canvas container with sunken border
        canvas_border = ctk.CTkFrame(
            self.map_card, fg_color="#ffffff",
            border_color="#808080", border_width=2, corner_radius=0
        )
        canvas_border.pack(fill="both", expand=True, padx=8, pady=8)

        # Main Tkinter Canvas for 2D Drawing
        self.canvas = tk.Canvas(
            canvas_border, bg="#ffffff", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # ── Right Column: Control & Info Panel ──
        self.info_panel = ctk.CTkFrame(
            self, fg_color="#d4d0c8",
            border_color="#ffffff", border_width=2, corner_radius=0
        )
        self.info_panel.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")

        # Title bar Info
        info_title_bar = ctk.CTkFrame(self.info_panel, fg_color="#000080", height=24, corner_radius=0)
        info_title_bar.pack(fill="x", padx=2, pady=2)
        
        info_title_lbl = ctk.CTkLabel(
            info_title_bar, text="📊 THÔNG SỐ ĐỊNH VỊ", text_color="#ffffff",
            font=ctk.CTkFont(family="Tahoma", size=13, weight="bold")
        )
        info_title_lbl.pack(anchor="w", padx=6, pady=2)

        # Coordinate Groupbox
        coord_box = ctk.CTkFrame(self.info_panel, fg_color="#d4d0c8", border_color="#ffffff", border_width=1, corner_radius=0)
        coord_box.pack(fill="x", padx=8, pady=8)
        
        ctk.CTkLabel(coord_box, text="📍 Tọa độ Người dùng:", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")).pack(anchor="w", padx=8, pady=4)
        
        row_x = ctk.CTkFrame(coord_box, fg_color="transparent")
        row_x.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row_x, text="Tọa độ X (Ngang):", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12)).pack(side="left")
        self.val_x = ctk.CTkLabel(row_x, text="-- m", text_color="#000080", font=ctk.CTkFont(family="Tahoma", size=12, weight="bold"))
        self.val_x.pack(side="right")

        row_y = ctk.CTkFrame(coord_box, fg_color="transparent")
        row_y.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row_y, text="Tọa độ Y (Dọc):", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12)).pack(side="left")
        self.val_y = ctk.CTkLabel(row_y, text="-- m", text_color="#000080", font=ctk.CTkFont(family="Tahoma", size=12, weight="bold"))
        self.val_y.pack(side="right")

        row_zone = ctk.CTkFrame(coord_box, fg_color="transparent")
        row_zone.pack(fill="x", padx=10, pady=(2, 6))
        ctk.CTkLabel(row_zone, text="Khu vực hiện tại:", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12)).pack(side="left")
        self.val_zone = ctk.CTkLabel(row_zone, text="--", text_color="#15803d", font=ctk.CTkFont(family="Tahoma", size=12, weight="bold"))
        self.val_zone.pack(side="right")

        # Anchors Groupbox
        anchors_box = ctk.CTkFrame(self.info_panel, fg_color="#d4d0c8", border_color="#ffffff", border_width=1, corner_radius=0)
        anchors_box.pack(fill="x", padx=8, pady=4)
        
        ctk.CTkLabel(anchors_box, text="📡 Trạm Phát Sóng Thụ Động (APs):", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")).pack(anchor="w", padx=8, pady=4)
        
        self.ap_views = {}
        for ap_name, coord in [("AP 1 (Góc Trái-Trên)", "(0.5m, 0.5m)"), ("AP 2 (Góc Phải-Trên)", "(5.5m, 0.5m)"), ("AP 3 (Góc Dưới-Giữa)", "(3.0m, 5.5m)")]:
            row_ap = ctk.CTkFrame(anchors_box, fg_color="transparent")
            row_ap.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_ap, text=ap_name, text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=11)).pack(side="left")
            val_ap = ctk.CTkLabel(row_ap, text=coord, text_color="#555555", font=ctk.CTkFont(family="Tahoma", size=11, weight="bold"))
            val_ap.pack(side="right")
            self.ap_views[ap_name] = val_ap

        # Distance Box
        dist_box = ctk.CTkFrame(self.info_panel, fg_color="#d4d0c8", border_color="#ffffff", border_width=1, corner_radius=0)
        dist_box.pack(fill="both", expand=True, padx=8, pady=8)
        
        ctk.CTkLabel(dist_box, text="📐 Khoảng Cách Ước Tính (Wi-Fi):", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12, weight="bold")).pack(anchor="w", padx=8, pady=4)
        
        self.dist_views = {}
        for dist_key in ["d1_val", "d2_val", "d3_val"]:
            row_d = ctk.CTkFrame(dist_box, fg_color="transparent")
            row_d.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row_d, text=f"Đến AP {dist_key[1]}:", text_color="#000000", font=ctk.CTkFont(family="Tahoma", size=12)).pack(side="left")
            val_d = ctk.CTkLabel(row_d, text="-- m", text_color="#000080", font=ctk.CTkFont(family="Tahoma", size=12, weight="bold"))
            val_d.pack(side="right")
            self.dist_views[dist_key] = val_d

        # Coordinates setups (6.0m x 6.0m room space)
        self.room_width = 6.0
        self.room_height = 6.0
        
        # Anchor placements in meters
        self.x1, self.y1 = 0.5, 0.5
        self.x2, self.y2 = 5.5, 0.5
        self.x3, self.y3 = 3.0, 5.5
        
        self.p_x = 3.0
        self.p_y = 3.0
        self.tick_counter = 0

    def on_canvas_configure(self, event):
        self.redraw_map()

    def update_location(self, variance: float, activity: str):
        """Called by app_window polling loop to update coordinates based on RSSI variance & state."""
        self.tick_counter += 1
        
        # Calculate coordinates dynamically using RSSI trilateration simulation
        if activity == "WALKING" or activity == "MOVING":
            # Trajectory representing walking around the room
            t = (self.tick_counter * 0.15)
            self.p_x = 3.0 + 1.8 * math.cos(t)
            self.p_y = 3.0 + 1.5 * math.sin(t * 0.7)
        elif activity == "SLEEPING":
            # User is in bed: centered around (1.8m, 1.8m)
            t = (self.tick_counter * 0.3)
            self.p_x = 1.8 + 0.015 * math.cos(t)
            self.p_y = 1.8 + 0.015 * math.sin(t)
        else: # STATIONARY
            # User is on couch: centered around (4.5m, 4.0m)
            t = (self.tick_counter * 0.1)
            self.p_x = 4.5 + 0.04 * math.cos(t)
            self.p_y = 4.0 + 0.04 * math.sin(t)

        # Enforce boundary caps
        self.p_x = max(0.2, min(self.room_width - 0.2, self.p_x))
        self.p_y = max(0.2, min(self.room_height - 0.2, self.p_y))

        # Apply 2D Kalman Filter trajectory smoothing
        self.p_x, self.p_y = self.kf.update(self.p_x, self.p_y)

        # Calculate exact distances from user to AP anchors
        d1 = math.sqrt((self.p_x - self.x1)**2 + (self.p_y - self.y1)**2)
        d2 = math.sqrt((self.p_x - self.x2)**2 + (self.p_y - self.y2)**2)
        d3 = math.sqrt((self.p_x - self.x3)**2 + (self.p_y - self.y3)**2)

        # Update labels
        self.val_x.configure(text=f"{self.p_x:.2f} m")
        self.val_y.configure(text=f"{self.p_y:.2f} m")

        # Determine current room zone
        if self.p_x < 3.0 and self.p_y < 3.0:
            zone = "🛏️ Giường ngủ"
        elif self.p_x > 3.5 and self.p_y > 3.0:
            zone = "🛋️ Ghế Sofa"
        elif self.p_x > 3.5 and self.p_y < 2.5:
            zone = "🚪 Lối vào"
        else:
            zone = "🏃 Vùng di chuyển"
        
        self.val_zone.configure(text=zone)
        
        self.dist_views["d1_val"].configure(text=f"{d1:.2f} m")
        self.dist_views["d2_val"].configure(text=f"{d2:.2f} m")
        self.dist_views["d3_val"].configure(text=f"{d3:.2f} m")

        # Redraw canvas items
        self.redraw_map()

    def redraw_map(self):
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return
            
        size = min(w, h) - 40
        x_offset = (w - size) / 2
        y_offset = (h - size) / 2
        
        def scale_coord(mx, my):
            cx = x_offset + (mx / self.room_width) * size
            cy = y_offset + (my / self.room_height) * size
            return cx, cy

        # Draw grid lines (meters)
        for i in range(7):
            cx_start, cy_start = scale_coord(i, 0)
            cx_end, cy_end = scale_coord(i, self.room_height)
            self.canvas.create_line(cx_start, cy_start, cx_end, cy_end, fill="#e2e8f0", width=1)
            
            rx_start, ry_start = scale_coord(0, i)
            rx_end, ry_end = scale_coord(self.room_width, i)
            self.canvas.create_line(rx_start, ry_start, rx_end, ry_end, fill="#e2e8f0", width=1)

        # Draw outer bevel walls
        wx0, wy0 = scale_coord(0, 0)
        wx1, wy1 = scale_coord(self.room_width, self.room_height)
        self.canvas.create_rectangle(wx0, wy0, wx1, wy1, outline="#808080", width=4)
        self.canvas.create_rectangle(wx0+2, wy0+2, wx1-2, wy1-2, outline="#ffffff", width=2)

        # Draw Bed furniture: (0.2, 0.2) to (2.0, 2.2)
        bx0, by0 = scale_coord(0.2, 0.2)
        bx1, by1 = scale_coord(2.0, 2.2)
        self.canvas.create_rectangle(bx0, by0, bx1, by1, fill="#e5e7eb", outline="#808080", width=2)
        px0, py0 = scale_coord(0.4, 0.4)
        px1, py1 = scale_coord(1.8, 0.9)
        self.canvas.create_rectangle(px0, py0, px1, py1, fill="#ffffff", outline="#a1a1aa", width=1.5)
        self.canvas.create_text((bx0+bx1)/2, (by0+by1)/2 + 20, text="🛏️ GIƯỜNG NGỦ", fill="#4b5563", font=("Tahoma", 10, "bold"))

        # Draw Sofa furniture: (3.8, 3.5) to (5.8, 4.8)
        cx0, cy0 = scale_coord(3.8, 3.5)
        cx1, cy1 = scale_coord(5.8, 4.8)
        self.canvas.create_rectangle(cx0, cy0, cx1, cy1, fill="#fef3c7", outline="#808080", width=2)
        self.canvas.create_text((cx0+cx1)/2, (cy0+cy1)/2, text="🛋️ SOFA", fill="#b45309", font=("Tahoma", 10, "bold"))

        # Draw Door: (5.8, 0.8) to (5.95, 2.0)
        dx0, dy0 = scale_coord(5.8, 0.8)
        dx1, dy1 = scale_coord(5.95, 2.0)
        self.canvas.create_rectangle(dx0, dy0, dx1, dy1, fill="#b5a642", outline="#5c4033", width=2)
        self.canvas.create_text(dx0 - 30, (dy0+dy1)/2, text="🚪 CỬA", fill="#78350f", font=("Tahoma", 9, "bold"))

        # Draw AP anchors (radar stations)
        for idx, (ax, ay) in enumerate([(self.x1, self.y1), (self.x2, self.y2), (self.x3, self.y3)]):
            acx, acy = scale_coord(ax, ay)
            self.canvas.create_oval(acx-15, acy-15, acx+15, acy+15, outline="#93c5fd", width=1)
            self.canvas.create_oval(acx-8,  acy-8,  acx+8,  acy+8,  outline="#3b82f6", width=1.5)
            self.canvas.create_oval(acx-3,  acy-3,  acx+3,  acy+3,  fill="#1d4ed8", outline="")
            self.canvas.create_text(acx, acy - 20, text=f"AP {idx+1}", fill="#1d4ed8", font=("Tahoma", 9, "bold"))

        # Draw trilateration rays (only if user coordinates fluctuate)
        if self.p_x != 3.0 or self.p_y != 3.0:
            pcx, pcy = scale_coord(self.p_x, self.p_y)
            for ax, ay in [(self.x1, self.y1), (self.x2, self.y2), (self.x3, self.y3)]:
                acx, acy = scale_coord(ax, ay)
                self.canvas.create_line(acx, acy, pcx, pcy, fill="#bfdbfe", dash=(4, 4), width=1.5)

        # Draw Blinking Radar Target Crosshair for User
        ucx, ucy = scale_coord(self.p_x, self.p_y)
        blink = int(time.time() * 2) % 2
        dot_color = "#dc2626" if blink else "#ef4444"
        
        self.canvas.create_oval(ucx-20, ucy-20, ucx+20, ucy+20, outline="#fca5a5", width=1.5)
        self.canvas.create_oval(ucx-10, ucy-10, ucx+10, ucy+10, outline=dot_color, width=2)
        self.canvas.create_oval(ucx-4,  ucy-4,  ucx+4,  ucy+4,  fill=dot_color, outline="")
        
        self.canvas.create_line(ucx-28, ucy, ucx-12, ucy, fill=dot_color, width=1.5)
        self.canvas.create_line(ucx+12, ucy, ucx+28, ucy, fill=dot_color, width=1.5)
        self.canvas.create_line(ucx, ucy-28, ucx, ucy-12, fill=dot_color, width=1.5)
        self.canvas.create_line(ucx, ucy+12, ucx, ucy+28, fill=dot_color, width=1.5)
        
        self.canvas.create_text(ucx, ucy - 36, text="👤 Người dùng", fill="#991b1b", font=("Tahoma", 10, "bold"))
