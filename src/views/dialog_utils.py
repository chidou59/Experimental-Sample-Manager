from PySide6.QtWidgets import (QDialogButtonBox, QDateTimeEdit, QCalendarWidget)
from PySide6.QtCore import Qt, QDateTime, QTime

# === 定义一组常用的科研 Emoji 图标 ===
SAMPLE_ICONS = [
    "🧪", "🧫", "🪨", "🧱", "⏳", "💧",
    "🌡️", "🔬", "🧊", "🏺", "📊", "📦"
]

# === 基础弹窗样式 ===
DIALOG_STYLES = """
    QDialog { background-color: #ffffff; }
    QLabel { color: #2c3e50; font-size: 14px; font-weight: 600; font-family: "Microsoft YaHei"; }

    QLineEdit, QDoubleSpinBox, QDateTimeEdit, QTextEdit, QComboBox {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 6px 10px;
        background-color: #f9f9f9; 
        color: #333333;
        font-size: 14px;
        font-family: "Microsoft YaHei";
        min-height: 20px;
    }
    QLineEdit:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus, QTextEdit:focus, QComboBox:focus {
        background-color: #ffffff;
        border: 1px solid #3498db;
    }
    QLineEdit:read-only { background-color: #f0f0f0; color: #888; }

    /* 下拉菜单美化 */
    QComboBox::drop-down {
        border: none; background: transparent; width: 20px;
    }
    QComboBox QAbstractItemView {
        border: 1px solid #3498db;
        background-color: white;
        selection-background-color: #ecf5ff;
        selection-color: #3498db;
        outline: none;
        padding: 4px;
    }
"""

# === 日历控件专属美化样式 ===
CALENDAR_STYLES = """
    /* 1. 整体背景和导航条 */
    QCalendarWidget QWidget#qt_calendar_navigationbar { 
        background-color: #3498db; 
        min-height: 35px;
    }
    QCalendarWidget QToolButton {
        color: white;
        background-color: transparent;
        border: none;
        font-weight: bold;
        icon-size: 20px;
        height: 30px;
    }
    QCalendarWidget QToolButton:hover {
        background-color: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }
    QCalendarWidget QToolButton::menu-indicator { image: none; }

    /* 2. 年份输入框和月份菜单 */
    QCalendarWidget QSpinBox {
        background-color: transparent;
        color: white;
        border: none;
        selection-background-color: rgba(255, 255, 255, 0.3);
        font-weight: bold;
    }
    QCalendarWidget QMenu { background-color: white; color: #333; border: 1px solid #ccc; }

    /* 3. 日期网格区域 */
    QCalendarWidget QAbstractItemView:enabled {
        background-color: white;
        color: #333;
        selection-background-color: #3498db; 
        selection-color: white;             
        font-family: "Microsoft YaHei";
        font-size: 13px;
        outline: none;
    }
    QCalendarWidget QAbstractItemView:disabled { color: #bbb; }
"""


def apply_dialog_theme(dialog, button_box=None):
    """应用统一样式到对话框"""
    dialog.setStyleSheet(DIALOG_STYLES)
    if button_box:
        ok_btn = button_box.button(QDialogButtonBox.Ok)
        if ok_btn:
            ok_btn.setText("确定")
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.setStyleSheet(
                "QPushButton { background-color: #3498db; color: white; border: none; border-radius: 6px; padding: 8px 25px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #2980b9; }")

        cancel_btn = button_box.button(QDialogButtonBox.Cancel)
        if cancel_btn:
            cancel_btn.setText("取消")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.setStyleSheet(
                "QPushButton { background-color: #f1f2f6; color: #7f8c8d; border: none; border-radius: 6px; padding: 8px 25px; font-size: 14px; } QPushButton:hover { background-color: #e4e7eb; color: #2c3e50; }")


def create_datetime_edit(init_str=None):
    """创建一个带有自定义样式的日期时间选择器"""
    dte = QDateTimeEdit()
    dte.setCalendarPopup(True)
    dte.setDisplayFormat("yyyy-MM-dd-HH':00'")
    dte.setMinimumWidth(200)
    dte.setStyleSheet(DIALOG_STYLES + CALENDAR_STYLES)

    current = QDateTime.currentDateTime()
    current.setTime(QTime(current.time().hour(), 0, 0))
    if init_str and init_str != "-":
        dt = QDateTime.fromString(init_str, "yyyy-MM-dd-HH:00")
        if not dt.isValid():
            dt = QDateTime.fromString(init_str, "yyyy-MM-dd")
            dt.setTime(QTime(0, 0, 0))
        if dt.isValid():
            dte.setDateTime(dt)
        else:
            dte.setDateTime(current)
    else:
        dte.setDateTime(current)
    return dte