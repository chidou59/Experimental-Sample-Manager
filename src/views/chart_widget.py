import csv
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFileDialog, QMessageBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import rcParams

# 统一配置字体与负号
rcParams['font.family'] = 'Microsoft YaHei'
rcParams['axes.unicode_minus'] = False
rcParams['font.size'] = 9

# 小按钮样式
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

# === 自定义画布类：忽略滚轮事件 ===
class SilentCanvas(FigureCanvasQTAgg):
    def wheelEvent(self, event):
        # 强制忽略滚轮事件，让它传递给父控件(QScrollArea)
        event.ignore()

class MassTrendChart(QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.current_data_export = []  # 用于存储待导出的数据
        self.current_mode = "mass"  # 当前显示模式

        # 1. 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0.5)

        # 2. 图表层
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        # 调整边距，保证标签显示完整
        self.fig.subplots_adjust(left=0.16, right=0.95, top=0.92, bottom=0.12)

        # 使用自定义的 SilentCanvas
        self.canvas = SilentCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)

        # 3. 按钮工具栏 (右下角)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 5, 10, 5)  # 上右下左
        btn_layout.addStretch()  # 把按钮顶到右边

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

        # 初始化样式
        self.apply_style()

    def wheelEvent(self, event):
        event.ignore()  # 再次确保自身也忽略

    def apply_style(self):
        """应用统一的图表样式"""
        self.ax.clear()
        self.ax.set_facecolor('white')

        # 极简边框
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#dcdfe6')
        self.ax.spines['bottom'].set_color('#dcdfe6')
        self.ax.spines['left'].set_linewidth(1)
        self.ax.spines['bottom'].set_linewidth(1)

        # 虚线网格
        self.ax.grid(True, linestyle=':', alpha=0.6, color='#909399')

        # 【学术化修改】刻度线朝内 (direction='in')
        self.ax.tick_params(axis='both', which='both', direction='in',
                            length=4, width=1, color='#606266', labelcolor='#606266')

    def clear_chart(self):
        self.apply_style()
        self.ax.set_title("暂无数据", color='#909399', pad=10)
        self.ax.set_xlabel("天数", color='#606266')
        self.ax.set_ylabel("数值", color='#606266')
        self.current_data_export = []
        self.canvas.draw()

    def update_chart(self, initial_mass, records, mode="mass"):
        self.apply_style()
        self.current_mode = mode
        self.current_data_export = []  # 清空旧数据

        if initial_mass <= 0: initial_mass = 1

        x_data = [0]
        y_data = []

        # 颜色定义
        color_mass = "#3498db"
        color_rate = "#e67e22"

        if mode == "mass":
            y_data = [initial_mass]
            y_label = "质量 (g)"
            main_color = color_mass
            title = "质量变化趋势"
            # 记录初始点
            self.current_data_export.append({"day": 0, "value": initial_mass})
        else:
            y_data = [0.0]
            y_label = "变化率 (%)"
            main_color = color_rate
            title = "质量变化率趋势"
            self.current_data_export.append({"day": 0, "value": 0.0})

        valid_records = []
        for r in records:
            try:
                d = float(r.get("days"))
                m = float(r.get("mass"))
                valid_records.append((d, m))
            except:
                continue
        valid_records.sort(key=lambda x: x[0])

        for d, m in valid_records:
            x_data.append(d)
            if mode == "mass":
                y_data.append(m)
                self.current_data_export.append({"day": d, "value": m})
            else:
                rate = ((m - initial_mass) / initial_mass) * 100
                y_data.append(rate)
                self.current_data_export.append({"day": d, "value": rate})

        # 绘图
        self.ax.set_title(title, fontsize=10, fontweight='bold', color='#303133', pad=10)
        self.ax.set_xlabel("时间 (天)", fontsize=9, color='#606266')
        self.ax.set_ylabel(y_label, fontsize=9, color='#606266')

        # 曲线
        self.ax.plot(x_data, y_data, color=main_color, linewidth=2,
                     marker='o', markersize=5, markerfacecolor='white', markeredgewidth=1.5,
                     zorder=3)

        # 填充区域
        if len(y_data) > 0:
            fill_base = min(y_data) * 0.999 if mode == "mass" else 0
            self.ax.fill_between(x_data, y_data, fill_base, color=main_color, alpha=0.1, zorder=2)

        self.canvas.draw()

    def export_data(self):
        if not self.current_data_export:
            QMessageBox.warning(self, "无数据", "当前图表没有可导出的数据。")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "导出CSV数据", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    # 根据当前模式写表头
                    unit = "(g)" if self.current_mode == "mass" else "(%)"
                    writer.writerow(["Time (Days)", f"Value {unit}"])
                    for row in self.current_data_export:
                        writer.writerow([row["day"], row["value"]])
                QMessageBox.information(self, "成功", f"数据已导出至:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def export_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "导出图片", "", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if file_path:
            try:
                # 导出 300 DPI 高清图
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"图片已保存:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")