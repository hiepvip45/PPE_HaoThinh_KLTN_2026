"""
PPE Guardian - Main Entry Point
Hệ Thống Giám Sát Thiết Bị Bảo Hộ Lao Động
"""
import sys
import os

# Đảm bảo import đúng thư mục gốc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QPen

from ui.main_window import PPEGuardianWindow


def create_splash() -> QSplashScreen:
    pix = QPixmap(500, 300)
    pix.fill(QColor("#0f1117"))

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background gradient feel
    brush = QBrush(QColor("#161b27"))
    painter.setBrush(brush)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(20, 20, 460, 260, 16, 16)

    # Border
    pen = QPen(QColor("#f97316"))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(20, 20, 460, 260, 16, 16)

    # Icon
    painter.setPen(QColor("#f97316"))
    font = QFont("Segoe UI", 36)
    painter.setFont(font)
    painter.drawText(pix.rect().adjusted(0, 30, 0, 0),
                     Qt.AlignmentFlag.AlignHCenter, "⛑")

    # Title
    font2 = QFont("Segoe UI", 22, QFont.Weight.Bold)
    painter.setFont(font2)
    painter.setPen(QColor("#f1f5f9"))
    painter.drawText(pix.rect().adjusted(0, 110, 0, 0),
                     Qt.AlignmentFlag.AlignHCenter, "PPE Guardian")

    # Subtitle
    font3 = QFont("Segoe UI", 10)
    painter.setFont(font3)
    painter.setPen(QColor("#64748b"))
    painter.drawText(pix.rect().adjusted(0, 160, 0, 0),
                     Qt.AlignmentFlag.AlignHCenter,
                     "HỆ THỐNG GIÁM SÁT BẢO HỘ LAO ĐỘNG")

    # Loading
    font4 = QFont("Segoe UI", 9)
    painter.setFont(font4)
    painter.setPen(QColor("#f97316"))
    painter.drawText(pix.rect().adjusted(0, 210, 0, 0),
                     Qt.AlignmentFlag.AlignHCenter,
                     "Đang khởi động...")

    painter.end()

    splash = QSplashScreen(pix, Qt.WindowType.WindowStaysOnTopHint)
    return splash


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PPE Guardian")
    app.setOrganizationName("PPEGuardian")

    # High DPI support
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    # Splash screen
    splash = create_splash()
    splash.show()
    app.processEvents()

    # Main window
    window = PPEGuardianWindow()

    def show_main():
        splash.finish(window)
        window.show()

    QTimer.singleShot(1500, show_main)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
