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
ollama_manager.py — Quản lý kết nối Ollama REST API.

Hỗ trợ:
  - Kiểm tra health Ollama và danh sách model
  - Tự động chọn model tốt nhất có trong máy (ưu tiên gemma4:e4b)
  - Non-streaming và streaming generation
  - Chat với lịch sử hội thoại
  - Tool calling (function calling) chuẩn Ollama API
"""

import json
import time
import threading
from typing import Optional, List, Dict, Generator, Callable
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode


# Thứ tự ưu tiên model — sẽ chọn model đầu tiên tìm thấy trong danh sách
PREFERRED_MODELS = [
    "gemma4:e4b",
    "gemma3:4b",
    "gemma3:2b",
    "llama3.2:3b",
    "llama3.1:8b",
]


class OllamaManager:
    """
    Quản lý kết nối với Ollama local REST API.
    Tất cả HTTP calls dùng urllib tiêu chuẩn — không cần thư viện ngoài.
    """

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._selected_model: Optional[str] = None
        self._available_models: List[str] = []
        self._lock = threading.Lock()

    # ── Health & Model Discovery ──────────────────────────────────────────────

    def health_check(self) -> bool:
        """Kiểm tra Ollama đang chạy và phản hồi."""
        try:
            req = Request(f"{self.base_url}/api/tags")
            with urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Lấy danh sách tên model đã cài trong Ollama."""
        try:
            req = Request(f"{self.base_url}/api/tags")
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._available_models = [m["name"] for m in data.get("models", [])]
                return self._available_models
        except Exception as e:
            print(f"[OllamaManager] Lỗi lấy danh sách model: {e}")
            return []

    def select_best_model(self) -> Optional[str]:
        """
        Chọn model tốt nhất có trong máy theo thứ tự ưu tiên PREFERRED_MODELS.
        Kết quả được cache trong self._selected_model.
        """
        available = self.list_models()
        if not available:
            return None

        for preferred in PREFERRED_MODELS:
            for installed in available:
                # So sánh không phân biệt hoa/thường, bỏ qua tag :latest
                if preferred.lower() == installed.lower():
                    self._selected_model = installed
                    print(f"[OllamaManager] Đã chọn model: {self._selected_model}")
                    return self._selected_model

        # Nếu không khớp với preferred list, dùng model đầu tiên có
        self._selected_model = available[0]
        print(f"[OllamaManager] Fallback model: {self._selected_model}")
        return self._selected_model

    @property
    def model(self) -> str:
        """Model đang dùng, tự động select nếu chưa có."""
        if not self._selected_model:
            self.select_best_model()
        return self._selected_model or "gemma4:e4b"

    # ── Core API Calls ────────────────────────────────────────────────────────

    def _post(self, endpoint: str, payload: dict) -> dict:
        """HTTP POST tới Ollama API, trả về JSON dict."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        body = json.dumps(payload).encode("utf-8")
        req = Request(url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post_stream(self, endpoint: str, payload: dict) -> Generator[dict, None, None]:
        """HTTP POST streaming — yield từng JSON chunk."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        payload = {**payload, "stream": True}
        body = json.dumps(payload).encode("utf-8")
        req = Request(url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=self.timeout) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    # ── Generate API ──────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system: str = "",
        context: Optional[list] = None
    ) -> str:
        """
        Tạo câu trả lời đơn giản (không streaming, không lịch sử chat).
        Phù hợp cho phân tích nội bộ (fall verifier, daily report).
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,   # Thấp để câu trả lời nhất quán, ít hallucination
                    "num_predict": 512,
                }
            }
            if system:
                payload["system"] = system
            if context:
                payload["context"] = context

            result = self._post("/api/generate", payload)
            return result.get("response", "").strip()

        except Exception as e:
            print(f"[OllamaManager] Lỗi generate: {e}")
            return ""

    # ── Chat API (với lịch sử hội thoại) ─────────────────────────────────────

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[dict]] = None,
    ) -> dict:
        """
        Chat API với lịch sử hội thoại.
        Trả về dict phản hồi đầy đủ (bao gồm tool_calls nếu có).

        messages format: [{"role": "user"|"assistant"|"system", "content": "..."}]
        tools format: Danh sách tool definitions theo chuẩn Ollama function calling
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_predict": 1024,
                }
            }
            if tools:
                payload["tools"] = tools

            result = self._post("/api/chat", payload)
            return result

        except Exception as e:
            print(f"[OllamaManager] Lỗi chat: {e}")
            return {"message": {"role": "assistant", "content": "Xin lỗi, tôi đang gặp sự cố kỹ thuật."}}

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        on_token: Callable[[str], None],
        on_done: Callable[[str], None],
        tools: Optional[List[dict]] = None,
    ) -> None:
        """
        Streaming chat — gọi on_token() mỗi lần nhận được token mới.
        Gọi on_done(full_text) khi hoàn thành.
        Chạy trong thread nền để không block UI.

        Sử dụng:
            manager.chat_stream(messages, on_token=update_label, on_done=save_history)
        """
        def _stream_worker():
            full_text = ""
            try:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 1024,
                    }
                }
                if tools:
                    payload["tools"] = tools

                for chunk in self._post_stream("/api/chat", payload):
                    msg = chunk.get("message", {})
                    token = msg.get("content", "")
                    if token:
                        full_text += token
                        try:
                            on_token(token)
                        except Exception:
                            pass  # UI có thể đã đóng

                    if chunk.get("done", False):
                        break

            except Exception as e:
                print(f"[OllamaManager] Lỗi streaming: {e}")
                full_text = full_text or "Xin lỗi, tôi đang gặp sự cố kỹ thuật."

            try:
                on_done(full_text)
            except Exception:
                pass

        thread = threading.Thread(target=_stream_worker, daemon=True)
        thread.start()

    # ── Utility ───────────────────────────────────────────────────────────────

    def get_status_text(self) -> str:
        """Trả về chuỗi trạng thái ngắn gọn hiển thị trên UI."""
        if not self.health_check():
            return "AI Offline ⚠️"
        model = self.model
        return f"{model} ✅ Online" if model else "Không có model"

    def warm_up(self) -> bool:
        """
        Gửi một prompt ngắn để 'warm up' model vào GPU VRAM.
        Gọi một lần khi khởi động để tránh độ trễ lần đầu.
        """
        try:
            print(f"[OllamaManager] Đang warm-up model {self.model}...")
            t0 = time.time()
            result = self.generate("Xin chào", system="Bạn là trợ lý.")
            elapsed = time.time() - t0
            print(f"[OllamaManager] Warm-up hoàn thành trong {elapsed:.1f}s. Phản hồi: '{result[:50]}'")
            return True
        except Exception as e:
            print(f"[OllamaManager] Warm-up thất bại: {e}")
            return False
