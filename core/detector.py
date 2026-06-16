"""
PPE Detector Engine - Xử lý phát hiện PPE bằng YOLOv8
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import os

# Các class vi phạm
VIOLATION_CLASSES = {
    'NO-Gloves', 'NO-Goggles', 'NO-Hardhat',
    'NO-Mask', 'NO-Safety Vest', 'Fall-Detected'
}

# Màu sắc cho từng class (BGR)
CLASS_COLORS = {
    'Fall-Detected':    (0,   0,   255),   # Đỏ đậm
    'Gloves':           (0,   200, 0),     # Xanh lá
    'Goggles':          (0,   200, 100),
    'Hardhat':          (0,   180, 255),   # Vàng cam
    'Ladder':           (200, 200, 0),
    'Mask':             (0,   255, 150),
    'NO-Gloves':        (0,   60,  255),   # Cam đỏ
    'NO-Goggles':       (0,   80,  255),
    'NO-Hardhat':       (0,   0,   220),
    'NO-Mask':          (20,  20,  255),
    'NO-Safety Vest':   (0,   40,  255),
    'Person':           (200, 200, 200),   # Xám
    'Safety Cone':      (0,   165, 255),
    'Safety Vest':      (0,   255, 200),
}

VIOLATION_LABELS_VI = {
    'NO-Gloves':      'Không đeo găng tay',
    'NO-Goggles':     'Không đeo kính bảo hộ',
    'NO-Hardhat':     'Không đội mũ bảo hộ',
    'NO-Mask':        'Không đeo khẩu trang',
    'NO-Safety Vest': 'Không mặc áo phản quang',
    'Fall-Detected':  'Phát hiện ngã/tai nạn',
}


class DetectionResult:
    def __init__(self):
        self.objects: List[Dict] = []
        self.violations: List[Dict] = []
        self.has_violation: bool = False
        self.total_persons: int = 0
        self.frame: Optional[np.ndarray] = None
        self.annotated_frame: Optional[np.ndarray] = None
        self.confidence_avg: float = 0.0


class PPEDetector:
    def __init__(self, model_path: str = 'best.pt', confidence: float = 0.5):
        self.model_path = model_path
        self.confidence = confidence
        self.inference_size = 416
        self.model: Optional[YOLO] = None
        self.class_names: List[str] = []
        self.loaded = False

    def load_model(self) -> Tuple[bool, str]:
        try:
            if not os.path.exists(self.model_path):
                return False, f"Không tìm thấy file model: {self.model_path}"
            self.model = YOLO(self.model_path)
            self.class_names = list(self.model.names.values())
            self.loaded = True
            return True, "Model đã được tải thành công"
        except Exception as e:
            return False, f"Lỗi tải model: {str(e)}"

    def detect(self, frame: np.ndarray,
               violation_classes: Optional[set] = None) -> DetectionResult:
        result = DetectionResult()
        result.frame = frame.copy()

        if not self.loaded or self.model is None:
            result.annotated_frame = frame.copy()
            return result

        vclasses = violation_classes if violation_classes else VIOLATION_CLASSES

        try:
            results = self.model(
                frame,
                conf=self.confidence,
                imgsz=self.inference_size,
                verbose=False
            )
            annotated = frame.copy()
            confidences = []

            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f"class_{cls_id}"
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    is_vio = class_name in vclasses
                    confidences.append(conf)

                    obj = {
                        'class_name': class_name,
                        'confidence': conf,
                        'bbox_x1': x1, 'bbox_y1': y1,
                        'bbox_x2': x2, 'bbox_y2': y2,
                        'is_violation': is_vio
                    }
                    result.objects.append(obj)
                    if is_vio:
                        result.violations.append(obj)

                    if class_name == 'Person':
                        result.total_persons += 1

                    # Vẽ bounding box
                    color = CLASS_COLORS.get(class_name, (128, 128, 128))
                    thickness = 3 if is_vio else 2
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

                    # Label
                    label_vi = VIOLATION_LABELS_VI.get(class_name, class_name)
                    label = f"{label_vi} {conf:.0%}"
                    font_scale = 0.55
                    font_thick = 1
                    (lw, lh), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)

                    ly = max(y1 - 5, lh + 5)
                    cv2.rectangle(annotated, (x1, ly - lh - baseline - 4),
                                  (x1 + lw + 4, ly + 2), color, -1)
                    text_color = (0, 0, 0) if is_vio else (255, 255, 255)
                    cv2.putText(annotated, label, (x1 + 2, ly - 2),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thick)

            result.has_violation = len(result.violations) > 0
            result.confidence_avg = sum(confidences) / len(confidences) if confidences else 0.0
            result.annotated_frame = annotated

        except Exception as e:
            print(f"[Detector] Lỗi detection: {e}")
            result.annotated_frame = frame.copy()

        return result

    def set_confidence(self, conf: float):
        self.confidence = max(0.1, min(1.0, conf))
