"""
Telegram Alert Manager - Gửi cảnh báo vi phạm qua Telegram
"""
import requests
import threading
import time
from datetime import datetime
from typing import Optional
import os

VIOLATION_EMOJI = {
    'NO-Gloves':      '🧤',
    'NO-Goggles':     '🥽',
    'NO-Hardhat':     '⛑️',
    'NO-Mask':        '😷',
    'NO-Safety Vest': '🦺',
    'Fall-Detected':  '🚨',
}

VIOLATION_LABELS_VI = {
    'NO-Gloves':      'Không đeo găng tay',
    'NO-Goggles':     'Không đeo kính bảo hộ',
    'NO-Hardhat':     'Không đội mũ bảo hộ',
    'NO-Mask':        'Không đeo khẩu trang',
    'NO-Safety Vest': 'Không mặc áo phản quang',
    'Fall-Detected':  'Phát hiện ngã/tai nạn',
}


class TelegramAlerter:
    def __init__(self, bot_token: str = '', chat_id: str = '',
                 cooldown_seconds: int = 30):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cooldown = cooldown_seconds
        self._last_sent: dict = {}   # violation_type -> timestamp
        self._lock = threading.Lock()
        self.enabled = bool(bot_token and chat_id)

    def update_config(self, bot_token: str, chat_id: str, cooldown: int = 30):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cooldown = cooldown
        self.enabled = bool(bot_token and chat_id)

    def _can_send(self, violation_type: str) -> bool:
        with self._lock:
            last = self._last_sent.get(violation_type, 0)
            return (time.time() - last) >= self.cooldown

    def _mark_sent(self, violation_type: str):
        with self._lock:
            self._last_sent[violation_type] = time.time()

    def send_violation_alert(self, violation_type: str, image_path: Optional[str],
                              source_name: str, confidence: float,
                              callback=None) -> None:
        """Gửi cảnh báo async (không block UI)"""
        if not self.enabled:
            return
        if not self._can_send(violation_type):
            return
        self._mark_sent(violation_type)

        threading.Thread(
            target=self._send_async,
            args=(violation_type, image_path, source_name, confidence, callback),
            daemon=True
        ).start()

    def _send_async(self, violation_type: str, image_path: Optional[str],
                    source_name: str, confidence: float, callback):
        emoji = VIOLATION_EMOJI.get(violation_type, '⚠️')
        label = VIOLATION_LABELS_VI.get(violation_type, violation_type)
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        is_fall = violation_type == 'Fall-Detected'

        msg = (
            f"{'🚨🚨🚨 KHẨN CẤP!' if is_fall else '⚠️ CẢNH BÁO VI PHẠM PPE'}\n\n"
            f"{emoji} *Vi phạm:* {label}\n"
            f"📹 *Nguồn:* {source_name}\n"
            f"🎯 *Độ tin cậy:* {confidence:.0%}\n"
            f"🕐 *Thời gian:* {now}\n"
        )
        if is_fall:
            msg += "\n⚠️ *Cần xử lý NGAY LẬP TỨC!*"

        success = False
        try:
            if image_path and os.path.exists(image_path):
                url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
                with open(image_path, 'rb') as img:
                    resp = requests.post(url, data={
                        'chat_id': self.chat_id,
                        'caption': msg,
                        'parse_mode': 'Markdown'
                    }, files={'photo': img}, timeout=15)
                success = resp.status_code == 200
            else:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                resp = requests.post(url, json={
                    'chat_id': self.chat_id,
                    'text': msg,
                    'parse_mode': 'Markdown'
                }, timeout=10)
                success = resp.status_code == 200

            if success:
                self._mark_sent(violation_type)
        except Exception as e:
            print(f"[Telegram] Lỗi gửi: {e}")

        if callback:
            callback(success)

    def test_connection(self) -> tuple[bool, str]:
        """Kiểm tra kết nối bot"""
        if not self.bot_token:
            return False, "Chưa nhập Bot Token"
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get('ok'):
                name = data['result'].get('first_name', 'Bot')
                return True, f"Kết nối thành công! Bot: {name}"
            return False, "Token không hợp lệ"
        except Exception as e:
            return False, f"Lỗi kết nối: {str(e)}"

    def send_test_message(self) -> tuple[bool, str]:
        if not self.enabled:
            return False, "Chưa cấu hình bot token hoặc chat ID"
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            msg = (
                "✅ *PPE Guardian - Test Connection*\n\n"
                "Hệ thống giám sát PPE đang hoạt động!\n"
                f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )
            resp = requests.post(url, json={
                'chat_id': self.chat_id,
                'text': msg,
                'parse_mode': 'Markdown'
            }, timeout=10)
            if resp.status_code == 200:
                return True, "Đã gửi tin nhắn test thành công!"
            return False, f"Lỗi: {resp.text}"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
