import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMenu, QDialog, QLabel, QGridLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import rcParams

from src.views.dialogs import AddStressDialog
# 引入新写的分析模块
from src.utils.mechanical_analysis import MechanicalAnalyzer

rcParams['font.family'] = 'Microsoft YaHei'
rcParams['axes.unicode_minus'] = False
rcParams['font.size'] = 9

# === 样式定义 ===
BTN_STYLE = """
    QPushButton {
        background-color: white;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #606266;
    }
    QPushButton:hover {
        border-color: #409eff;
        color: #409eff;
        background-color: #ecf5ff;
    }
"""

BTN_ANALYZE_STYLE = """
    QPushButton {
        background-color: #e6f7ff;
        border: 1px solid #91d5ff;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #1890ff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1890ff;
        color: white;
    }
"""

BTN_RESET_STYLE = """
    QPushButton {
        background-color: #fff0f0;
        border: 1px solid #ffccc7;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        color: #ff4d4f;
    }
    QPushButton:hover {
        background-color: #ff4d4f;
        color: white;
    }
"""

TABLE_STYLE = """
    QTableWidget {
        background-color: white;
        border: 1px solid #ebeef5;
        border-radius: 6px;
        gridline-color: #f2f6fc;
        font-size: 11px;
    }
    QHeaderView::section {
        background-color: #fafafe;
        color: #555;
        padding: 6px;
        border: none;
        border-bottom: 2px solid #e4e7ed;
        font-weight: bold;
        font-family: "Microsoft YaHei";
    }
    QTableWidget::item { padding: 4px; }
    QTableWidget::item:selected { background-color: #ecf5ff; color: #409eff; }

    QScrollBar:vertical {
        border: none;
        background: #f4f6f9;
        width: 6px;
    }
    QScrollBar::handle:vertical {
        background: #c0c4cc;
        border-radius: 3px;
    }
"""

MENU_STYLE = """
    QMenu {
        background-color: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 4px;
        padding: 4px 0px;
    }
    QMenu::item {
        background-color: transparent;
        color: #333333;
        padding: 6px 20px;
        margin: 2px 4px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #ecf5ff;
        color: #409eff;
    }
    QMenu::separator {
        height: 1px;
        background: #f0f0f0;
        margin: 4px 0px;
    }
"""


