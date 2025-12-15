from PySide6.QtWidgets import QSplashScreen, QProgressBar
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QRect

class ModernSplashScreen(QSplashScreen):
    def __init__(self):
        # 1. 动态绘制一张背景图 (600x350)
        pixmap = QPixmap(600, 350)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆角矩形背景 (深蓝渐变)
        gradient = QLinearGradient(0, 0, 600, 350)
        gradient.setColorAt(0, QColor("#2c3e50"))  # 深蓝
        gradient.setColorAt(1, QColor("#3498db"))  # 亮蓝

        rect = QRect(0, 0, 600, 350)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 15, 15)

        # 绘制 Logo/Emoji
        font_icon = QFont("Segoe UI Emoji", 60)
        if not font_icon.exactMatch():
            font_icon = QFont("Apple Color Emoji", 60)
        painter.setFont(font_icon)
        painter.setPen(QColor("white"))
        painter.drawText(QRect(0, 50, 600, 100), Qt.AlignCenter, "🔬")

        # 绘制主标题
        font_title = QFont("Microsoft YaHei", 24, QFont.Bold)
        painter.setFont(font_title)
        painter.drawText(QRect(0, 160, 600, 50), Qt.AlignCenter, "试样数据管理平台")

        # 绘制副标题/版本号
        font_sub = QFont("Microsoft YaHei", 12)
        painter.setFont(font_sub)
        painter.setPen(QColor("#ecf0f1"))
        painter.drawText(QRect(0, 210, 600, 30), Qt.AlignCenter, "Experimental Sample Manager v.2.1")

        painter.end()

        super().__init__(pixmap)

        # 2. 添加进度条
        self.progress = QProgressBar(self)
        self.progress.setGeometry(50, 280, 500, 8) # 位置和大小
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 4px;
            }
        """)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)

    def update_progress(self, value):
        self.progress.setValue(value)