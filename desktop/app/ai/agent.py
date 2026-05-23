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
agent.py — Vòng lặp AI Agent ReAct (Reason → Act → Observe).

Kiến trúc:
  - System prompt tiếng Việt, phù hợp với người cao tuổi và gia đình
  - Vòng lặp tối đa 5 bước tool calling để tránh vòng lặp vô tận
  - Thread-safe: chạy trong daemon thread, trả kết quả qua callback
  - Hỗ trợ cả interactive chat (người dùng gõ) và event-driven mode (hệ thống trigger)
"""

import json
import time
import threading
from typing import Optional, List, Dict, Callable
from desktop.app.ai.ollama_manager import OllamaManager, PREFERRED_MODELS
from desktop.app.ai.tools import ToolExecutor, TOOL_DEFINITIONS


# System prompt tiếng Việt
SYSTEM_PROMPT = """Bạn là Trợ lý Sức khỏe Thông minh của hệ thống Wifi-Censor, 
được thiết kế để hỗ trợ theo dõi và bảo vệ người cao tuổi sống một mình.

Nguyên tắc trả lời:
- Luôn trả lời bằng tiếng Việt, đơn giản và dễ hiểu
- Ưu tiên sự rõ ràng hơn kỹ thuật — tránh thuật ngữ chuyên môn phức tạp
- Khi phát hiện tình huống nguy hiểm, hãy thông báo rõ ràng và kêu gọi hành động
- Khi thấy dữ liệu bình thường, hãy trấn an và tóm tắt ngắn gọn
- Khi cần dữ liệu thực tế, hãy dùng các công cụ (tools) được cung cấp để tra cứu

Vai trò của bạn:
1. Trả lời câu hỏi về tình trạng sức khỏe và hoạt động
2. Phân tích xu hướng và đưa ra gợi ý chăm sóc
3. Giải thích nguyên nhân các cảnh báo đã xảy ra
4. Hỗ trợ điều chỉnh hệ thống khi cần thiết

