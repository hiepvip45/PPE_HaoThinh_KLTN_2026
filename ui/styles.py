"""
Styles - Dark industrial theme cho PPE Guardian
"""

APP_STYLE = """
/* ─── Base ─────────────────────────────────── */
QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0f1117;
}

/* ─── Sidebar ───────────────────────────────── */
#sidebar {
    background-color: #161b27;
    border-right: 1px solid #1e2535;
    min-width: 220px;
    max-width: 220px;
}

#logo_label {
    color: #f97316;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 8px 0;
}

#sub_logo {
    color: #64748b;
    font-size: 10px;
    letter-spacing: 2px;
}

/* ─── Nav Buttons ───────────────────────────── */
QPushButton#nav_btn {
    background: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_btn:hover {
    background-color: #1e2535;
    color: #e2e8f0;
}

QPushButton#nav_btn[active="true"] {
    background-color: #1e3a5f;
    color: #f97316;
    border-left: 3px solid #f97316;
    font-weight: 700;
}

/* ─── Content Area ──────────────────────────── */
#content_area {
    background-color: #0f1117;
}

#page_title {
    color: #f1f5f9;
    font-size: 22px;
    font-weight: 700;
}

/* ─── Cards ─────────────────────────────────── */
#card {
    background-color: #161b27;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 16px;
}

#stat_card {
    background-color: #161b27;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 20px;
    min-width: 160px;
}

#stat_value {
    font-size: 32px;
    font-weight: 800;
    color: #f97316;
}

#stat_label {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
    letter-spacing: 0.5px;
}

/* ─── Buttons ───────────────────────────────── */
QPushButton {
    background-color: #1e2535;
    color: #e2e8f0;
    border: 1px solid #2d3748;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2d3748;
    border-color: #4a5568;
}

QPushButton:pressed {
    background-color: #1a202c;
}

QPushButton#btn_primary {
    background-color: #f97316;
    color: #fff;
    border: none;
    font-weight: 700;
    padding: 10px 24px;
    border-radius: 8px;
}

QPushButton#btn_primary:hover {
    background-color: #ea6c0a;
}

QPushButton#btn_primary:disabled {
    background-color: #4a3520;
    color: #7a5a3a;
}

QPushButton#btn_danger {
    background-color: #dc2626;
    color: #fff;
    border: none;
    font-weight: 700;
    padding: 10px 24px;
    border-radius: 8px;
}

QPushButton#btn_danger:hover {
    background-color: #b91c1c;
}

QPushButton#btn_success {
    background-color: #16a34a;
    color: #fff;
    border: none;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: 8px;
}

QPushButton#btn_success:hover {
    background-color: #15803d;
}

/* ─── Input Fields ──────────────────────────── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1e2535;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e2e8f0;
    selection-background-color: #f97316;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #f97316;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #1e2535;
    border: 1px solid #2d3748;
    selection-background-color: #f97316;
    color: #e2e8f0;
}

/* ─── Table ─────────────────────────────────── */
QTableWidget {
    background-color: #161b27;
    border: 1px solid #1e2535;
    border-radius: 8px;
    gridline-color: #1e2535;
    selection-background-color: #1e3a5f;
    alternate-background-color: #1a2030;
}

QTableWidget::item {
    padding: 8px 12px;
    border: none;
    color: #e2e8f0;
}

QTableWidget::item:selected {
    background-color: #1e3a5f;
    color: #f97316;
}

QHeaderView::section {
    background-color: #0f1117;
    color: #64748b;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #1e2535;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ─── ScrollBar ─────────────────────────────── */
QScrollBar:vertical {
    background: #0f1117;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #2d3748;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #4a5568;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0f1117;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: #2d3748;
    border-radius: 4px;
}

/* ─── Tabs ──────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #1e2535;
    border-radius: 8px;
    background: #161b27;
}

QTabBar::tab {
    background: transparent;
    color: #64748b;
    padding: 10px 20px;
    border: none;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #f97316;
    border-bottom: 2px solid #f97316;
}

QTabBar::tab:hover {
    color: #e2e8f0;
}

/* ─── CheckBox ──────────────────────────────── */
QCheckBox {
    color: #e2e8f0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid #2d3748;
    background: #1e2535;
}

QCheckBox::indicator:checked {
    background: #f97316;
    border-color: #f97316;
}

/* ─── Slider ────────────────────────────────── */
QSlider::groove:horizontal {
    height: 4px;
    background: #2d3748;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #f97316;
    border: none;
    width: 16px; height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}

QSlider::sub-page:horizontal {
    background: #f97316;
    border-radius: 2px;
}

/* ─── Label / Status ────────────────────────── */
#status_bar {
    background: #161b27;
    border-top: 1px solid #1e2535;
    color: #64748b;
    font-size: 12px;
    padding: 4px 16px;
}

#badge_violation {
    background: #dc2626;
    color: white;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
}

#badge_ok {
    background: #16a34a;
    color: white;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#section_title {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

/* ─── Date Edit ─────────────────────────────── */
QDateEdit {
    background-color: #1e2535;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 7px 10px;
    color: #e2e8f0;
}

QDateEdit::drop-down {
    border: none;
    width: 24px;
}

QCalendarWidget {
    background-color: #1e2535;
    color: #e2e8f0;
}

/* ─── Message Box ───────────────────────────── */
QMessageBox {
    background-color: #161b27;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ─── Tooltip ───────────────────────────────── */
QToolTip {
    background-color: #1e2535;
    color: #e2e8f0;
    border: 1px solid #2d3748;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ─── Progress Bar ──────────────────────────── */
QProgressBar {
    background: #1e2535;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: #f97316;
    border-radius: 4px;
}
"""
