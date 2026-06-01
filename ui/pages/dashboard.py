"""
Dashboard Page - Trang tổng quan
"""
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from core.detector import VIOLATION_LABELS_VI


class DashboardPage(QWidget):
    def __init__(self, db, config):
        super().__init__()
        self.db = db
        self.config = config
        self._recent_live = []
        self._setup_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh)
        self._timer.start(30000)

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;")
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setSpacing(14)
        il.setContentsMargins(0, 0, 8, 16)

        # Welcome
        welcome = QLabel("Xin chào! 👋  Hệ thống đang hoạt động")
        welcome.setStyleSheet("color:#64748b; font-size:13px;")
        il.addWidget(welcome)

        # Stat cards
        stat_row = QHBoxLayout()
        stat_row.setSpacing(10)
        self.c_today  = self._stat_card("VI PHẠM HÔM NAY",    "0", "#dc2626")
        self.c_week   = self._stat_card("VI PHẠM TUẦN NÀY",   "0", "#f97316")
        self.c_comp   = self._stat_card("TỶ LỆ TUÂN THỦ",     "–%","#16a34a")
        self.c_person = self._stat_card("LƯỢT NGƯỜI HÔM NAY", "0", "#3b82f6")
        for c in [self.c_today, self.c_week, self.c_comp, self.c_person]:
            stat_row.addWidget(c)
        il.addLayout(stat_row)

        # System status chips
        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self.chip_db    = self._chip("🗄️ Database", False)
        self.chip_tg    = self._chip("📱 Telegram", False)
        self.chip_model = self._chip("🤖 Model", False)
        chip_row.addWidget(self.chip_db)
        chip_row.addWidget(self.chip_tg)
        chip_row.addWidget(self.chip_model)
        chip_row.addStretch()
        il.addLayout(chip_row)

        # Recent violations
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        hdr = QHBoxLayout()
        ttl = QLabel("VI PHẠM GẦN ĐÂY")
        ttl.setStyleSheet("color:#64748b; font-size:11px; font-weight:700; letter-spacing:1px;")
        hdr.addWidget(ttl)
        hdr.addStretch()
        btn_r = QPushButton("🔄")
        btn_r.setFixedSize(30, 30)
        btn_r.setToolTip("Làm mới")
        btn_r.clicked.connect(self.refresh)
        hdr.addWidget(btn_r)
        cl.addLayout(hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Thời gian", "Vi phạm", "Nguồn", "Độ tin cậy", "Telegram"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setFixedHeight(260)
        cl.addWidget(self.table)
        il.addWidget(card)

        il.addStretch()
        scroll.setWidget(inner)
        main.addWidget(scroll, 1)

    def _stat_card(self, label, value, color):
        card = QFrame()
        card.setObjectName("stat_card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lo = QVBoxLayout(card)
        lo.setSpacing(4)
        val = QLabel(value)
        val.setStyleSheet(f"color:{color}; font-size:30px; font-weight:800;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setObjectName("_val")
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#64748b; font-size:10px; font-weight:700; letter-spacing:0.5px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(val)
        lo.addWidget(lbl)
        return card

    def _set_stat(self, card, value):
        for w in card.findChildren(QLabel):
            if w.objectName() == "_val":
                w.setText(value)
                break

    def _chip(self, text, active):
        lbl = QLabel(text)
        c  = "#16a34a" if active else "#4a5568"
        bg = "#052e16" if active else "#1e2535"
        lbl.setStyleSheet(
            f"background:{bg}; color:{c}; border-radius:12px;"
            f"padding:4px 12px; font-size:12px; font-weight:600;")
        return lbl

    def update_system_status(self, db_ok, tg_ok, model_ok):
        def style(ok):
            c  = "#16a34a" if ok else "#dc2626"
            bg = "#052e16" if ok else "#2d0a0a"
            return (f"background:{bg}; color:{c}; border-radius:12px;"
                    f"padding:4px 12px; font-size:12px; font-weight:600;")
        self.chip_db.setStyleSheet(style(db_ok))
        self.chip_db.setText("🗄️ Database " + ("✓" if db_ok else "✗"))
        self.chip_tg.setStyleSheet(style(tg_ok))
        self.chip_tg.setText("📱 Telegram " + ("✓" if tg_ok else "–"))
        self.chip_model.setStyleSheet(style(model_ok))
        self.chip_model.setText("🤖 Model " + ("✓" if model_ok else "✗"))

    def add_live_violation(self, violation_type, source_name, confidence):
        label = VIOLATION_LABELS_VI.get(violation_type, violation_type)
        self._recent_live.insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'label': label, 'vtype': violation_type,
            'source': source_name, 'conf': confidence
        })
        self._recent_live = self._recent_live[:50]
        self._fill_live_table(self._recent_live)

    def _fill_live_table(self, items):
        self.table.setRowCount(len(items))
        for i, r in enumerate(items):
            is_fall = r.get('vtype', '') == 'Fall-Detected'
            cells = [
                r.get('time', ''),
                r.get('label', r.get('violation_type', '')),
                r.get('source', r.get('source_name', '')),
                f"{float(r.get('conf', r.get('confidence', 0))):.0%}",
                "✅" if r.get('telegram_sent') else r.get('tg', '–'),
            ]
            for col, txt in enumerate(cells):
                item = QTableWidgetItem(str(txt))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_fall:
                    item.setForeground(QColor("#dc2626"))
                elif col == 1:
                    item.setForeground(QColor("#f97316"))
                self.table.setItem(i, col, item)

    def refresh(self):
        if not self.db:
            return
        try:
            today = self.db.get_summary_today()
            self._set_stat(self.c_today, str(today.get('total_violations') or 0))
            self._set_stat(self.c_person, str(int(today.get('total_persons') or 0)))

            week = self.db.count_violations(datetime.now() - timedelta(days=7))
            self._set_stat(self.c_week, str(week))

            stats = self.db.get_compliance_stats(7)
            total = max(stats.get('total') or 1, 1)
            comp  = stats.get('compliant') or 0
            self._set_stat(self.c_comp, f"{comp/total*100:.0f}%")

            rows = self.db.get_violations(limit=20)
            # Normalize keys for _fill_live_table
            mapped = []
            for r in rows:
                mapped.append({
                    'time':   str(r.get('violation_at', ''))[:19],
                    'label':  VIOLATION_LABELS_VI.get(r.get('violation_type',''), r.get('violation_type','')),
                    'vtype':  r.get('violation_type', ''),
                    'source': r.get('source_name', ''),
                    'conf':   r.get('confidence', 0),
                    'tg':     "✅" if r.get('telegram_sent') else "❌",
                })
            self._fill_live_table(mapped)
        except Exception as e:
            print(f"[Dashboard] refresh error: {e}")
