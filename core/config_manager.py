"""
Config Manager - Quản lý cấu hình app (lưu local + DB)
"""
import json
import os
from typing import Dict, Any


DEFAULT_CONFIG = {
    "db_path": "ppe_guardian.db",
    "telegram_bot_token": "8970431050:AAEZCOOT5fxv1APDesuv5JWZqBlS62yOoZ8",
    "telegram_chat_id": "6101947078",
    "alert_cooldown_seconds": "30",
    "confidence_threshold": "0.5",
    "violation_classes": "NO-Gloves,NO-Goggles,NO-Hardhat,NO-Mask,NO-Safety Vest,Fall-Detected",
    "capture_violations": "1",
    "send_telegram": "1",
    "model_path": "best.pt",
    "capture_dir": "captured_violations",
}

CONFIG_FILE = "app_config.json"


class ConfigManager:
    def __init__(self):
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._load_local()

    def _load_local(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config.update(data)
            except Exception:
                pass

    def save_local(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] Lỗi lưu: {e}")

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value

    def get_all(self) -> Dict:
        return self._config.copy()

    def update(self, data: Dict):
        self._config.update(data)
        self.save_local()

    @property
    def confidence_threshold(self) -> float:
        return float(self.get('confidence_threshold', 0.5))

    @property
    def violation_classes(self) -> set:
        val = self.get('violation_classes', '')
        return set(v.strip() for v in val.split(',') if v.strip())

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.get('send_telegram', '1') == '1' and
                    self.get('telegram_bot_token') and
                    self.get('telegram_chat_id'))

    @property
    def capture_enabled(self) -> bool:
        return self.get('capture_violations', '1') == '1'

    @property
    def model_path(self) -> str:
        return self.get('model_path', 'best.pt')
