import sys
import os
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

import config
from src.views.main_window import MainWindow

# === 全局样式表 (QSS) ===
# 这里定义了所有控件的默认长相
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
    app = QApplication(sys.argv)

    # 1. 设置全局字体 (稍微调大一点点，更清晰)
    font = QFont("Microsoft YaHei", 10)  # 这里的10是pt，大概对应13-14px
    app.setFont(font)

    # 2. 应用全局样式
    app.setStyleSheet(GLOBAL_STYLES)

    # 3. 路径检查逻辑
    if config.DATA_ROOT is None:
        QMessageBox.information(None, "欢迎", "欢迎使用试样管理器！\n请先选择一个文件夹作为您的数据仓库。")
        selected_path = QFileDialog.getExistingDirectory(None, "选择数据存储根目录")

        if selected_path:
            config.save_settings(selected_path)
        else:
            sys.exit(0)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()