"""
Capture Manager - Quản lý lưu ảnh vi phạm
"""
import cv2
import numpy as np
import os
from datetime import datetime
from typing import Optional


class CaptureManager:
    def __init__(self, save_dir: str = 'captured_violations'):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def save_violation_image(self, frame: np.ndarray,
                              violation_type: str,
                              source_name: str = '') -> Optional[str]:
        """Lưu ảnh vi phạm, trả về đường dẫn file"""
        try:
            now = datetime.now()
            safe_vtype = violation_type.replace(' ', '_').replace('/', '_')
            safe_source = os.path.splitext(os.path.basename(source_name))[0] \
                            if source_name else 'cam'
            safe_source = safe_source.replace(' ', '_')[:20]
            filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{safe_vtype}_{safe_source}.jpg"

            # Tạo thư mục theo ngày
            day_dir = os.path.join(self.save_dir, now.strftime('%Y%m%d'))
            os.makedirs(day_dir, exist_ok=True)
            filepath = os.path.join(day_dir, filename)

            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return filepath
        except Exception as e:
            print(f"[Capture] Lỗi lưu ảnh: {e}")
            return None

    def set_save_dir(self, path: str):
        self.save_dir = path
        os.makedirs(path, exist_ok=True)
