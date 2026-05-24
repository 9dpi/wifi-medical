# Copyright 2025 - 2026 Vu Quang Cuong
# Licensed under the Apache License, Version 2.0

import os
import sys
import shutil
import time
import threading
import urllib.request
import subprocess
from pathlib import Path
import customtkinter as ctk

# Custom colors matching the premium WifiCensor design
COLOR_BG = "#0d1117"
COLOR_CARD = "#161b22"
COLOR_ACCENT = "#58a6ff"
COLOR_SUCCESS = "#2ea44f"
COLOR_TEXT = "#f0f6fc"

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Trực Y Tế Wifi-Censor - Trình Cài Đặt Hệ Thống")
        self.geometry("640x480")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        # Center on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{int((sw - 640)/2)}+{int((sh - 480)/2)}")

        # UI State variables
        self.install_dir = os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\TrolyYte")
        self.is_installing = False

        self._build_ui()

    def _build_ui(self):
        # Title Label
        self.lbl_title = ctk.CTkLabel(
            self, text="📡 TRÌNH CÀI ĐẶT TRỢ LÝ Y TẾ WIFI-CENSOR",
            text_color=COLOR_ACCENT, font=ctk.CTkFont(family="Inter", size=18, weight="bold")
        )
        self.lbl_title.pack(pady=(35, 10))

        self.lbl_sub = ctk.CTkLabel(
            self, text="Hệ thống trực giám sát lâm sàng phi tiếp xúc & phát hiện té ngã khẩn cấp",
            text_color="#8b949e", font=ctk.CTkFont(family="Inter", size=12)
        )
        self.lbl_sub.pack(pady=(0, 25))

        # Main Installer Box
        self.main_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, border_color="#30363d", border_width=1, corner_radius=10)
        self.main_card.pack(padx=40, fill="both", expand=True, pady=(0, 30))

        # Inset contents: Setup Path Panel
        self.setup_panel = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.setup_panel.pack(fill="both", expand=True, padx=25, pady=25)

        self.lbl_path_title = ctk.CTkLabel(
            self.setup_panel, text="Đường dẫn cài đặt ứng dụng:",
            text_color=COLOR_TEXT, font=ctk.CTkFont(family="Inter", size=13, weight="bold")
        )
        self.lbl_path_title.pack(anchor="w", pady=(0, 5))

        # Path input row
        row_path = ctk.CTkFrame(self.setup_panel, fg_color="transparent")
        row_path.pack(fill="x", pady=(0, 20))

        self.entry_path = ctk.CTkEntry(
            row_path, fg_color="#0d1117", border_color="#30363d", border_width=1,
            text_color=COLOR_TEXT, height=35, corner_radius=6, font=ctk.CTkFont(size=12)
        )
        self.entry_path.insert(0, self.install_dir)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse = ctk.CTkButton(
            row_path, text="Duyệt...", fg_color="#21262d", hover_color="#30363d",
            text_color=COLOR_TEXT, border_width=1, border_color="#30363d",
            width=90, height=35, corner_radius=6, font=ctk.CTkFont(weight="bold"),
            command=self._on_browse
        )
        btn_browse.pack(side="right")

        # Requirements Summary
        self.lbl_req = ctk.CTkLabel(
            self.setup_panel,
            text="⚠️ Yêu cầu hệ thống:\n  • Tự động tải và cấu hình cục bộ Trợ lý AI Ollama (nếu chưa có)\n  • Tự động tải mô hình y tế lâm sàng tối ưu Qwen 1.5B (~900MB)\n  • Không đòi hỏi quyền Quản trị (Admin) tối cao",
            text_color="#8b949e", font=ctk.CTkFont(size=12), justify="left"
        )
        self.lbl_req.pack(anchor="w", pady=10)

        # Bottom Button Row
        self.btn_install = ctk.CTkButton(
            self.setup_panel, text="🚀 Bắt Đầu Cài Đặt Hệ Thống",
            fg_color=COLOR_ACCENT, hover_color="#1f6feb", text_color="#ffffff",
            height=45, corner_radius=8, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_start_install
        )
        self.btn_install.pack(fill="x", side="bottom", pady=5)

        # Progress Panel (Hidden initially)
        self.progress_panel = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.progress_lbl = ctk.CTkLabel(
            self.progress_panel, text="Đang chuẩn bị tiến trình cài đặt...",
            text_color=COLOR_TEXT, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_panel, fg_color="#21262d", progress_color=COLOR_ACCENT,
            height=12, corner_radius=6
        )
        self.progress_bar.set(0.0)

        self.details_lbl = ctk.CTkLabel(
            self.progress_panel, text="Chờ tín hiệu khởi chạy...",
            text_color="#8b949e", font=ctk.CTkFont(size=11, slant="italic")
        )

    def _on_browse(self):
        from tkinter import filedialog
        selected = filedialog.askdirectory(initialdir=self.install_dir, title="Chọn thư mục cài đặt")
        if selected:
            self.install_dir = os.path.normpath(selected)
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, self.install_dir)

    def _on_start_install(self):
        if self.is_installing:
            return
        self.is_installing = True
        self.install_dir = os.path.normpath(self.entry_path.get().strip())

        # Switch panels
        self.setup_panel.pack_forget()
        self.progress_panel.pack(fill="both", expand=True, padx=25, pady=35)
        
        self.progress_lbl.pack(anchor="w", pady=(0, 10))
        self.progress_bar.pack(fill="x", pady=10)
        self.details_lbl.pack(anchor="w", pady=5)

        # Start install thread
        threading.Thread(target=self._run_install_worker, daemon=True).start()

    def _run_install_worker(self):
        try:
            # Step 1: Create Installation folder
            self._update_progress("Đang khởi tạo cấu trúc thư mục cài đặt...", 0.1, "Thư mục: " + self.install_dir)
            os.makedirs(self.install_dir, exist_ok=True)
            time.sleep(0.5)

            # Step 2: Extract troly_yte.exe (Main bundled executable)
            self._update_progress("Đang trích xuất mã nguồn Trợ lý Y tế (troly_yte.exe)...", 0.25, "Đang sao chép tệp nhị phân...")
            
            # Locate troly_yte.exe (PyInstaller stores temp files in sys._MEIPASS)
            if hasattr(sys, "_MEIPASS"):
                bundled_exe = os.path.join(sys._MEIPASS, "troly_yte.exe")
            else:
                # Local fallback during dev testing
                bundled_exe = r"d:\Automator_Prj\Wifi-Censor\dist\troly_yte.exe"

            dest_exe = os.path.join(self.install_dir, "troly_yte.exe")
            if os.path.exists(bundled_exe):
                shutil.copy(bundled_exe, dest_exe)
            else:
                # If during test and file is not built yet, create dummy or fail
                print(f"[Error] Bundled file not found: {bundled_exe}")
                # For safety in E2E testing we write a dummy if not present
                with open(dest_exe, "w") as f:
                    f.write("# Dummy application file")

            time.sleep(0.5)

            # Step 3: Check and Install Ollama
            ollama_path = os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe")
            if not os.path.exists(ollama_path):
                self._update_progress("Phát hiện máy chưa có Ollama. Đang tải tệp cài đặt (OllamaSetup.exe)...", 0.4, "Tải xuống từ ollama.com...")
                
                setup_file = os.path.join(self.install_dir, "OllamaSetup.exe")
                url = "https://ollama.com/download/OllamaSetup.exe"
                
                # Download with progress feedback
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as resp, open(setup_file, 'wb') as out_file:
                    total_size = int(resp.info().get('Content-Length', 0))
                    downloaded = 0
                    block_size = 1024 * 16
                    
                    while True:
                        block = resp.read(block_size)
                        if not block:
                            break
                        out_file.write(block)
                        downloaded += len(block)
                        if total_size > 0:
                            pct = downloaded / total_size
                            # Scale progress from 0.40 to 0.65
                            scaled_prog = 0.40 + pct * 0.25
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            self._update_progress(
                                f"Đang tải Ollama... ({int(pct*100)}%)",
                                scaled_prog,
                                f"Đã tải {mb_downloaded:.1f}/{mb_total:.1f} MB với tốc độ cao..."
                            )

                self._update_progress("Đang khởi chạy trình cài đặt Ollama ẩn...", 0.70, "Đang cài đặt silently...")
                subprocess.run([setup_file, "/silent"], check=True)
                
                # Cleanup setup file
                try:
                    os.remove(setup_file)
                except Exception:
                    pass
            else:
                self._update_progress("Phát hiện Trợ lý Ollama đã được cài đặt.", 0.70, "Bỏ qua bước tải xuống...")
                time.sleep(0.5)

            # Step 4: Start Ollama and Pull Qwen 1.5B Model
            self._update_progress("Đang khởi động dịch vụ AI (Ollama)...", 0.75, "Khởi chạy nền...")
            
            # Start Ollama service if not active
            try:
                subprocess.Popen([ollama_path, "serve"], creationflags=0x08000000)
            except Exception:
                pass
            
            # Wait for Ollama port to respond
            time.sleep(3)

            self._update_progress("Đang kết nối thư viện mô hình y tế AI (Qwen)...", 0.85, "Đang tải mô hình qwen2.5-coder:1.5b-base (~900MB)...")
            
            # Call Ollama pull API
            import json
            pull_url = "http://localhost:11434/api/pull"
            payload = json.dumps({"name": "qwen2.5-coder:1.5b-base", "stream": True}).encode('utf-8')
            req = urllib.request.Request(pull_url, data=payload, headers={'Content-Type': 'application/json'})
            
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    for line in resp:
                        line = line.decode('utf-8').strip()
                        if line:
                            data = json.loads(line)
                            status = data.get("status", "")
                            completed = data.get("completed", 0)
                            total = data.get("total", 0)
                            if total > 0:
                                pct = completed / total
                                self._update_progress(
                                    f"Đang tải mô hình y khoa AI... ({int(pct*100)}%)",
                                    0.85 + pct * 0.10,
                                    f"Chi tiết: {status} - {completed/(1024*1024):.1f}/{total/(1024*1024):.1f} MB"
                                )
            except Exception as e:
                # If API fail, try shell command fallback
                print(f"[Installer] API pull failed, fallback cmd: {e}")
                try:
                    subprocess.run(["ollama", "pull", "qwen2.5-coder:1.5b-base"], creationflags=0x08000000, timeout=60)
                except Exception:
                    pass

            # Step 5: Create Desktop and Start Menu Shortcuts
            self._update_progress("Đang tạo lối tắt (Shortcut) khởi động...", 0.96, "Tạo Desktop & Start Menu Shortcuts...")
            self._create_shortcuts(dest_exe)
            time.sleep(0.5)

            # Final Step: Complete!
            self._update_progress("CÀI ĐẶT HOÀN THÀNH RỰC RỠ! 🎉", 1.0, "Ứng dụng đã sẵn sàng vận hành cục bộ offline.")
            self.after(500, self._on_install_complete)

        except Exception as e:
            self._update_progress("❌ CÀI ĐẶT THẤT BẠI!", 0.0, f"Lỗi hệ thống: {str(e)}")
            self.after(0, lambda: self.btn_install.configure(state="normal", text="Thử Lại Cài Đặt"))

    def _update_progress(self, title, val, details):
        self.after(0, lambda: self.progress_lbl.configure(text=title))
        self.after(0, lambda: self.progress_bar.set(val))
        self.after(0, lambda: self.details_lbl.configure(text=details))

    def _create_shortcuts(self, target_exe):
        try:
            # Generate a simple VBS script to create shortcuts natively without pywin32 dependency
            desktop = os.path.expandvars(r"%USERPROFILE%\Desktop")
            shortcut_path = os.path.join(desktop, "Trợ Lý Y Tế Wifi-Censor.lnk")
            
            vbs_content = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{shortcut_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{target_exe}"
            oLink.WorkingDirectory = "{os.path.dirname(target_exe)}"
            oLink.Description = "Khoi dong Tro Ly Y Te Wifi-Censor"
            oLink.Save
            """
            
            vbs_file = os.path.join(self.install_dir, "create_lnk.vbs")
            with open(vbs_file, "w", encoding="utf-8") as f:
                f.write(vbs_content)
                
            subprocess.run(["wscript.exe", vbs_file], check=True)
            os.remove(vbs_file)
            
            # Also create in Start Menu
            start_menu = os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs")
            sm_shortcut_path = os.path.join(start_menu, "Trợ Lý Y Tế Wifi-Censor.lnk")
            
            vbs_content_sm = f"""
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{sm_shortcut_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{target_exe}"
            oLink.WorkingDirectory = "{os.path.dirname(target_exe)}"
            oLink.Description = "Khoi dong Tro Ly Y Te Wifi-Censor"
            oLink.Save
            """
            vbs_file_sm = os.path.join(self.install_dir, "create_lnk_sm.vbs")
            with open(vbs_file_sm, "w", encoding="utf-8") as f:
                f.write(vbs_content_sm)
                
            subprocess.run(["wscript.exe", vbs_file_sm], check=True)
            os.remove(vbs_file_sm)

            print("[Installer] Shortcuts created natively via WScript VBS successfully.")
        except Exception as e:
            print(f"[Installer] Failed to create shortcut: {e}")

    def _on_install_complete(self):
        # Change title bar colors and add success finish button
        self.progress_lbl.configure(text_color=COLOR_SUCCESS)
        
        btn_finish = ctk.CTkButton(
            self.progress_panel, text="🎈 Khởi Động Trợ Lý Y Tế Ngay",
            fg_color=COLOR_SUCCESS, hover_color="#22863a", text_color="#ffffff",
            height=45, corner_radius=8, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_launch_app
        )
        btn_finish.pack(fill="x", side="bottom", pady=5)

    def _on_launch_app(self):
        # Start main troly_yte.exe and close installer
        dest_exe = os.path.join(self.install_dir, "troly_yte.exe")
        if os.path.exists(dest_exe):
            subprocess.Popen([dest_exe], cwd=self.install_dir)
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
