"""
Settings Page - Cấu hình hệ thống, database, Telegram
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFormLayout, QGroupBox, QMessageBox, QFileDialog,
    QSpinBox, QDoubleSpinBox, QTabWidget, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsPage(QWidget):
    def __init__(self, db_manager, telegram_alerter, config):
        super().__init__()
        self.db_manager = db_manager
        self.alerter = telegram_alerter
        self.config = config
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(16)
        inner_layout.setContentsMargins(0, 0, 8, 16)

        tabs = QTabWidget()

        # ── Tab 1: Database ──
        db_tab = QWidget()
        db_layout = QVBoxLayout(db_tab)
        db_layout.setSpacing(12)

        db_group = self._make_group("CẤU HÌNH DATABASE SQLITE")
        db_form = QFormLayout()
        db_form.setSpacing(10)
        db_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_db_path = QLineEdit()
        self.inp_db_path.setPlaceholderText("ppe_guardian.db")

        db_form.addRow("Đường dẫn DB:", self.inp_db_path)
        
        db_btn_row = QHBoxLayout()
        btn_browse_db = QPushButton("📂  Chọn file DB")
        btn_browse_db.clicked.connect(self._browse_db_path)
        btn_save_db = QPushButton("💾  Lưu cấu hình DB")
        btn_save_db.setObjectName("btn_primary")
        btn_save_db.clicked.connect(self._save_db)
        db_btn_row.addWidget(btn_browse_db)
        db_btn_row.addWidget(btn_save_db)
        db_btn_row.addStretch()

        self.lbl_db_status = QLabel("ℹ️  Dữ liệu sẽ được lưu vào file SQLite")
        self.lbl_db_status.setStyleSheet("font-size:12px; color:#64748b;")

        db_inner = QVBoxLayout()
        db_inner.addLayout(db_form)
        db_inner.addLayout(db_btn_row)
        db_inner.addWidget(self.lbl_db_status)
        db_group.setLayout(db_inner)
        db_layout.addWidget(db_group)
        db_layout.addStretch()
        tabs.addTab(db_tab, "🗄️  Database")

        # ── Tab 2: Telegram ──
        tg_tab = QWidget()
        tg_layout = QVBoxLayout(tg_tab)
        tg_layout.setSpacing(12)

        tg_group = self._make_group("CẤU HÌNH TELEGRAM")
        tg_inner = QVBoxLayout()
        tg_inner.setSpacing(10)

        # Guide
        guide = QLabel(
            "📖 Cách lấy Bot Token & Chat ID:\n"
            "1. Mở Telegram → Tìm @BotFather\n"
            "2. Gửi /newbot → đặt tên → lấy Token\n"
            "3. Tìm @userinfobot → gửi /start → lấy Chat ID\n"
            "4. Gửi tin nhắn bất kỳ cho bot của bạn trước\n"
            "   (để bot có thể nhắn lại)"
        )
        guide.setStyleSheet(
            "background:#1e3a5f; color:#93c5fd; border-radius:8px;"
            "padding:12px; font-size:12px; line-height:1.6;")
        guide.setWordWrap(True)
        tg_inner.addWidget(guide)

        tg_form = QFormLayout()
        tg_form.setSpacing(10)
        tg_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.inp_token = QLineEdit()
        self.inp_token.setPlaceholderText("123456:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.inp_chatid = QLineEdit()
        self.inp_chatid.setPlaceholderText("-100123456789 hoặc 123456789")
        self.inp_cooldown = QSpinBox()
        self.inp_cooldown.setRange(5, 3600)
        self.inp_cooldown.setSuffix(" giây")
        self.inp_cooldown.setValue(30)
        tg_form.addRow("Bot Token:", self.inp_token)
        tg_form.addRow("Chat ID:", self.inp_chatid)
        tg_form.addRow("Cooldown giữa 2 alert:", self.inp_cooldown)
        tg_inner.addLayout(tg_form)

        tg_btn_row = QHBoxLayout()
        btn_test_tg = QPushButton("📨  Gửi tin nhắn test")
        btn_test_tg.clicked.connect(self._test_telegram)
        btn_save_tg = QPushButton("💾  Lưu cấu hình")
        btn_save_tg.setObjectName("btn_primary")
        btn_save_tg.clicked.connect(self._save_telegram)
        tg_btn_row.addWidget(btn_test_tg)
        tg_btn_row.addWidget(btn_save_tg)
        tg_btn_row.addStretch()
        tg_inner.addLayout(tg_btn_row)

        self.lbl_tg_status = QLabel("")
        self.lbl_tg_status.setStyleSheet("font-size:12px;")
        tg_inner.addWidget(self.lbl_tg_status)

        tg_group.setLayout(tg_inner)
        tg_layout.addWidget(tg_group)
        tg_layout.addStretch()
        tabs.addTab(tg_tab, "📱  Telegram")

        # ── Tab 3: Model & Capture ──
        model_tab = QWidget()
        model_layout = QVBoxLayout(model_tab)
        model_layout.setSpacing(12)

        model_group = self._make_group("CẤU HÌNH MODEL")
        model_inner = QFormLayout()
        model_inner.setSpacing(10)
        model_inner.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        model_row = QHBoxLayout()
        self.inp_model = QLineEdit()
        self.inp_model.setPlaceholderText("best.pt")
        btn_browse_model = QPushButton("📂")
        btn_browse_model.setFixedWidth(40)
        btn_browse_model.clicked.connect(self._browse_model)
        model_row.addWidget(self.inp_model)
        model_row.addWidget(btn_browse_model)

        self.inp_conf = QDoubleSpinBox()
        self.inp_conf.setRange(0.1, 0.95)
        self.inp_conf.setSingleStep(0.05)
        self.inp_conf.setDecimals(2)
        self.inp_conf.setValue(0.5)

        capture_row = QHBoxLayout()
        self.inp_capture_dir = QLineEdit()
        self.inp_capture_dir.setPlaceholderText("captured_violations")
        btn_browse_dir = QPushButton("📂")
        btn_browse_dir.setFixedWidth(40)
        btn_browse_dir.clicked.connect(self._browse_capture_dir)
        capture_row.addWidget(self.inp_capture_dir)
        capture_row.addWidget(btn_browse_dir)

        model_inner.addRow("File model (.pt):", model_row)
        model_inner.addRow("Ngưỡng tin cậy:", self.inp_conf)
        model_inner.addRow("Thư mục lưu ảnh:", capture_row)

        btn_save_model = QPushButton("💾  Lưu cấu hình model")
        btn_save_model.setObjectName("btn_primary")
        btn_save_model.clicked.connect(self._save_model_config)

        model_inner_widget = QVBoxLayout()
        model_inner_widget.addLayout(model_inner)
        model_inner_widget.addWidget(btn_save_model)
        model_group.setLayout(model_inner_widget)
        model_layout.addWidget(model_group)
        model_layout.addStretch()
        tabs.addTab(model_tab, "🤖  Model & Lưu ảnh")

        inner_layout.addWidget(tabs)
        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _make_group(self, title: str) -> QGroupBox:
        g = QGroupBox(title)
        g.setStyleSheet("""
            QGroupBox {
                background:#161b27; border:1px solid #1e2535;
                border-radius:10px; margin-top:10px; padding:16px;
                font-size:11px; font-weight:700; color:#64748b;
                letter-spacing:1px;
            }
            QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 4px; }
        """)
        return g

    def _load_values(self):
        c = self.config.get_all()
        self.inp_db_path.setText(c.get('db_path', 'ppe_guardian.db'))
        self.inp_token.setText(c.get('telegram_bot_token', ''))
        self.inp_chatid.setText(c.get('telegram_chat_id', ''))
        self.inp_cooldown.setValue(int(c.get('alert_cooldown_seconds', 30)))
        self.inp_model.setText(c.get('model_path', 'best.pt'))
        self.inp_conf.setValue(float(c.get('confidence_threshold', 0.5)))
        self.inp_capture_dir.setText(c.get('capture_dir', 'captured_violations'))

    def _browse_db_path(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Chọn hoặc tạo file database", "", "SQLite DB (*.db)")
        if path:
            self.inp_db_path.setText(path)

    def _save_db(self):
        db_path = self.inp_db_path.text().strip()
        if not db_path:
            db_path = 'ppe_guardian.db'
        self.config.update({
            'db_path': db_path,
        })
        QMessageBox.information(self, "Đã lưu",
                                 "Cấu hình database đã được lưu!\n"
                                 "Khởi động lại app để áp dụng.")

    def _test_telegram(self):
        token = self.inp_token.text().strip()
        chat_id = self.inp_chatid.text().strip()
        if not token or not chat_id:
            QMessageBox.warning(self, "Thiếu thông tin",
                                 "Vui lòng nhập Bot Token và Chat ID!")
            return
        self.alerter.update_config(token, chat_id,
                                    self.inp_cooldown.value())
        ok, msg = self.alerter.send_test_message()
        if ok:
            self.lbl_tg_status.setText(f"✅ {msg}")
            self.lbl_tg_status.setStyleSheet("color:#16a34a; font-size:12px;")
        else:
            self.lbl_tg_status.setText(f"❌ {msg}")
            self.lbl_tg_status.setStyleSheet("color:#dc2626; font-size:12px;")

    def _save_telegram(self):
        self.config.update({
            'telegram_bot_token': self.inp_token.text().strip(),
            'telegram_chat_id': self.inp_chatid.text().strip(),
            'alert_cooldown_seconds': str(self.inp_cooldown.value()),
        })
        self.alerter.update_config(
            self.inp_token.text().strip(),
            self.inp_chatid.text().strip(),
            self.inp_cooldown.value()
        )
        QMessageBox.information(self, "Đã lưu",
                                 "Cấu hình Telegram đã được lưu!")

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file model", "", "Model files (*.pt)")
        if path:
            self.inp_model.setText(path)

    def _browse_capture_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu ảnh")
        if path:
            self.inp_capture_dir.setText(path)

    def _save_model_config(self):
        self.config.update({
            'model_path': self.inp_model.text(),
            'confidence_threshold': str(self.inp_conf.value()),
            'capture_dir': self.inp_capture_dir.text(),
        })
        QMessageBox.information(self, "Đã lưu",
                                 "Cấu hình model đã được lưu!\n"
                                 "Khởi động lại app để tải model mới.")