Lưu ý quan trọng: Bạn KHÔNG phải bác sĩ. Luôn khuyên người dùng hỏi ý kiến bác sĩ 
khi có vấn đề sức khỏe nghiêm trọng."""


class WifiCensorAgent:
    """
    AI Agent chính của Wifi-Censor.
    
    Sử dụng:
        agent = WifiCensorAgent(ollama, tool_executor)
        agent.chat_async("Nhịp tim hôm nay thế nào?", on_token=..., on_done=...)
    """

    MAX_TOOL_ROUNDS = 5   # Tối đa 5 vòng tool calling để tránh vòng vô tận
    TOOL_TIMEOUT_S  = 10  # Timeout mỗi lần gọi tool

    def __init__(self, ollama: OllamaManager, tool_executor: ToolExecutor):
        self.ollama = ollama
        self.tools = tool_executor
        self._history: List[Dict] = []  # Lịch sử hội thoại trong phiên hiện tại
        self._lock = threading.Lock()

    # ── Public API ─────────────────────────────────────────────────────────────

    def chat_async(
        self,
        user_message: str,
        on_token: Callable[[str], None],
        on_done: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Gửi tin nhắn của người dùng và xử lý trong thread nền.
        Kết quả được stream về qua on_token(), kết thúc bằng on_done().
        """
        thread = threading.Thread(
            target=self._chat_worker,
            args=(user_message, on_token, on_done, on_error),
            daemon=True
        )
        thread.start()

    def ask_sync(self, prompt: str, system_override: str = "") -> str:
        """
        Gửi câu hỏi nội bộ (không phải từ người dùng) và chờ trả lời đồng bộ.
        Dùng cho fall_verifier và report_generator — không qua tool calling.
        """
        system = system_override or SYSTEM_PROMPT
        return self.ollama.generate(prompt=prompt, system=system)

    def reset_history(self) -> None:
        """Xóa lịch sử hội thoại (bắt đầu phiên mới)."""
        with self._lock:
            self._history.clear()

    def get_history(self) -> List[Dict]:
        """Trả về bản sao lịch sử hội thoại hiện tại."""
        with self._lock:
            return list(self._history)

    # ── Internal: ReAct Loop ──────────────────────────────────────────────────

    def _chat_worker(
        self,
        user_message: str,
        on_token: Callable[[str], None],
        on_done: Callable[[str], None],
        on_error: Optional[Callable[[str], None]]
    ) -> None:
        """
        Vòng lặp ReAct chạy trong thread nền:
        1. Thêm tin nhắn người dùng vào history
        2. Gửi cho Ollama (với tools) — không streaming để xử lý tool calls
        3. Nếu AI muốn gọi tool → thực thi → gửi kết quả lại
        4. Lặp tối đa MAX_TOOL_ROUNDS lần
        5. Khi AI trả về tin nhắn cuối (không có tool call) → stream về UI
        """
        try:
            with self._lock:
                # Thêm tin nhắn người dùng
                self._history.append({
                    "role": "user",
                    "content": user_message
                })
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(self._history)

            # Vòng lặp ReAct
            for round_num in range(self.MAX_TOOL_ROUNDS):
                response = self.ollama.chat(messages=messages, tools=TOOL_DEFINITIONS)
                msg = response.get("message", {})
                tool_calls = msg.get("tool_calls", [])

                if not tool_calls:
                    # Không còn tool call — đây là câu trả lời cuối
                    final_text = msg.get("content", "").strip()
                    if not final_text:
                        final_text = "Xin lỗi, tôi không thể xử lý yêu cầu này."

                    # Thêm câu trả lời vào history
                    with self._lock:
                        self._history.append({"role": "assistant", "content": final_text})

                    # Stream từng ký tự ra UI (giả lập streaming vì chat() không stream)
                    self._pseudo_stream(final_text, on_token)
                    on_done(final_text)
                    return

                # Có tool calls — thực thi từng tool
                # Thêm assistant message (với tool_calls) vào history
                messages.append(msg)

                tool_results = []
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    tool_name = fn.get("name", "")
                    raw_args = fn.get("arguments", {})

                    # Parse arguments nếu là string JSON
                    if isinstance(raw_args, str):
                        try:
                            raw_args = json.loads(raw_args)
                        except Exception:
                            raw_args = {}

                    print(f"[Agent] Tool call [{round_num+1}]: {tool_name}({raw_args})")

                    # Thông báo UI đang xử lý
                    try:
                        on_token(f"\n🔧 Đang tra cứu: **{tool_name}**...\n")
                    except Exception:
                        pass

                    # Thực thi tool
                    result_str = self.tools.execute(tool_name, raw_args)
                    print(f"[Agent] Tool result: {result_str[:100]}...")

                    tool_results.append({
                        "role": "tool",
                        "content": result_str,
                    })

                # Thêm tất cả tool results vào messages
                messages.extend(tool_results)

            # Vượt quá giới hạn tool rounds — trả lời mặc định
            fallback = "Xin lỗi, tôi đã tìm kiếm quá nhiều lần mà chưa có kết quả rõ ràng. Vui lòng thử lại với câu hỏi khác."
            with self._lock:
                self._history.append({"role": "assistant", "content": fallback})
            self._pseudo_stream(fallback, on_token)
            on_done(fallback)

        except Exception as e:
            error_msg = f"Đã xảy ra lỗi kỹ thuật: {str(e)}"
            print(f"[Agent] Lỗi: {e}")
            if on_error:
                try:
                    on_error(error_msg)
                except Exception:
                    pass
            else:
                try:
                    on_done(error_msg)
                except Exception:
                    pass

    def _pseudo_stream(self, text: str, on_token: Callable[[str], None]) -> None:
        """
        Giả lập streaming bằng cách chia text thành các chunk nhỏ.
        Tạo cảm giác AI đang 'gõ' câu trả lời — giúp UI cảm giác nhanh hơn.
        """
        # Chia theo từ để giữ nguyên nghĩa
        words = text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            try:
                on_token(chunk)
            except Exception:
                break
            time.sleep(0.02)  # 20ms mỗi từ ≈ 50 từ/giây — cảm giác tự nhiên
