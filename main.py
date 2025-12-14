import sys
import os
import time
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide6.QtCore import Qt

import config
from src.views.main_window import MainWindow
from src.views.splash_screen import ModernSplashScreen

# === 全局样式表 (QSS) ===
GLOBAL_STYLES = """
/* 全局字体与背景 */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #333;
}

/* 主窗口背景 */
QMainWindow {
    background-color: #f4f6f9; /* 浅灰背景，护眼 */
}

/* 按钮通用样式 */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    padding: 6px 16px;
    color: #606266;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #ecf5ff;
    color: #409eff;
    border-color: #c6e2ff;
}
QPushButton:pressed {
    background-color: #d9ecff;
}

/* 蓝色主按钮 (Primary Button) */
QPushButton[class="primary"] {
    background-color: #3498db; /* 实验室蓝 */
    color: white;
    border: none;
}
QPushButton[class="primary"]:hover {
    background-color: #2980b9;
}

/* 输入框样式 */
QLineEdit, QTextEdit, QDoubleSpinBox, QDateEdit, QDateTimeEdit {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 5px;
    background: white;
    selection-background-color: #3498db;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3498db;
}

/* 表格样式 */
QTableWidget {
    background-color: white;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    gridline-color: #ebeef5;
    selection-background-color: #ecf5ff;
    selection-color: #606266;
}
QHeaderView::section {
    background-color: #f5f7fa;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #ebeef5;
    font-weight: bold;
    color: #909399;
}

/* 滚动条美化 */
QScrollBar:vertical {
    border: none;
    background: #f4f6f9;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #c0c4cc;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #909399;
}
"""


def main():
    # 高分屏适配
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)

    # 1. 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    app.setStyleSheet(GLOBAL_STYLES)

    # === 2. 显示启动动画 ===
    splash = ModernSplashScreen()
    splash.show()

    # 模拟加载过程
    loading_steps = [
        (10, "正在初始化核心组件..."),
        (30, "加载用户配置文件..."),
        (60, "校验数据完整性..."),
        (80, "准备用户界面..."),
        (100, "启动完成")
    ]

    for progress, msg in loading_steps:
        splash.update_progress(progress)
        splash.showMessage(f"\n\n\n\n\n\n\n\n\n\n{msg}", int(Qt.AlignBottom | Qt.AlignCenter), Qt.white)
        t_end = time.time() + 0.3
        while time.time() < t_end:
            app.processEvents()

    # === 3. 路径检查逻辑 ===
    if config.DATA_ROOT is None:
        splash.hide()
        QMessageBox.information(None, "欢迎", "欢迎使用试样管理器！\n请先选择一个文件夹作为您的数据仓库。")
        selected_path = QFileDialog.getExistingDirectory(None, "选择数据存储根目录")

        if selected_path:
            config.save_settings(selected_path)
            splash.show()
        else:
            sys.exit(0)

    # === 4. 启动主窗口 ===
    window = MainWindow()

    # 动画结束，切换到主窗口
    splash.finish(window)
    # 根据 main_window.py 中的设置，这里可以直接 show
    # (如果 main_window.py 中用了 showMaximized，这里也生效)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()