class AnalysisResultDialog(QDialog):
    """显示分析结果的漂亮弹窗"""

    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 力学性能智能分析报告")
        self.resize(350, 300)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("特征参数计算结果")
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #303133; border-bottom: 2px solid #3498db; padding-bottom: 5px;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(15)

        def add_row(row, label_text, value_text, unit_text, desc_text=""):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #606266; font-weight: bold;")
            val = QLabel(value_text)
            val.setStyleSheet("color: #303133; font-size: 14px; font-weight: bold;")
            unit = QLabel(unit_text)
            unit.setStyleSheet("color: #909399; font-size: 12px;")

            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)
            grid.addWidget(unit, row, 2)

            if desc_text:
                desc = QLabel(desc_text)
                desc.setStyleSheet("color: #909399; font-size: 10px; font-style: italic;")
                grid.addWidget(desc, row + 1, 0, 1, 3)
                return row + 2
            return row + 1

        r = 0
        r = add_row(r, "弹性模量 (E):", f"{results['elastic_modulus']:.2f}", "MPa", "基于峰值前30%-70%线性拟合")
        r = add_row(r, "峰值强度 (UCS):", f"{results['peak_stress']:.2f}", "kPa", "")
        r = add_row(r, "峰值应变:", f"{results['peak_strain']:.2f}", "%", "")
        r = add_row(r, "残余强度:", f"{results['residual_stress']:.2f}", "kPa", "")
        r = add_row(r, "韧性 (Toughness):", f"{results['toughness']:.2f}", "kJ/m³", "应力-应变曲线下的能量积分")

        layout.addLayout(grid)
        layout.addStretch()

        btn_ok = QPushButton("确定")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(
            "background-color: #3498db; color: white; border-radius: 5px; padding: 6px 15px; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok, alignment=Qt.AlignRight)


class StressStrainChart(QWidget):
    data_modified = Signal(list)
    file_dropped = Signal(str)

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.current_data_points = []
        # 用于存储分析后的拟合线，以便在重绘时画出来
        self.current_fit_line = None

        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0.5)

        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.fig.subplots_adjust(left=0.18, right=0.95, top=0.90, bottom=0.22)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)
        layout.addWidget(self.canvas, stretch=10)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 10, 0)

        # 新增分析按钮放在左侧
        self.btn_analyze = QPushButton("🧠 智能分析")
        self.btn_analyze.setStyleSheet(BTN_ANALYZE_STYLE)
        self.btn_analyze.setCursor(Qt.PointingHandCursor)
        self.btn_analyze.setToolTip("自动计算弹性模量、韧性及特征强度")
        self.btn_analyze.clicked.connect(self.run_mechanical_analysis)
        btn_layout.addWidget(self.btn_analyze)

        # === 新增：重置按钮 ===
        self.btn_reset_analysis = QPushButton("↺")
        self.btn_reset_analysis.setToolTip("清除分析结果 (拟合线)")
        self.btn_reset_analysis.setStyleSheet(BTN_RESET_STYLE)
        self.btn_reset_analysis.setCursor(Qt.PointingHandCursor)
        self.btn_reset_analysis.setFixedWidth(30)
        self.btn_reset_analysis.clicked.connect(self.clear_analysis_line)
        # 默认隐藏，有分析结果才显示
        self.btn_reset_analysis.hide()
        btn_layout.addWidget(self.btn_reset_analysis)

        btn_layout.addStretch()

        self.btn_export_data = QPushButton("📊 导出数据")
        self.btn_export_data.setStyleSheet(BTN_STYLE)
        self.btn_export_data.setCursor(Qt.PointingHandCursor)
        self.btn_export_data.clicked.connect(self.export_data)

        self.btn_export_img = QPushButton("🖼️ 导出高清图像")
        self.btn_export_img.setStyleSheet(BTN_STYLE)
        self.btn_export_img.setCursor(Qt.PointingHandCursor)
        self.btn_export_img.clicked.connect(self.export_image)

        btn_layout.addWidget(self.btn_export_data)
        btn_layout.addWidget(self.btn_export_img)

        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["应变 / Strain (%)", "应力 / Stress (kPa)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setMaximumHeight(150)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table, stretch=3)
        self.apply_style()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                filename = urls[0].toLocalFile().lower()
                if filename.endswith(('.csv', '.xls', '.xlsx')):
                    event.accept()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.file_dropped.emit(path)

    def wheelEvent(self, event):
        if self.table.underMouse():
            super().wheelEvent(event)
        else:
            event.ignore()

    def apply_style(self):
        self.ax.clear()
        self.ax.set_facecolor('white')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#dcdfe6')
        self.ax.spines['bottom'].set_color('#dcdfe6')
        self.ax.grid(True, linestyle=':', alpha=0.6, color='#909399')
        self.ax.tick_params(axis='both', which='both', direction='in',
                            length=4, width=1, color='#606266', labelcolor='#606266')

    def clear_chart(self):
        self.apply_style()
        self.ax.set_title("暂无 UCS 数据", color='#909399', pad=10)
        self.ax.set_xlabel("应变 (%)", color='#606266')
        self.ax.set_ylabel("应力 (kPa)", color='#606266')
        self.current_data_points = []
        self.current_fit_line = None  # 清空拟合线
        self.btn_reset_analysis.hide()  # 隐藏重置按钮
        self.canvas.draw()
        self.table.setRowCount(0)

    # === 关键修改：增加 keep_analysis 参数 ===
    def update_chart(self, data_points, keep_analysis=False):
        """
        更新图表。
        :param data_points: 新的数据点列表
        :param keep_analysis: 是否保留当前的分析拟合线。
                              默认为 False，即每次更新数据（如切换试样）都会自动清除旧的分析结果。
        """
        self.apply_style()
        self.current_data_points = data_points

        # 如果不保留分析，则清除拟合线并隐藏按钮
        if not keep_analysis:
            self.current_fit_line = None
            self.btn_reset_analysis.hide()

        x_data = [p["strain"] for p in data_points]
        y_data = [p["stress"] for p in data_points]

        self.ax.set_title("应力-应变曲线 (UCS)", fontsize=10, fontweight='bold', color='#303133', pad=10)
        self.ax.set_xlabel("应变 / Strain (%)", fontsize=9, color='#606266')
        self.ax.set_ylabel("应力 / Stress (kPa)", fontsize=9, color='#606266')

        line_color = "#e74c3c"

        # 降采样逻辑
        MAX_POINTS = 3000
        display_x = x_data
        display_y = y_data

        if len(x_data) > MAX_POINTS:
            step = len(x_data) // MAX_POINTS
            display_x = x_data[::step]
            display_y = y_data[::step]

        self.ax.plot(display_x, display_y, color=line_color, linewidth=2, zorder=3, label="试验曲线")

        # === 绘制峰值点 ===
        if y_data:
            max_y = max(y_data)
            max_index = y_data.index(max_y)
            max_x = x_data[max_index]

            self.ax.plot(max_x, max_y, 'o', color='#c0392b', markersize=6, zorder=4)

            info_text = (
                f"峰值应力: {max_y:.2f} kPa\n"
                f"峰值应变: {max_x:.2f} %"
            )
            self.ax.text(0.96, 0.04, info_text,
                         transform=self.ax.transAxes,
                         horizontalalignment='right',
                         verticalalignment='bottom',
                         fontsize=9,
                         color='#303133',
                         bbox=dict(boxstyle="round,pad=0.5", facecolor='white', edgecolor='#dcdfe6', alpha=0.9))

        # === 绘制拟合直线 (如果存在) ===
        if self.current_fit_line:
            fit_x = [p[0] for p in self.current_fit_line]
            fit_y = [p[1] for p in self.current_fit_line]
            self.ax.plot(fit_x, fit_y, color='#1890ff', linestyle='--', linewidth=1.5, zorder=3, label="弹性阶段拟合")
            self.ax.legend(loc='upper right', frameon=False, fontsize=8)
            # 有分析结果时，显示重置按钮
            self.btn_reset_analysis.show()

        self.canvas.draw()

        # === 更新表格 ===
        TABLE_LIMIT = 500
        row_count = min(len(data_points), TABLE_LIMIT)

        self.table.setSortingEnabled(False)
        self.table.setRowCount(row_count)

        for i in range(row_count):
            p = data_points[i]
            item_strain = QTableWidgetItem(f"{p['strain']:.3f}")
            item_strain.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, item_strain)

            item_stress = QTableWidgetItem(f"{p['stress']:.3f}")
            item_stress.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, item_stress)

        self.table.setSortingEnabled(True)

    def run_mechanical_analysis(self):
        """执行智能分析逻辑"""
        if not self.current_data_points:
            QMessageBox.warning(self, "无数据", "请先导入或录入应力应变数据。")
            return

        # 调用分析工具
        result = MechanicalAnalyzer.analyze(self.current_data_points)

        if not result["success"]:
            QMessageBox.warning(self, "分析失败", result["msg"])
            return

        # 保存拟合线以便绘图
        self.current_fit_line = result["fit_line"]

        # 刷新图表 (强制保留分析结果)
        self.update_chart(self.current_data_points, keep_analysis=True)

        # 弹窗显示详细结果
        dialog = AnalysisResultDialog(result, self)
        dialog.exec()

    def clear_analysis_line(self):
        """手动清除分析结果"""
        self.current_fit_line = None
        # 刷新图表 (keep_analysis默认为False，会自动隐藏按钮)
        self.update_chart(self.current_data_points)

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        row = item.row()
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        menu.addAction("✏️ 修改", lambda: self.edit_data_point(row))
        menu.addAction("🗑️ 删除", lambda: self.delete_data_point(row))
        menu.exec(self.table.mapToGlobal(pos))

    def edit_data_point(self, row):
        if row < 0 or row >= len(self.current_data_points): return
        data = self.current_data_points[row]
        dialog = AddStressDialog(self)
        dialog.setWindowTitle("修改数据点")
        dialog.strain_input.setValue(data['strain'])
        dialog.stress_input.setValue(data['stress'])

        if dialog.exec():
            new_data = dialog.get_data()
            self.current_data_points[row] = new_data
            self.current_data_points.sort(key=lambda x: x["strain"])

            # 修改数据后，数据变了，旧分析失效，所以默认 update_chart 就会清除它
            self.update_chart(self.current_data_points)
            self.data_modified.emit(self.current_data_points)

    def delete_data_point(self, row):
        if QMessageBox.question(self, "确认", "确定删除该数据点吗？",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            del self.current_data_points[row]
            # 数据变了，旧分析失效
            self.update_chart(self.current_data_points)
            self.data_modified.emit(self.current_data_points)

    def export_data(self):
        if not self.current_data_points:
            QMessageBox.warning(self, "无数据", "当前没有应力应变数据可导出。")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "导出UCS数据", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Strain (%)", "Stress (kPa)"])
                    for p in self.current_data_points:
                        writer.writerow([p["strain"], p["stress"]])
                QMessageBox.information(self, "成功", f"数据已导出至:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def export_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出图片", "", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if file_path:
            try:
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"图片已保存:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")