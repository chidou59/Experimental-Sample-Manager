import sys
import os
import time
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide6.QtCore import Qt

# 【优化 1】只在顶部导入轻量级模块 (config)，重型模块移到后面
import config

# 注意：这里不再顶部导入 MainWindow 和 FileManager，防止阻塞启动

# === 全局样式表 (QSS) ===
GLOBAL_STYLES = """
/* 全局字体与背景 */
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #333;
}
/* ... (样式保持不变，为了节省篇幅，这里引用您原本的样式) ... */
QMessageBox { background-color: #ffffff; }
QMessageBox QLabel { color: #333333; background-color: transparent; }
QMainWindow { background-color: #f4f6f9; }
QPushButton { background-color: #ffffff; border: 1px solid #dcdfe6; border-radius: 6px; padding: 6px 16px; color: #606266; font-weight: 500; }
QPushButton:hover { background-color: #ecf5ff; color: #409eff; border-color: #c6e2ff; }
QPushButton:pressed { background-color: #d9ecff; }
QPushButton[class="primary"] { background-color: #3498db; color: white; border: none; }
QPushButton[class="primary"]:hover { background-color: #2980b9; }
QLineEdit, QTextEdit, QDoubleSpinBox, QDateEdit, QDateTimeEdit { border: 1px solid #dcdfe6; border-radius: 4px; padding: 5px; background: white; selection-background-color: #3498db; }
QLineEdit:focus, QTextEdit:focus { border: 1px solid #3498db; }
QTableWidget { background-color: white; border: 1px solid #ebeef5; border-radius: 4px; gridline-color: #ebeef5; selection-background-color: #ecf5ff; selection-color: #606266; }
QHeaderView::section { background-color: #f5f7fa; padding: 8px; border: none; border-bottom: 1px solid #ebeef5; font-weight: bold; color: #909399; }
QScrollBar:vertical { border: none; background: #f4f6f9; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: #c0c4cc; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: #909399; }
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

    # === 【优化 2】先显示启动页，再加载重型库 ===
    # 必须先导入 Splash，因为它只依赖 PySide6 (比较快)
    from src.views.splash_screen import ModernSplashScreen
    splash = ModernSplashScreen()
    splash.show()

    # 强制刷新界面，确保启动图立刻显示出来，而不是白板
    app.processEvents()

    # === 【优化 3】在进度条更新过程中，进行真正的“懒加载” ===
    # 以前这里是假的 time.sleep，现在我们用来做真正的 import

    # 阶段 1: 加载基础配置
    splash.update_progress(10)
    splash.showMessage("\n\n\n\n\n\n\n\n\n\n正在初始化核心组件...", int(Qt.AlignBottom | Qt.AlignCenter), Qt.white)
    app.processEvents()

    # 阶段 2: 加载数据管理器 (这里会导入 pandas, scipy，最耗时！)
    splash.update_progress(30)
    splash.showMessage("\n\n\n\n\n\n\n\n\n\n正在加载数据引擎 (Pandas/Scipy)...", int(Qt.AlignBottom | Qt.AlignCenter),
                       Qt.white)
    app.processEvents()

    # --- 核心修改：在这里 Import ---
    from src.controllers.file_manager import FileManager
    # -----------------------------

    # 阶段 3: 加载主界面 (这里会导入 matplotlib)
    splash.update_progress(70)
    splash.showMessage("\n\n\n\n\n\n\n\n\n\n正在构建用户界面...", int(Qt.AlignBottom | Qt.AlignCenter), Qt.white)
    app.processEvents()

    # --- 核心修改：在这里 Import ---
    from src.views.main_window import MainWindow
    # -----------------------------

    splash.update_progress(90)
    splash.showMessage("\n\n\n\n\n\n\n\n\n\n准备就绪...", int(Qt.AlignBottom | Qt.AlignCenter), Qt.white)
    app.processEvents()

    # === 3. 路径检查逻辑 (保持原有逻辑) ===
    if config.DATA_ROOT is None:
        splash.hide()
        QMessageBox.information(None, "欢迎", "欢迎使用试样管理器！\n请先选择一个文件夹作为您的数据仓库。")
        selected_path = QFileDialog.getExistingDirectory(None, "选择数据存储根目录")

        if selected_path:
            config.save_settings(selected_path)
            try:
                # 此时 FileManager 已经加载完毕，可以使用了
                manager = FileManager()
                if manager.generate_demo_data():
                    QMessageBox.information(None, "准备就绪",
                                            "🎉 已为您自动生成了一个[示例项目]！\n\n包含了典型的 MICP 实验数据（质量记录、应力应变曲线）。\n快去看看吧！")
            except Exception as e:
                print(f"生成演示数据失败: {e}")
            splash.show()
        else:
            sys.exit(0)

    # === 4. 启动主窗口 ===
    window = MainWindow()

    splash.update_progress(100)
    app.processEvents()

    splash.finish(window)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()