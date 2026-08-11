"""
Live Detection Page - Phát hiện PPE theo thời gian thực
Hỗ trợ: Webcam, Camera IP/RTSP, File video, Ảnh tĩnh
"""
import cv2
import numpy as np
import os
import uuid
import time
import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFileDialog, QFrame, QSizePolicy,
    QMessageBox, QGroupBox, QCheckBox, QScrollArea,
    QLineEdit, QSpinBox, QTabWidget, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
from core import PPEDetector, CaptureManager, TelegramAlerter
from core.detector import VIOLATION_LABELS_VI, VIOLATION_CLASSES, CLASS_COLORS


# ─── Camera IP Dialog ────────────────────────────────────────────────────────
class CameraIPDialog(QDialog):
    """Dialog nhập thông tin camera IP / RTSP"""
    def __init__(self, parent=None, last_url=""):
        super().__init__(parent)
        self.setWindowTitle("Kết nối Camera IP / RTSP")
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog { background:#161b27; }
            QLabel  { color:#e2e8f0; }
            QLineEdit, QSpinBox, QComboBox {
                background:#1e2535; border:1px solid #2d3748;
                border-radius:6px; padding:7px 10px; color:#e2e8f0;
            }
            QLineEdit:focus { border-color:#f97316; }
            QPushButton {
                background:#1e2535; color:#e2e8f0;
                border:1px solid #2d3748; border-radius:6px; padding:8px 18px;
            }
            QPushButton:hover { background:#2d3748; }
            QPushButton#ok_btn {
                background:#f97316; color:#fff; border:none; font-weight:700;
            }
            QPushButton#ok_btn:hover { background:#ea6c0a; }
        """)
        self._build_ui(last_url)

    def _build_ui(self, last_url):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 16)

        # Tabs: Nhanh / Thủ công
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border:1px solid #1e2535; border-radius:8px;
                               background:#161b27; }
            QTabBar::tab { background:transparent; color:#64748b;
                           padding:8px 18px; border:none; font-size:12px; }
            QTabBar::tab:selected { color:#f97316; border-bottom:2px solid #f97316; }
        """)

        # ── Tab 1: Cài nhanh ──
        quick = QWidget()
        ql = QVBoxLayout(quick)
        ql.setSpacing(10)
        ql.setContentsMargins(12, 12, 12, 12)

        # Preset common URL patterns
        presets = [
            ("RTSP chung",           "rtsp://admin:password@192.168.1.100:554/stream"),
            ("RTSP Hikvision",       "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101"),
            ("RTSP Dahua",           "rtsp://admin:password@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0"),
            ("HTTP MJPEG",           "http://192.168.1.100:8080/video"),
            ("IP Cam Android (DroidCam)", "http://192.168.1.100:4747/video"),
            ("IP Cam iPhone",        "http://192.168.1.100:8080/video"),
            ("Webcam USB index 0",   "0"),
            ("Webcam USB index 1",   "1"),
        ]

        lbl_preset = QLabel("Chọn loại camera:")
        lbl_preset.setStyleSheet("color:#94a3b8; font-size:12px;")
        ql.addWidget(lbl_preset)

        self.cmb_preset = QComboBox()
        for name, _ in presets:
            self.cmb_preset.addItem(name)
        ql.addWidget(self.cmb_preset)

        # Form điền IP / User / Pass
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_ip   = QLineEdit()
        self.inp_ip.setPlaceholderText("192.168.1.100")
        self.inp_port = QSpinBox()
        self.inp_port.setRange(1, 65535)
        self.inp_port.setValue(554)
        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("admin")
        self.inp_pass = QLineEdit()
        self.inp_pass.setPlaceholderText("password")
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_channel = QSpinBox()
        self.inp_channel.setRange(1, 32)
        self.inp_channel.setValue(1)

        form.addRow("IP Camera:", self.inp_ip)
        form.addRow("Port:", self.inp_port)
        form.addRow("Username:", self.inp_user)
        form.addRow("Password:", self.inp_pass)
        form.addRow("Channel:", self.inp_channel)
        ql.addLayout(form)

        btn_build = QPushButton("🔨  Tạo URL từ thông tin trên")
        btn_build.setObjectName("ok_btn")
        btn_build.clicked.connect(self._build_url_from_form)
        ql.addWidget(btn_build)
        ql.addStretch()
        tabs.addTab(quick, "⚡ Cài nhanh")

        # ── Tab 2: Nhập thủ công ──
        manual = QWidget()
        ml = QVBoxLayout(manual)
        ml.setSpacing(10)
        ml.setContentsMargins(12, 12, 12, 12)

        lbl_url = QLabel("URL đầy đủ (RTSP / HTTP / rtmp):")
        lbl_url.setStyleSheet("color:#94a3b8; font-size:12px;")
        ml.addWidget(lbl_url)

        self.inp_url = QLineEdit(last_url)
        self.inp_url.setPlaceholderText(
            "rtsp://user:pass@192.168.x.x:554/stream  hoặc  0  (webcam)")
        ml.addWidget(self.inp_url)

        # Tips box
        tips = QLabel(
            "💡 Ví dụ:\n"
            "• Webcam USB:        0  hoặc  1\n"
            "• RTSP Hikvision:    rtsp://admin:pass@192.168.1.x:554/Streaming/Channels/101\n"
            "• RTSP Dahua:        rtsp://admin:pass@192.168.1.x:554/cam/realmonitor?channel=1\n"
            "• HTTP MJPEG:        http://192.168.1.x:8080/video\n"
            "• DroidCam (Android):http://192.168.1.x:4747/video"
        )
        tips.setStyleSheet(
            "background:#1e3a5f; color:#93c5fd; border-radius:8px;"
            "padding:10px; font-size:11px; line-height:1.6;")
        tips.setWordWrap(True)
        ml.addWidget(tips)
        ml.addStretch()
        tabs.addTab(manual, "✏️ Nhập thủ công")

        layout.addWidget(tabs)
        self._tabs = tabs

        # Kết quả URL
        result_frame = QFrame()
        result_frame.setStyleSheet(
            "background:#0f1117; border:1px solid #1e2535; border-radius:8px;")
        rl = QHBoxLayout(result_frame)
        lbl_r = QLabel("URL:")
        lbl_r.setStyleSheet("color:#64748b; font-size:12px; min-width:30px;")
        self.lbl_result_url = QLabel("(chưa có)")
        self.lbl_result_url.setStyleSheet("color:#f97316; font-size:12px;")
        self.lbl_result_url.setWordWrap(True)
        rl.addWidget(lbl_r)
        rl.addWidget(self.lbl_result_url, 1)
        layout.addWidget(result_frame)

        # Buttons
        btn_box = QDialogButtonBox()
        self.btn_test = btn_box.addButton("🔌  Test kết nối", QDialogButtonBox.ButtonRole.ActionRole)
        self.btn_ok   = btn_box.addButton("✅  Kết nối",      QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_cancel = btn_box.addButton("Hủy",            QDialogButtonBox.ButtonRole.RejectRole)
        self.btn_ok.setObjectName("ok_btn")
        self.btn_test.clicked.connect(self._test_connection)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # Preset change → update port hint
        self.cmb_preset.currentIndexChanged.connect(
            lambda i: self._update_port_hint(presets[i][1]))

    def _update_port_hint(self, url_template):
        if url_template.startswith("rtsp"):
            self.inp_port.setValue(554)
        elif url_template.startswith("http"):
            self.inp_port.setValue(8080)

    def _build_url_from_form(self):
        idx = self.cmb_preset.currentIndex()
        ip   = self.inp_ip.text().strip() or "192.168.1.100"
        port = self.inp_port.value()
        user = self.inp_user.text().strip() or "admin"
        pwd  = self.inp_pass.text().strip() or "password"
        ch   = self.inp_channel.value()

        templates = [
            f"rtsp://{user}:{pwd}@{ip}:{port}/stream",
            f"rtsp://{user}:{pwd}@{ip}:{port}/Streaming/Channels/{ch}01",
            f"rtsp://{user}:{pwd}@{ip}:{port}/cam/realmonitor?channel={ch}&subtype=0",
            f"http://{ip}:{port}/video",
            f"http://{ip}:4747/video",
            f"http://{ip}:8080/video",
            "0", "1",
        ]
        url = templates[min(idx, len(templates)-1)]
        self.inp_url.setText(url)
        self.lbl_result_url.setText(url)
        self._tabs.setCurrentIndex(1)   # chuyển sang tab thủ công

    def _test_connection(self):
        url = self.get_url()
        if not url:
            QMessageBox.warning(self, "Thiếu URL", "Vui lòng nhập URL!")
            return
        self.lbl_result_url.setText(f"⏳ Đang kiểm tra: {url}")
        QApplication_processEvents()
        src = int(url) if url.isdigit() else url
        cap = cv2.VideoCapture(src)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                self.lbl_result_url.setText(f"✅ Kết nối thành công!\n{url}")
                self.lbl_result_url.setStyleSheet("color:#16a34a; font-size:12px;")
                return
        self.lbl_result_url.setText(f"❌ Không kết nối được!\nKiểm tra IP/user/pass\n{url}")
        self.lbl_result_url.setStyleSheet("color:#dc2626; font-size:12px;")

    def get_url(self) -> str:
        """Lấy URL cuối cùng"""
        # Ưu tiên tab thủ công nếu có nội dung
        manual = self.inp_url.text().strip()
        return manual if manual else ""


def QApplication_processEvents():
    from PyQt6.QtWidgets import QApplication
    QApplication.processEvents()


# ─── Video Worker ─────────────────────────────────────────────────────────────
class VideoWorker(QThread):
    display_ready = pyqtSignal(np.ndarray)
    frame_ready = pyqtSignal(np.ndarray, object)
    finished    = pyqtSignal()
    error       = pyqtSignal(str)
    status_msg  = pyqtSignal(str)

    def __init__(self, source, detector, violation_classes,
                 reconnect=False, detect_fps=5, display_fps=24):
        super().__init__()
        self.source           = source
        self.detector         = detector
        self.violation_classes = violation_classes
        self.reconnect        = reconnect   # tự kết nối lại nếu mất tín hiệu
        self.detect_fps       = max(1, detect_fps)
        self.display_fps      = max(self.detect_fps, display_fps)
        self._running         = False
        self._detecting       = False
        self._detect_lock     = threading.Lock()

    def run(self):
        self._running = True
        fail_count = 0
        max_fails  = 50   # ~5 giây liên tiếp không có frame
        detect_interval = 1.0 / self.detect_fps
        display_interval = 1.0 / self.display_fps

        while self._running:
            cap = cv2.VideoCapture(self.source)
            if not cap.isOpened():
                self.error.emit(f"Không thể mở nguồn:\n{self.source}")
                return

            # Giữ buffer nhỏ để tránh xử lý dồn frame cũ và giảm tải webcam USB.
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if isinstance(self.source, int):
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            self.status_msg.emit(f"✅ Đã kết nối: {self.source}")
            fail_count = 0
            next_detect_time = 0.0
            next_display_time = 0.0

            while self._running:
                ret, frame = cap.read()
                if not ret:
                    fail_count += 1
                    if fail_count > max_fails:
                        cap.release()
                        if self.reconnect and self._running:
                            self.status_msg.emit("⚠️ Mất tín hiệu — đang kết nối lại...")
                            self.msleep(2000)
                            break   # vòng ngoài sẽ reconnect
                        else:
                            self.status_msg.emit("⏹ Nguồn video đã kết thúc")
                            self.finished.emit()
                            return
                    self.msleep(50)
                    continue

                fail_count = 0
                now = time.monotonic()

                if now >= next_display_time:
                    self.display_ready.emit(frame)
                    next_display_time = now + display_interval

                if now >= next_detect_time and self._try_start_detection(frame):
                    next_detect_time = now + detect_interval

                self.msleep(1)

            cap.release()

            if not self.reconnect or not self._running:
                break

        self.finished.emit()

    def _try_start_detection(self, frame):
        with self._detect_lock:
            if self._detecting:
                return False
            self._detecting = True

        detect_frame = frame.copy()
        threading.Thread(
            target=self._detect_async,
            args=(detect_frame,),
            daemon=True
        ).start()
        return True

    def _detect_async(self, frame):
        try:
            if not self._running:
                return
            result = self.detector.detect(frame, self.violation_classes)
            if self._running:
                self.frame_ready.emit(result.annotated_frame, result)
        finally:
            with self._detect_lock:
                self._detecting = False

    def stop(self):
        self._running = False


# ─── Live Detection Page ──────────────────────────────────────────────────────
class LiveDetectionPage(QWidget):
    violation_detected = pyqtSignal(object, str)

    def __init__(self, detector, capture_mgr, alerter, db, config):
        super().__init__()
        self.detector    = detector
        self.capture_mgr = capture_mgr
        self.alerter     = alerter
        self.db          = db
        self.config      = config
        self.worker      = None
        self.session_id  = str(uuid.uuid4())[:8]
        self.current_source      = None
        self.current_source_type = 'webcam'
        self.current_source_name = 'Webcam'
        self._frame_count = 0
        self._last_ip_url = ""
        self._last_saved_violation = {}
        self._violation_save_cooldown = 5.0
        self._last_detection_objects = []
        self._last_detection_at = 0.0
        self._overlay_ttl = 1.0
        self._setup_ui()
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(1000)

    # ─── UI ──────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # ── Left: video feed ──
        left = QFrame()
        left.setObjectName("card")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 10, 10)

        hdr = QHBoxLayout()
        self.lbl_src = QLabel("📷 Chưa khởi động")
        self.lbl_src.setStyleSheet("color:#64748b; font-size:12px;")
        hdr.addWidget(self.lbl_src)
        hdr.addStretch()
        self.lbl_fps = QLabel("–– FPS")
        self.lbl_fps.setStyleSheet("color:#f97316; font-weight:700;")
        hdr.addWidget(self.lbl_fps)
        ll.addLayout(hdr)

        self.video_lbl = QLabel("▶  Chọn nguồn và nhấn START")
        self.video_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_lbl.setMinimumSize(640, 460)
        self.video_lbl.setStyleSheet(
            "background:#000; border-radius:8px; color:#4a5568; font-size:16px;")
        ll.addWidget(self.video_lbl, 1)

        self.status_lbl = QLabel("Sẵn sàng")
        self.status_lbl.setStyleSheet(
            "background:#0f1117; color:#64748b; padding:5px 10px;"
            "border-radius:6px; font-size:12px;")
        ll.addWidget(self.status_lbl)
        root.addWidget(left, 1)

        # ── Right: controls ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(278)
        scroll.setStyleSheet("border:none; background:transparent;")
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 4, 4, 8)
        rl.setSpacing(10)

        # ── Nguồn video ──
        g_src = self._group("NGUỒN VIDEO")
        gl_src = QVBoxLayout()

        # 4 nút nguồn
        self.btn_webcam   = QPushButton("📷  Webcam mặc định")
        self.btn_webcam.setObjectName("btn_primary")
        self.btn_webcam.clicked.connect(lambda: self._select('webcam'))

        self.btn_ip       = QPushButton("🌐  Camera IP / RTSP")
        self.btn_ip.setStyleSheet(
            "background:#1e3a5f; color:#93c5fd; border:1px solid #2d5a8f;"
            "border-radius:8px; padding:8px 14px; font-weight:600;")
        self.btn_ip.setToolTip("Kết nối camera mạng, IP Cam, RTSP stream")
        self.btn_ip.clicked.connect(self._open_ip_dialog)

        self.btn_video    = QPushButton("🎬  File video")
        self.btn_video.clicked.connect(lambda: self._select('video'))

        self.btn_image    = QPushButton("🖼️  Ảnh tĩnh")
        self.btn_image.clicked.connect(lambda: self._select('image'))

        # Label hiển thị nguồn đang chọn
        self.lbl_sel = QLabel("Chưa chọn nguồn")
        self.lbl_sel.setStyleSheet(
            "color:#64748b; font-size:11px; background:#0f1117;"
            "border-radius:6px; padding:4px 8px;")
        self.lbl_sel.setWordWrap(True)

        gl_src.addWidget(self.btn_webcam)
        gl_src.addWidget(self.btn_ip)
        gl_src.addWidget(self.btn_video)
        gl_src.addWidget(self.btn_image)
        gl_src.addWidget(self.lbl_sel)
        g_src.setLayout(gl_src)
        rl.addWidget(g_src)

        # ── IP Camera nhanh ──
        g_quick = self._group("KẾT NỐI NHANH CAMERA IP")
        gl_quick = QVBoxLayout()
        lbl_q = QLabel("URL trực tiếp:")
        lbl_q.setStyleSheet("color:#64748b; font-size:11px;")
        gl_quick.addWidget(lbl_q)

        url_row = QHBoxLayout()
        self.inp_quick_url = QLineEdit()
        self.inp_quick_url.setPlaceholderText("rtsp://user:pass@192.168.x.x:554/...")
        self.inp_quick_url.setStyleSheet(
            "background:#1e2535; border:1px solid #2d3748; border-radius:6px;"
            "padding:6px 8px; color:#e2e8f0; font-size:11px;")
        btn_quick = QPushButton("▶")
        btn_quick.setFixedWidth(36)
        btn_quick.setObjectName("btn_success")
        btn_quick.setToolTip("Kết nối ngay với URL này")
        btn_quick.clicked.connect(self._quick_connect)
        url_row.addWidget(self.inp_quick_url)
        url_row.addWidget(btn_quick)
        gl_quick.addLayout(url_row)

        # Webcam index chọn nhanh
        idx_row = QHBoxLayout()
        lbl_idx = QLabel("Webcam index:")
        lbl_idx.setStyleSheet("color:#64748b; font-size:11px;")
        self.spin_cam_idx = QSpinBox()
        self.spin_cam_idx.setRange(0, 10)
        self.spin_cam_idx.setValue(0)
        self.spin_cam_idx.setFixedWidth(60)
        btn_idx = QPushButton("Chọn")
        btn_idx.setFixedWidth(55)
        btn_idx.clicked.connect(
            lambda: self._set_source_webcam(self.spin_cam_idx.value()))
        idx_row.addWidget(lbl_idx)
        idx_row.addStretch()
        idx_row.addWidget(self.spin_cam_idx)
        idx_row.addWidget(btn_idx)
        gl_quick.addLayout(idx_row)
        g_quick.setLayout(gl_quick)
        rl.addWidget(g_quick)

        # ── Start / Stop ──
        g_ctrl = self._group("ĐIỀU KHIỂN")
        gl_ctrl = QVBoxLayout()
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("▶  Start")
        self.btn_start.setObjectName("btn_success")
        self.btn_start.clicked.connect(self._start)
        self.btn_stop  = QPushButton("⏹  Stop")
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        gl_ctrl.addLayout(btn_row)

        self.cb_reconnect = QCheckBox("🔄 Tự kết nối lại khi mất tín hiệu")
        self.cb_reconnect.setChecked(True)
        gl_ctrl.addWidget(self.cb_reconnect)
        g_ctrl.setLayout(gl_ctrl)
        rl.addWidget(g_ctrl)

        # ── Confidence ──
        g_conf = self._group("ĐỘ TIN CẬY TỐI THIỂU")
        gl_conf = QHBoxLayout()
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(10, 95)
        self.conf_slider.setValue(
            int(float(self.config.get('confidence_threshold', 0.5)) * 100))
        self.conf_val = QLabel(f"{self.conf_slider.value()}%")
        self.conf_val.setStyleSheet("color:#f97316; font-weight:700; min-width:36px;")
        self.conf_slider.valueChanged.connect(
            lambda v: (self.conf_val.setText(f"{v}%"),
                       self.detector.set_confidence(v/100)))
        gl_conf.addWidget(self.conf_slider)
        gl_conf.addWidget(self.conf_val)
        g_conf.setLayout(gl_conf)
        rl.addWidget(g_conf)

        # ── Violation classes ──
        g_vio = self._group("LOẠI VI PHẠM CẦN PHÁT HIỆN")
        gl_vio = QVBoxLayout()
        enabled = self.config.violation_classes
        self.vio_checks = {}
        for cls in sorted(VIOLATION_CLASSES):
            cb = QCheckBox(VIOLATION_LABELS_VI.get(cls, cls))
            cb.setChecked(cls in enabled)
            self.vio_checks[cls] = cb
            gl_vio.addWidget(cb)
        g_vio.setLayout(gl_vio)
        rl.addWidget(g_vio)

        # ── Cảnh báo ──
        g_alert = self._group("CẢNH BÁO")
        gl_alert = QVBoxLayout()
        self.cb_capture  = QCheckBox("💾 Lưu ảnh vi phạm")
        self.cb_capture.setChecked(self.config.capture_enabled)
        self.cb_telegram = QCheckBox("📱 Gửi Telegram")
        self.cb_telegram.setChecked(self.config.telegram_enabled)
        gl_alert.addWidget(self.cb_capture)
        gl_alert.addWidget(self.cb_telegram)
        g_alert.setLayout(gl_alert)
        rl.addWidget(g_alert)

        # ── Thông tin live ──
        g_info = self._group("THÔNG TIN PHÁT HIỆN")
        gl_info = QVBoxLayout()
        self.lbl_persons  = QLabel("👤 Người: 0")
        self.lbl_viocount = QLabel("⚠️ Vi phạm: 0")
        self.lbl_viocount.setStyleSheet("color:#16a34a; font-weight:700;")
        self.lbl_conf_cur = QLabel("🎯 Độ tin cậy TB: –")
        gl_info.addWidget(self.lbl_persons)
        gl_info.addWidget(self.lbl_viocount)
        gl_info.addWidget(self.lbl_conf_cur)
        g_info.setLayout(gl_info)
        rl.addWidget(g_info)

        rl.addStretch()
        scroll.setWidget(right)
        root.addWidget(scroll)

    def _group(self, title):
        g = QGroupBox(title)
        g.setStyleSheet("""
            QGroupBox {
                background:#161b27; border:1px solid #1e2535;
                border-radius:8px; margin-top:8px; padding:8px 6px 6px 6px;
                font-size:10px; font-weight:700; color:#64748b; letter-spacing:1px;
            }
            QGroupBox::title { subcontrol-origin:margin; left:8px; padding:0 4px; }
        """)
        return g

    # ─── Source selection ─────────────────────────────────────────────────────
    def _select(self, stype):
        if stype == 'webcam':
            self._set_source_webcam(0)
        elif stype == 'video':
            path, _ = QFileDialog.getOpenFileName(
                self, "Chọn file video", "",
                "Video (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.ts)")
            if path:
                self.current_source      = path
                self.current_source_type = 'video'
                self.current_source_name = os.path.basename(path)
                self.lbl_sel.setText(f"🎬 {self.current_source_name}")
                self.status_lbl.setText(f"Đã chọn: {self.current_source_name}")
        elif stype == 'image':
            path, _ = QFileDialog.getOpenFileName(
                self, "Chọn ảnh", "",
                "Ảnh (*.jpg *.jpeg *.png *.bmp *.webp *.tiff)")
            if path:
                self._detect_image(path)

    def _set_source_webcam(self, index: int):
        self.current_source      = index
        self.current_source_type = 'webcam'
        self.current_source_name = f'Webcam #{index}'
        self.lbl_sel.setText(f"📷 Webcam index {index}")
        self.status_lbl.setText(f"Đã chọn: Webcam #{index}")

    def _open_ip_dialog(self):
        dlg = CameraIPDialog(self, self._last_ip_url)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            url = dlg.get_url().strip()
            if url:
                self._connect_ip(url)

    def _quick_connect(self):
        url = self.inp_quick_url.text().strip()
        if not url:
            QMessageBox.warning(self, "Thiếu URL", "Vui lòng nhập URL camera!")
            return
        self._connect_ip(url)

    def _connect_ip(self, url: str):
        self._last_ip_url = url
        self.inp_quick_url.setText(url)
        # Xử lý nếu là số (webcam index)
        if url.isdigit():
            self._set_source_webcam(int(url))
            return
        self.current_source      = url
        self.current_source_type = 'ip_camera'
        # Tên hiển thị: lấy IP từ URL
        try:
            import re
            ip_match = re.search(r'@([\d.]+)', url)
            ip = ip_match.group(1) if ip_match else url[:30]
            self.current_source_name = f'IP Cam {ip}'
        except Exception:
            self.current_source_name = 'IP Camera'
        self.lbl_sel.setText(f"🌐 {self.current_source_name}\n{url[:50]}...")
        self.status_lbl.setText(f"Đã chọn IP Camera: {self.current_source_name}")

    # ─── Detection ────────────────────────────────────────────────────────────
    def _detect_image(self, path):
        frame = cv2.imread(path)
        if frame is None:
            QMessageBox.warning(self, "Lỗi", "Không đọc được ảnh!")
            return
        vclasses = {c for c, cb in self.vio_checks.items() if cb.isChecked()}
        result = self.detector.detect(frame, vclasses)
        self._show_frame(result.annotated_frame)
        self._update_info(result)
        if result.has_violation:
            self._save_and_alert(result, path, 'image', os.path.basename(path))
        self.status_lbl.setText(
            f"✅ Xong | {len(result.objects)} đối tượng | "
            f"{len(result.violations)} vi phạm | {os.path.basename(path)}")

    def _start(self):
        if not self.detector.loaded:
            QMessageBox.warning(self, "Lỗi", "Model chưa được tải!\nVào Settings để kiểm tra.")
            return
        if self.current_source is None:
            self._set_source_webcam(0)

        vclasses = {c for c, cb in self.vio_checks.items() if cb.isChecked()}
        self.session_id = str(uuid.uuid4())[:8]
        self._last_detection_objects = []
        self._last_detection_at = 0.0
        reconnect = self.cb_reconnect.isChecked()

        self.worker = VideoWorker(
            self.current_source, self.detector, vclasses, reconnect,
            detect_fps=8, display_fps=24)
        self.worker.display_ready.connect(self._on_display_frame)
        self.worker.frame_ready.connect(self._on_frame)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.status_msg.connect(self.status_lbl.setText)
        self.worker.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_src.setText(f"📡 Đang chạy: {self.current_source_name}")
        self.status_lbl.setText(f"⏳ Đang kết nối {self.current_source_name}...")

    def _on_display_frame(self, frame):
        self._show_frame(self._draw_cached_detections(frame))
        self._frame_count += 1

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_src.setText("⏹ Đã dừng")
        self.status_lbl.setText("Đã dừng")
        self._last_detection_objects = []
        self._last_detection_at = 0.0

    def _on_frame(self, frame, result):
        self._last_detection_objects = list(result.objects)
        self._last_detection_at = time.monotonic()
        self._update_info(result)
        if result.has_violation:
            selected = self._violations_due_for_save(result.violations)
            if selected:
                self._save_and_alert(result, None,
                                     self.current_source_type,
                                     self.current_source_name,
                                     selected)

    def _draw_cached_detections(self, frame):
        if not self._last_detection_objects:
            return frame
        if time.monotonic() - self._last_detection_at > self._overlay_ttl:
            return frame

        annotated = frame.copy()
        for obj in self._last_detection_objects:
            class_name = obj.get('class_name', '')
            conf = obj.get('confidence', 0.0)
            x1 = int(obj.get('bbox_x1', 0))
            y1 = int(obj.get('bbox_y1', 0))
            x2 = int(obj.get('bbox_x2', 0))
            y2 = int(obj.get('bbox_y2', 0))
            is_vio = bool(obj.get('is_violation', False))

            color = CLASS_COLORS.get(class_name, (128, 128, 128))
            thickness = 3 if is_vio else 2
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

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

        return annotated

    def _show_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, w*ch, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self.video_lbl.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation)
        self.video_lbl.setPixmap(pix)

    def _update_info(self, result):
        self.lbl_persons.setText(f"👤 Người: {result.total_persons}")
        n = len(result.violations)
        self.lbl_viocount.setText(f"⚠️ Vi phạm: {n}")
        self.lbl_viocount.setStyleSheet(
            "color:#dc2626; font-weight:700;" if n > 0
            else "color:#16a34a; font-weight:700;")
        if result.confidence_avg > 0:
            self.lbl_conf_cur.setText(f"🎯 Độ tin cậy TB: {result.confidence_avg:.0%}")

    def _violations_due_for_save(self, violations):
        now = time.monotonic()
        selected = []
        for vobj in violations:
            vtype = vobj['class_name']
            last = self._last_saved_violation.get(vtype, 0.0)
            if now - last >= self._violation_save_cooldown:
                self._last_saved_violation[vtype] = now
                selected.append(vobj)
        return selected

    def _save_and_alert(self, result, existing_img, src_type, src_name,
                        selected_violations=None):
        if not self.db:
            return
        violations = selected_violations if selected_violations is not None else result.violations
        if not violations:
            return
        det_id = self.db.save_detection(
            self.session_id, src_type, src_name,
            result.total_persons, True,
            existing_img or '', 0, result.confidence_avg)
        if det_id:
            self.db.save_detection_objects(det_id, result.objects)

        for vobj in violations:
            img_path = existing_img
            if self.cb_capture.isChecked() and result.annotated_frame is not None:
                img_path = self.capture_mgr.save_violation_image(
                    result.annotated_frame, vobj['class_name'], src_name)
            vid = None
            if det_id:
                vid = self.db.save_violation(
                    det_id, vobj['class_name'], img_path or '',
                    src_type, src_name, vobj['confidence'])
            if self.cb_telegram.isChecked() and self.alerter.enabled:
                def _cb(ok, _vid=vid):
                    if ok and _vid and self.db:
                        self.db.update_telegram_sent(_vid)
                self.alerter.send_violation_alert(
                    vobj['class_name'], img_path, src_name,
                    vobj['confidence'], callback=_cb)
            self.violation_detected.emit(result, vobj['class_name'])

    def _update_fps(self):
        self.lbl_fps.setText(f"{self._frame_count} FPS")
        self._frame_count = 0

    def _on_error(self, msg):
        self.status_lbl.setText(f"❌ {msg}")
        self._on_finished()

    def _on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def cleanup(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)
