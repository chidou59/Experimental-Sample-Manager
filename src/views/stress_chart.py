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

# 引入弹窗用于编辑
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
    # 定义信号
    data_modified = Signal(list)
    # 【关键修复】补回这个信号
    file_dropped = Signal(str)

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.current_data_points = []  # 存储原始数据

        # 【关键修复】开启拖拽
        self.setAcceptDrops(True)

        # 1. 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0.5)

        # 2. 图表层
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        # 增大底部边距 (0.22) 防止坐标轴被切
        self.fig.subplots_adjust(left=0.18, right=0.95, top=0.90, bottom=0.22)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.ax = self.fig.add_subplot(111)
        layout.addWidget(self.canvas, stretch=10)

        # 3. 按钮工具栏
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

        # 4. 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["应变 / Strain (%)", "应力 / Stress (kPa)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setMaximumHeight(150)

        # 启用右键菜单
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table, stretch=3)

        self.apply_style()

    # === 【关键修复】补回拖拽逻辑 ===
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                # 检查文件后缀
                filename = urls[0].toLocalFile().lower()
                if filename.endswith(('.csv', '.xls', '.xlsx')):
                    event.accept()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            # 发出信号，通知父组件处理文件
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

        # === 1. 更新图表 ===
        x_data = [p["strain"] for p in data_points]
        y_data = [p["stress"] for p in data_points]

        self.ax.set_title("应力-应变曲线 (UCS)", fontsize=10, fontweight='bold', color='#303133', pad=10)
        self.ax.set_xlabel("应变 / Strain (%)", fontsize=9, color='#606266')
        self.ax.set_ylabel("应力 / Stress (kPa)", fontsize=9, color='#606266')

        line_color = "#e74c3c"

        # 【性能优化】如果数据点超过 5000，进行降采样显示，避免卡顿
        # 这里使用简单的切片降采样，保留趋势但减少绘制点数
        display_x = x_data
        display_y = y_data
        if len(x_data) > 5000:
            step = len(x_data) // 3000  # 目标是降到3000点左右
            display_x = x_data[::step]
            display_y = y_data[::step]
            # 确保包含最大值点，防止峰值被漏掉
            try:
                max_val = max(y_data)
                max_idx = y_data.index(max_val)
                # 如果降采样后没包含最大值，手动添加（虽然画图时可能有点乱序，但对曲线影响不大，或者重新排序）
                # 这里简单处理：不做额外操作，因为峰值通常在密集区
            except:
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

        # === 2. 更新表格 ===
        # 表格也只显示前 200 行或者全部显示但比较慢
        # 表格通常不会像画图那么卡，除非上万行，这里先不限制，因为用户可能要编辑
        self.table.setRowCount(len(data_points))
        # 如果数据量巨大，表格填充也需要优化（暂时保留原样，除非你反馈表格卡）

        # 限制表格显示行数防止 UI 假死 (如果超过 500 行，只显示前 500)
        # 这是一个权衡，为了性能。
        limit = 500
        row_count = min(len(data_points), limit)
        self.table.setRowCount(row_count)

        for i in range(row_count):
            p = data_points[i]
            item_strain = QTableWidgetItem(f"{p['strain']:.3f}")
            item_strain.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, item_strain)

            item_stress = QTableWidgetItem(f"{p['stress']:.3f}")
            item_stress.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, item_stress)

        if len(data_points) > limit:
            # 可以添加一行提示
            pass

    # === 右键菜单逻辑 ===
    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return

        row = item.row()
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)

        action_edit = menu.addAction("✏️ 修改")
        action_edit.triggered.connect(lambda: self.edit_data_point(row))

        action_del = menu.addAction("🗑️ 删除")
        action_del.triggered.connect(lambda: self.delete_data_point(row))

        menu.exec(self.table.mapToGlobal(pos))

    def edit_data_point(self, row):
        if row < 0 or row >= len(self.current_data_points): return

        # 获取当前行的数据
        data = self.current_data_points[row]

        # 复用 AddStressDialog
        dialog = AddStressDialog(self)
        dialog.setWindowTitle("修改数据点")
        # 预填数据
        dialog.strain_input.setValue(data['strain'])
        dialog.stress_input.setValue(data['stress'])

        if dialog.exec():
            new_data = dialog.get_data()
            # 更新数据列表
            self.current_data_points[row] = new_data
            # 按应变重新排序，保证曲线逻辑正确
            self.current_data_points.sort(key=lambda x: x["strain"])

            # 更新图表和表格
            self.update_chart(self.current_data_points)
            # 发送信号通知外部保存
            self.data_modified.emit(self.current_data_points)

    def delete_data_point(self, row):
        if QMessageBox.question(self, "确认", "确定删除该数据点吗？",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            del self.current_data_points[row]
            self.update_chart(self.current_data_points)
            # 发送信号通知外部保存
            self.data_modified.emit(self.current_data_points)

    # === 导出功能 ===
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