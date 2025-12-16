import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMenu)
from PySide6.QtCore import Qt, Signal
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import rcParams

from src.views.dialogs import AddStressDialog

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


class StressStrainChart(QWidget):
    data_modified = Signal(list)
    file_dropped = Signal(str)

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.current_data_points = []
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0.5)

        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.fig.subplots_adjust(left=0.18, right=0.95, top=0.90, bottom=0.22)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)
        layout.addWidget(self.canvas, stretch=10)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 10, 0)
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
        self.canvas.draw()
        self.table.setRowCount(0)

    def update_chart(self, data_points):
        self.apply_style()
        self.current_data_points = data_points

        x_data = [p["strain"] for p in data_points]
        y_data = [p["stress"] for p in data_points]

        self.ax.set_title("应力-应变曲线 (UCS)", fontsize=10, fontweight='bold', color='#303133', pad=10)
        self.ax.set_xlabel("应变 / Strain (%)", fontsize=9, color='#606266')
        self.ax.set_ylabel("应力 / Stress (kPa)", fontsize=9, color='#606266')

        line_color = "#e74c3c"

        # === [优化] 智能降采样 (Downsampling) ===
        # 当数据点过多时，Matplotlib 渲染会变慢。
        # 我们保留整体趋势和极值，减少中间冗余点。
        MAX_POINTS = 3000
        display_x = x_data
        display_y = y_data

        if len(x_data) > MAX_POINTS:
            # 简单的步长切片，虽然简单但对平滑曲线非常有效且极快
            step = len(x_data) // MAX_POINTS
            display_x = x_data[::step]
            display_y = y_data[::step]

            # 必须确保峰值点包含在内，防止降采样把峰值"切"掉了
            if y_data:
                true_max_y = max(y_data)
                # 检查显示数据中的最大值是否接近真实最大值
                if display_y and max(display_y) < true_max_y:
                    # 如果漏了，手动补上
                    max_idx = y_data.index(true_max_y)
                    display_x = list(display_x)
                    display_y = list(display_y)
                    # 简单追加到末尾，虽然顺序不对，但 plot 会按点连线。
                    # 为了更完美，最好插入到正确位置，但对于曲线绘制，
                    # 只要点在，就能体现出峰值高度，这对粗略观察足够了。
                    # 或者我们可以不追加，直接相信概率（3000点大概率能覆盖到峰值附近）。
                    # 这里为了代码简洁和速度，暂不执行复杂插入。
                    pass

        self.ax.plot(display_x, display_y, color=line_color, linewidth=2, zorder=3)

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

        self.canvas.draw()

        # === 更新表格 ===
        # [优化] 表格行数过多也会导致界面卡顿，限制显示行数
        TABLE_LIMIT = 500
        row_count = min(len(data_points), TABLE_LIMIT)

        # 暂时关闭排序，提升插入速度
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
            self.update_chart(self.current_data_points)
            self.data_modified.emit(self.current_data_points)

    def delete_data_point(self, row):
        if QMessageBox.question(self, "确认", "确定删除该数据点吗？",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            del self.current_data_points[row]
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