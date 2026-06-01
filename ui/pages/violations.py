"""
Violations Page - Xem lịch sử vi phạm, tìm kiếm, lọc, xuất báo cáo
"""
import csv
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
    QHeaderView, QFileDialog, QMessageBox, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from core.detector import VIOLATION_LABELS_VI, VIOLATION_CLASSES


PAGE_SIZE = 100


class ViolationsPage(QWidget):
    def __init__(self, db, config):
        super().__init__()
        self.db = db
        self.config = config
        self.current_offset = 0
        self.total_count = 0
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ── Filter bar ──
        filter_card = QFrame()
        filter_card.setObjectName("card")
        fl = QHBoxLayout(filter_card)
        fl.setSpacing(10)

        # Date range
        fl.addWidget(QLabel("Từ:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setFixedWidth(120)
        fl.addWidget(self.date_from)

        fl.addWidget(QLabel("Đến:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setFixedWidth(120)
        fl.addWidget(self.date_to)

        fl.addWidget(QLabel("Loại vi phạm:"))
        self.cmb_type = QComboBox()
        self.cmb_type.setFixedWidth(200)
        self.cmb_type.addItem("Tất cả")
        for cls in sorted(VIOLATION_CLASSES):
            label = VIOLATION_LABELS_VI.get(cls, cls)
            self.cmb_type.addItem(f"{label}", cls)
        fl.addWidget(self.cmb_type)

        btn_search = QPushButton("🔍  Tìm kiếm")
        btn_search.setObjectName("btn_primary")
        btn_search.clicked.connect(self._search)
        fl.addWidget(btn_search)

        btn_reset = QPushButton("↺  Đặt lại")
        btn_reset.clicked.connect(self._reset_filters)
        fl.addWidget(btn_reset)

        fl.addStretch()

        btn_export = QPushButton("📥  Xuất CSV")
        btn_export.setObjectName("btn_success")
        btn_export.clicked.connect(self._export_csv)
        fl.addWidget(btn_export)

        layout.addWidget(filter_card)

        # ── Summary row ──
        sum_row = QHBoxLayout()
        self.lbl_total = QLabel("Tổng: 0 vi phạm")
        self.lbl_total.setStyleSheet("color:#f97316; font-weight:700; font-size:14px;")
        sum_row.addWidget(self.lbl_total)
        sum_row.addStretch()
        self.lbl_page = QLabel("")
        self.lbl_page.setStyleSheet("color:#64748b; font-size:12px;")
        sum_row.addWidget(self.lbl_page)
        layout.addLayout(sum_row)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "STT", "Thời gian", "Loại vi phạm", "Nguồn", "Loại nguồn",
            "Độ tin cậy", "Telegram"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        layout.addWidget(self.table, 1)

        # ── Pagination ──
        pag_row = QHBoxLayout()
        self.btn_prev = QPushButton("◀  Trước")
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next = QPushButton("Sau  ▶")
        self.btn_next.clicked.connect(self._next_page)
        pag_row.addWidget(self.btn_prev)
        pag_row.addStretch()
        pag_row.addWidget(self.btn_next)
        layout.addLayout(pag_row)

    def _get_filters(self):
        start_dt = self.date_from.date().toPyDate()
        end_dt = self.date_to.date().toPyDate()
        # end of day
        from datetime import datetime, time
        end_dt = datetime.combine(end_dt, time(23, 59, 59))

        vtype = None
        if self.cmb_type.currentText() != "Tất cả":
            vtype = self.cmb_type.currentData()
        return start_dt, end_dt, vtype

    def _search(self):
        self.current_offset = 0
        self.load_data()

    def _reset_filters(self):
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.cmb_type.setCurrentIndex(0)
        self.current_offset = 0
        self.load_data()

    def load_data(self):
        if not self.db:
            return
        start, end, vtype = self._get_filters()
        self.total_count = self.db.count_violations(start, end, vtype)
        rows = self.db.get_violations(start, end, vtype, PAGE_SIZE, self.current_offset)

        self.lbl_total.setText(f"Tổng: {self.total_count:,} vi phạm")
        page_num = self.current_offset // PAGE_SIZE + 1
        total_pages = max(1, (self.total_count + PAGE_SIZE - 1) // PAGE_SIZE)
        self.lbl_page.setText(f"Trang {page_num}/{total_pages}")

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            stt = self.current_offset + i + 1
            vtype_val = row.get('violation_type', '')
            label = VIOLATION_LABELS_VI.get(vtype_val, vtype_val)
            is_fall = vtype_val == 'Fall-Detected'

            items = [
                QTableWidgetItem(str(stt)),
                QTableWidgetItem(str(row.get('violation_at', ''))[:19]),
                QTableWidgetItem(label),
                QTableWidgetItem(row.get('source_name', '')),
                QTableWidgetItem(row.get('source_type', '')),
                QTableWidgetItem(f"{row.get('confidence', 0):.0%}"),
                QTableWidgetItem("✅" if row.get('telegram_sent') else "❌"),
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_fall:
                    item.setForeground(QColor("#dc2626"))
                elif col == 2:
                    item.setForeground(QColor("#f97316"))
                self.table.setItem(i, col, item)

        self.btn_prev.setEnabled(self.current_offset > 0)
        self.btn_next.setEnabled(
            self.current_offset + PAGE_SIZE < self.total_count)

    def _prev_page(self):
        self.current_offset = max(0, self.current_offset - PAGE_SIZE)
        self.load_data()

    def _next_page(self):
        self.current_offset += PAGE_SIZE
        self.load_data()

    def _export_csv(self):
        if not self.db:
            return
        start, end, vtype = self._get_filters()
        rows = self.db.export_violations_csv(start, end, vtype)
        if not rows:
            QMessageBox.information(self, "Thông báo", "Không có dữ liệu để xuất!")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu báo cáo CSV", 
            f"violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["STT", "Thời gian", "Loại vi phạm",
                                  "Nguồn", "Loại nguồn", "Độ tin cậy",
                                  "Telegram đã gửi", "Đường dẫn ảnh"])
                for idx, row in enumerate(rows, 1):
                    writer.writerow([
                        idx,
                        str(row.get('violation_at', ''))[:19],
                        VIOLATION_LABELS_VI.get(row.get('violation_type', ''),
                                                 row.get('violation_type', '')),
                        row.get('source_name', ''),
                        row.get('source_type', ''),
                        f"{row.get('confidence', 0):.0%}",
                        "Có" if row.get('telegram_sent') else "Không",
                        row.get('image_path', '')
                    ])
            QMessageBox.information(
                self, "Thành công",
                f"Đã xuất {len(rows):,} bản ghi ra:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {e}")

    def refresh(self):
        self.load_data()
