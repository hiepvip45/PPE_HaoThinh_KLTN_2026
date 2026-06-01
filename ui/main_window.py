"""
Main Window - Cửa sổ chính PPE Guardian
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush

from core import DatabaseManager, PPEDetector, CaptureManager, TelegramAlerter, ConfigManager
from ui.styles import APP_STYLE
from ui.pages import (
    DashboardPage, LiveDetectionPage, ViolationsPage,
    StatisticsPage, SettingsPage
)


class ModelLoader(QThread):
    done = pyqtSignal(bool, str)
    def __init__(self, detector):
        super().__init__()
        self.detector = detector
    def run(self):
        ok, msg = self.detector.load_model()
        self.done.emit(ok, msg)


class PPEGuardianWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPE Guardian  |  Hệ Thống Giám Sát Bảo Hộ Lao Động")
        self.setMinimumSize(1280, 780)
        self.resize(1440, 860)

        self.config = ConfigManager()
        self.db = DatabaseManager(
            host=self.config.get('db_host', 'localhost'),
            port=int(self.config.get('db_port', 3306)),
            database=self.config.get('db_name', 'ppe_guardian'),
            user=self.config.get('db_user', 'root'),
            password=self.config.get('db_password', ''),
        )
        self.detector = PPEDetector(
            model_path=self.config.model_path,
            confidence=self.config.confidence_threshold
        )
        self.capture_mgr = CaptureManager(
            self.config.get('capture_dir', 'captured_violations'))
        self.alerter = TelegramAlerter(
            bot_token=self.config.get('telegram_bot_token', ''),
            chat_id=self.config.get('telegram_chat_id', ''),
            cooldown_seconds=int(self.config.get('alert_cooldown_seconds', 30))
        )

        self._db_connected = False
        self._setup_ui()
        self._connect_db()
        self._load_model()

    def _connect_db(self):
        self._db_connected = self.db.connect()
        # Gán db cho các page sau khi connect
        if self._db_connected:
            self.dashboard.db = self.db
            self.live_page.db = self.db
            self.vio_page.db = self.db
            self.stats_page.db = self.db
            self._set_status("✅ Kết nối database thành công")
        else:
            self._set_status("❌ Không kết nối được DB — chạy ở chế độ không lưu lịch sử")

    def _load_model(self):
        self._set_status("⏳ Đang tải model YOLOv8, vui lòng chờ...")
        self.model_loader = ModelLoader(self.detector)
        self.model_loader.done.connect(self._on_model_loaded)
        self.model_loader.start()

    def _on_model_loaded(self, ok: bool, msg: str):
        self._set_status(("✅ " if ok else "❌ ") + msg)
        self.dashboard.update_system_status(
            self._db_connected,
            bool(self.config.get('telegram_bot_token')),
            ok
        )
        if ok:
            self.lbl_model_info.setText(f"YOLOv8 · 14 classes\n{self.config.model_path}")
            self.lbl_model_info.setStyleSheet("color:#16a34a; font-size:10px; padding:4px;")
        else:
            self.lbl_model_info.setText("⚠️ Model chưa tải được")
            self.lbl_model_info.setStyleSheet("color:#dc2626; font-size:10px; padding:4px;")
            QMessageBox.warning(
                self, "Không tải được model",
                f"{msg}\n\n"
                "➤ Hãy đặt file best.pt vào cùng thư mục với main.py\n"
                "➤ Hoặc vào Settings → Model & Lưu ảnh để chọn đường dẫn khác."
            )

    def _setup_ui(self):
        self.setStyleSheet(APP_STYLE)
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        content_wrap = QWidget()
        content_wrap.setObjectName("content_area")
        cw_layout = QVBoxLayout(content_wrap)
        cw_layout.setContentsMargins(16, 16, 16, 8)
        cw_layout.setSpacing(10)

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("page_title")
        cw_layout.addWidget(self.page_title)

        self.stack = QStackedWidget()

        # Pages khởi tạo với db=None, sẽ được gán sau khi connect
        self.dashboard     = DashboardPage(None, self.config)
        self.live_page     = LiveDetectionPage(
            self.detector, self.capture_mgr, self.alerter, None, self.config)
        self.vio_page      = ViolationsPage(None, self.config)
        self.stats_page    = StatisticsPage(None, self.config)
        self.settings_page = SettingsPage(self.db, self.alerter, self.config)

        for page in [self.dashboard, self.live_page, self.vio_page,
                     self.stats_page, self.settings_page]:
            self.stack.addWidget(page)

        cw_layout.addWidget(self.stack, 1)

        self.status_lbl = QLabel("Đang khởi động...")
        self.status_lbl.setObjectName("status_bar")
        cw_layout.addWidget(self.status_lbl)

        root.addWidget(content_wrap, 1)

        self.live_page.violation_detected.connect(self._on_violation)
        QTimer.singleShot(800, self.dashboard.refresh)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        logo = QLabel("⛑  PPE Guardian")
        logo.setObjectName("logo_label")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("SAFETY MONITORING")
        sub.setObjectName("sub_logo")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        layout.addWidget(sub)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background:#1e2535; max-height:1px; margin:10px 0;")
        layout.addWidget(div)
        layout.addSpacing(6)

        nav_items = [
            ("🏠", "Dashboard",       0, "Dashboard"),
            ("📹", "Live Detection",  1, "Phát Hiện Trực Tiếp"),
            ("⚠️", "Vi Phạm",        2, "Lịch Sử Vi Phạm"),
            ("📊", "Thống Kê",       3, "Thống Kê & Báo Cáo"),
            ("⚙️", "Cài Đặt",       4, "Cài Đặt Hệ Thống"),
        ]

        self._nav_btns = []
        for icon, label, idx, title in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx, t=title: self._nav(i, t))
            self._nav_btns.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        self.lbl_model_info = QLabel("Model: đang tải...")
        self.lbl_model_info.setStyleSheet("color:#4a5568; font-size:10px; padding:4px;")
        self.lbl_model_info.setWordWrap(True)
        layout.addWidget(self.lbl_model_info)

        self._set_nav_active(0)
        return sidebar

    def _set_nav_active(self, index: int):
        for i, btn in enumerate(self._nav_btns):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _nav(self, index: int, title: str):
        self.stack.setCurrentIndex(index)
        self.page_title.setText(title)
        self._set_nav_active(index)
        if index == 0:
            self.dashboard.refresh()
        elif index == 2:
            self.vio_page.refresh()
        elif index == 3:
            self.stats_page.refresh()

    def _on_violation(self, result, violation_type: str):
        self.dashboard.add_live_violation(
            violation_type,
            self.live_page.current_source_name,
            result.confidence_avg
        )

    def _set_status(self, msg: str):
        self.status_lbl.setText(msg)

    def closeEvent(self, event):
        self.live_page.cleanup()
        self.db.disconnect()
        event.accept()
