"""
Statistics Page - Thống kê và biểu đồ
"""
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt

try:
    import matplotlib
    matplotlib.use('QtAgg')
    import matplotlib.ticker
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

CHART_BG = '#161b27'
CHART_FG = '#94a3b8'
ACCENT   = '#f97316'
GREEN    = '#16a34a'
RED      = '#dc2626'
COLORS   = ['#f97316','#3b82f6','#16a34a','#dc2626',
            '#8b5cf6','#06b6d4','#f59e0b','#ec4899']

from core.detector import VIOLATION_LABELS_VI


class ChartCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        lbl = QLabel(title)
        lbl.setStyleSheet("color:#64748b; font-size:11px; font-weight:700; letter-spacing:1px;")
        self._layout.addWidget(lbl)
        self._content = QVBoxLayout()
        self._layout.addLayout(self._content)

    def set_widget(self, widget):
        while self._content.count():
            item = self._content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._content.addWidget(widget)


class StatBox(QFrame):
    def __init__(self, label: str, value: str, color=ACCENT, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lo = QVBoxLayout(self)
        lo.setSpacing(4)
        self._val = QLabel(value)
        self._val.setStyleSheet(f"color:{color}; font-size:28px; font-weight:800;")
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#64748b; font-size:10px; font-weight:700; letter-spacing:0.5px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(self._val)
        lo.addWidget(lbl)

    def update_value(self, v: str):
        self._val.setText(v)


class StatisticsPage(QWidget):
    def __init__(self, db, config):
        super().__init__()
        self.db = db
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(12)

        # Controls
        top = QHBoxLayout()
        top.addWidget(QLabel("Khoảng thời gian:"))
        self.cmb = QComboBox()
        self.cmb.addItems(["7 ngày", "30 ngày", "90 ngày", "12 tháng"])
        self.cmb.setCurrentIndex(1)
        self.cmb.setFixedWidth(140)
        self.cmb.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.cmb)
        top.addStretch()
        btn = QPushButton("🔄  Làm mới")
        btn.setObjectName("btn_primary")
        btn.clicked.connect(self.refresh)
        top.addWidget(btn)
        main.addLayout(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setSpacing(12)
        il.setContentsMargins(0, 0, 8, 16)

        # Stat boxes
        row = QHBoxLayout()
        row.setSpacing(10)
        self.s_vio    = StatBox("TỔNG VI PHẠM",        "–", RED)
        self.s_today  = StatBox("VI PHẠM HÔM NAY",     "–", ACCENT)
        self.s_comp   = StatBox("TỶ LỆ TUÂN THỦ",      "–%", GREEN)
        self.s_person = StatBox("LƯỢT NGƯỜI PHÁT HIỆN","–", '#3b82f6')
        for s in [self.s_vio, self.s_today, self.s_comp, self.s_person]:
            row.addWidget(s)
        il.addLayout(row)

        # Charts
        r1 = QHBoxLayout()
        r1.setSpacing(10)
        self.c_timeline = ChartCard("VI PHẠM THEO THỜI GIAN")
        self.c_timeline.setFixedHeight(300)
        r1.addWidget(self.c_timeline, 2)
        self.c_pie = ChartCard("PHÂN BỐ LOẠI VI PHẠM")
        self.c_pie.setFixedHeight(300)
        r1.addWidget(self.c_pie, 1)
        il.addLayout(r1)

        self.c_bar = ChartCard("TOP VI PHẠM THEO LOẠI")
        self.c_bar.setFixedHeight(280)
        il.addWidget(self.c_bar)

        il.addStretch()
        scroll.setWidget(inner)
        main.addWidget(scroll, 1)

    def refresh(self):
        if not self.db:
            return
        period_map = {"7 ngày": 7, "30 ngày": 30, "90 ngày": 90, "12 tháng": 365}
        days = period_map.get(self.cmb.currentText(), 30)

        try:
            total_vio = self.db.count_violations(datetime.now() - timedelta(days=days))
            today_stats = self.db.get_summary_today()
            stats = self.db.get_compliance_stats(days)

            self.s_vio.update_value(f"{total_vio:,}")
            self.s_today.update_value(str(today_stats.get('total_violations') or 0))

            total = max(stats.get('total') or 1, 1)
            compliant = stats.get('compliant') or 0
            self.s_comp.update_value(f"{compliant/total*100:.1f}%")

            avg_p = stats.get('avg_persons')
            self.s_person.update_value(f"{int(avg_p or 0):,}")

            if not HAS_MPL:
                return

            type_data = self.db.get_violations_by_type(days)

            if days <= 90:
                tl_data = self.db.get_violations_by_day(days)
                self._draw_line(tl_data)
            else:
                tl_data = self.db.get_monthly_violations()
                self._draw_bar_monthly(tl_data)

            self._draw_pie(type_data)
            self._draw_hbar(type_data)

        except Exception as e:
            print(f"[Stats] refresh error: {e}")

    def _make_fig(self, figsize=(8, 3)):
        fig = Figure(figsize=figsize, facecolor=CHART_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CHART_BG)
        ax.tick_params(colors=CHART_FG, labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor('#1e2535')
        fig.tight_layout(pad=1.5)
        return fig, ax

    def _draw_line(self, data):
        fig, ax = self._make_fig((9, 3))
        if data:
            dates  = [str(r['day'])[5:] for r in data]   # MM-DD
            counts = [int(r['count']) for r in data]
            x = range(len(dates))
            ax.plot(list(x), counts, color=ACCENT, linewidth=2.5, marker='o', markersize=4)
            ax.fill_between(list(x), counts, alpha=0.12, color=ACCENT)
            step = max(1, len(dates)//10)
            ax.set_xticks(list(x)[::step])
            ax.set_xticklabels(dates[::step], rotation=45, fontsize=8, color=CHART_FG)
            ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
            ax.tick_params(axis='y', colors=CHART_FG)
        else:
            ax.text(0.5, 0.5, 'Không có dữ liệu', transform=ax.transAxes,
                    ha='center', va='center', color=CHART_FG, fontsize=12)
        self.c_timeline.set_widget(FigureCanvas(fig))

    def _draw_bar_monthly(self, data):
        fig, ax = self._make_fig((9, 3))
        if data:
            months = [r['month'] for r in data]
            counts = [int(r['count']) for r in data]
            ax.bar(range(len(months)), counts, color=ACCENT, alpha=0.85, width=0.6)
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(months, rotation=45, fontsize=8, color=CHART_FG)
            ax.tick_params(axis='y', colors=CHART_FG)
        else:
            ax.text(0.5, 0.5, 'Không có dữ liệu', transform=ax.transAxes,
                    ha='center', va='center', color=CHART_FG, fontsize=12)
        self.c_timeline.set_widget(FigureCanvas(fig))

    def _draw_pie(self, data):
        fig = Figure(figsize=(4, 3.5), facecolor=CHART_BG)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CHART_BG)
        if data:
            labels = [VIOLATION_LABELS_VI.get(r['violation_type'], r['violation_type'])
                      for r in data]
            sizes  = [int(r['count']) for r in data]
            short  = [l[:14]+'…' if len(l) > 14 else l for l in labels]
            wedges, texts, autotexts = ax.pie(
                sizes, labels=short, colors=COLORS[:len(sizes)],
                autopct='%1.1f%%', pctdistance=0.8,
                textprops={'color': CHART_FG, 'fontsize': 8})
            for at in autotexts:
                at.set_fontsize(7)
                at.set_color('#fff')
        else:
            ax.text(0.5, 0.5, 'Không có dữ liệu', transform=ax.transAxes,
                    ha='center', va='center', color=CHART_FG, fontsize=12)
        fig.tight_layout(pad=1)
        self.c_pie.set_widget(FigureCanvas(fig))

    def _draw_hbar(self, data):
        fig, ax = self._make_fig((9, max(2.5, len(data)*0.45 + 0.5)))
        if data:
            labels = [VIOLATION_LABELS_VI.get(r['violation_type'], r['violation_type'])
                      for r in data]
            counts = [int(r['count']) for r in data]
            y = range(len(labels))
            bars = ax.barh(list(y), counts, color=COLORS[:len(labels)], height=0.55)
            ax.set_yticks(list(y))
            ax.set_yticklabels(labels, fontsize=9, color=CHART_FG)
            ax.tick_params(axis='x', colors=CHART_FG)
            for bar, val in zip(bars, counts):
                ax.text(bar.get_width() + max(counts)*0.01,
                        bar.get_y() + bar.get_height()/2,
                        str(val), va='center', color=CHART_FG, fontsize=9)
        else:
            ax.text(0.5, 0.5, 'Không có dữ liệu', transform=ax.transAxes,
                    ha='center', va='center', color=CHART_FG, fontsize=12)
        self.c_bar.set_widget(FigureCanvas(fig))
