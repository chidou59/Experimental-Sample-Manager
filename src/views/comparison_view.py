import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib import rcParams

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QTreeWidget, QTreeWidgetItem,
                               QLabel, QSplitter, QFrame, QCheckBox, QComboBox,
                               QHeaderView, QTreeWidgetItemIterator, QSizePolicy, QTextEdit, QPushButton,
                               QApplication, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon

# 配置绘图字体
rcParams['font.family'] = 'Microsoft YaHei'
rcParams['axes.unicode_minus'] = False
rcParams['font.size'] = 9

# 定义一组高对比度的颜色
COLOR_CYCLE = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]


class ComparisonView(QWidget):
    def __init__(self, file_manager, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.selected_samples = {}

        # === 主布局 ===
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #dcdfe6; }")

        # === 1. 左侧：选择列表 ===
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #2c3e50;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("勾选以对比")
        header = self.tree.header()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #34495e;
                color: #bdc3c7;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #2c3e50;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        self.tree.setStyleSheet("""
            QTreeWidget { 
                background-color: #2c3e50; 
                color: #ecf0f1; 
                border: none; 
                padding-top: 10px; 
                font-size: 13px; 
            }
            QTreeWidget::item { 
                height: 35px; 
                padding-left: 5px; 
                border-radius: 4px; 
                margin: 2px 5px; 
            }
            QTreeWidget::item:hover { 
                background-color: #34495e; 
            }
            QTreeWidget::item:selected { 
                background-color: #3498db; 
                color: white; 
            }
            QTreeWidget::indicator {
                width: 16px;
                height: 16px;
            }
        """)

        self.tree.itemChanged.connect(self.on_item_changed)
        left_layout.addWidget(self.tree)

        # === 2. 右侧：图表区域 ===
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #f4f6f9;")

        # 使用 ScrollArea 防止内容过多显示不全
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;")

        charts_container = QWidget()
        charts_layout = QGridLayout(charts_container)
        charts_layout.setContentsMargins(20, 20, 20, 20)
        charts_layout.setSpacing(15)

        card_style = """
            QFrame {
                background-color: white;
                border: 1px solid #dcdfe6;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background-color: transparent;
            }
        """

        # 统一设置图表内容的最小高度
        UNIFIED_MIN_HEIGHT = 300

        # --- 1. 左上：质量图卡片 ---
        mass_card = QFrame()
        mass_card.setStyleSheet(card_style)
        mass_layout = QVBoxLayout(mass_card)
        mass_layout.setContentsMargins(15, 15, 15, 15)
        mass_layout.setSpacing(5)

        lbl1 = QLabel("📊 质量变化对比")
        lbl1.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 15px;")
        lbl1.setAlignment(Qt.AlignCenter)

        self.mass_fig = Figure(figsize=(4, 3), dpi=100, facecolor='white')
        self.mass_fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.20)

        self.mass_canvas = FigureCanvasQTAgg(self.mass_fig)
        self.mass_canvas.wheelEvent = lambda event: event.ignore()  # ✨ 修复滚动
        self.mass_ax = self.mass_fig.add_subplot(111)
        self.mass_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mass_canvas.setMinimumHeight(UNIFIED_MIN_HEIGHT)

        mass_layout.addWidget(lbl1)
        mass_layout.addWidget(self.mass_canvas)

        # --- 2. 右上：应力应变图卡片 ---
        stress_card = QFrame()
        stress_card.setStyleSheet(card_style)
        stress_layout = QVBoxLayout(stress_card)
        stress_layout.setContentsMargins(15, 15, 15, 15)
        stress_layout.setSpacing(5)

        lbl2 = QLabel("📈 应力应变对比")
        lbl2.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 15px;")
        lbl2.setAlignment(Qt.AlignCenter)

        self.stress_fig = Figure(figsize=(4, 3), dpi=100, facecolor='white')
        self.stress_fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.20)

        self.stress_canvas = FigureCanvasQTAgg(self.stress_fig)
        self.stress_canvas.wheelEvent = lambda event: event.ignore()  # ✨ 修复滚动
        self.stress_ax = self.stress_fig.add_subplot(111)
        self.stress_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stress_canvas.setMinimumHeight(UNIFIED_MIN_HEIGHT)

        stress_layout.addWidget(lbl2)
        stress_layout.addWidget(self.stress_canvas)

        # --- 3. 左下：关键变量趋势图卡片 ---
        var_card = QFrame()
        var_card.setStyleSheet(card_style)
        var_layout = QVBoxLayout(var_card)
        var_layout.setContentsMargins(15, 15, 15, 15)
        var_layout.setSpacing(5)

        # 【修改】将 Label 变为成员变量，以便动态修改文本
        self.var_chart_title = QLabel("📐 关键变量对峰值应力的影响")
        self.var_chart_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 15px;")
        self.var_chart_title.setAlignment(Qt.AlignCenter)

        self.var_fig = Figure(figsize=(4, 3), dpi=100, facecolor='white')
        self.var_fig.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.20)

        self.var_canvas = FigureCanvasQTAgg(self.var_fig)
        self.var_canvas.wheelEvent = lambda event: event.ignore()  # ✨ 修复滚动
        self.var_ax = self.var_fig.add_subplot(111)
        self.var_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.var_canvas.setMinimumHeight(UNIFIED_MIN_HEIGHT)

        var_layout.addWidget(self.var_chart_title)
        var_layout.addWidget(self.var_canvas)

        # --- 4. 右下：AI 分析卡片 ---
        ai_card = QFrame()
        ai_card.setStyleSheet(card_style)
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setContentsMargins(15, 15, 15, 15)
        ai_layout.setSpacing(10)

        ai_header = QHBoxLayout()
        ai_lbl = QLabel("🤖 AI分析提示词生成器")
        ai_lbl.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 15px;")

        ai_hint = QLabel("将提示词发给AI进行分析吧")
        ai_hint.setStyleSheet("color: #909399; font-size: 12px; font-style: italic;")

        self.btn_copy_ai = QPushButton("📋 复制")
        self.btn_copy_ai.setCursor(Qt.PointingHandCursor)
        self.btn_copy_ai.setStyleSheet("""
            QPushButton { 
                background-color: #ecf5ff; color: #409eff; border: 1px solid #b3d8ff; 
                border-radius: 4px; padding: 4px 10px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #409eff; color: white; }
        """)
        self.btn_copy_ai.clicked.connect(self.copy_ai_prompt)

        ai_header.addWidget(ai_lbl)
        ai_header.addWidget(ai_hint)
        ai_header.addStretch()
        ai_header.addWidget(self.btn_copy_ai)

        self.ai_text_edit = QTextEdit()
        self.ai_text_edit.setReadOnly(True)
        self.ai_text_edit.setPlaceholderText(
            "勾选试样后这里会自动生成提示词，复制给AI看看吧~")
        self.ai_text_edit.setStyleSheet("""
            QTextEdit { 
                background-color: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; 
                color: #555; font-family: "Microsoft YaHei"; font-size: 12px; padding: 8px;
            }
        """)
        self.ai_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ai_text_edit.setMinimumHeight(UNIFIED_MIN_HEIGHT - 40)

        ai_layout.addLayout(ai_header)
        ai_layout.addWidget(self.ai_text_edit)

        # --- Grid 布局 ---
        # Row 0
        charts_layout.addWidget(mass_card, 0, 0)
        charts_layout.addWidget(stress_card, 0, 1)
        # Row 1
        charts_layout.addWidget(var_card, 1, 0)
        charts_layout.addWidget(ai_card, 1, 1)

        charts_layout.setRowStretch(0, 1)
        charts_layout.setRowStretch(1, 1)
        charts_layout.setColumnStretch(0, 1)
        charts_layout.setColumnStretch(1, 1)

        scroll_area.setWidget(charts_container)

        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(scroll_area)
        self.splitter.setSizes([220, 980])

        layout.addWidget(self.splitter)
        self.reset_charts()

    def refresh_tree(self):
        """重新加载左侧的试样树"""
        self.tree.clear()
        self.tree.blockSignals(True)

        structure = self.file_manager.get_project_structure()

        for project_name, samples in structure.items():
            p_item = QTreeWidgetItem(self.tree)
            p_item.setText(0, project_name)
            p_item.setFlags(p_item.flags() | Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable)
            p_item.setCheckState(0, Qt.Unchecked)
            p_item.setExpanded(True)

            for sample_id in samples:
                s_item = QTreeWidgetItem(p_item)
                s_item.setText(0, sample_id)
                s_item.setData(0, Qt.UserRole, f"{project_name}/{sample_id}")
                s_item.setFlags(s_item.flags() | Qt.ItemIsUserCheckable)
                s_item.setCheckState(0, Qt.Unchecked)

        self.tree.blockSignals(False)

    def on_item_changed(self, item, column):
        self.update_charts()

    def copy_ai_prompt(self):
        text = self.ai_text_edit.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.btn_copy_ai.setText("已复制! ✅")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.btn_copy_ai.setText("📋 复制"))

    def update_charts(self):
        self.reset_charts()

        checked_samples = []
        iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.Checked)
        while iterator.value():
            item = iterator.value()
            unique_id = item.data(0, Qt.UserRole)
            if unique_id:
                project_name, sample_id = unique_id.split('/')
                checked_samples.append((project_name, sample_id))
            iterator += 1

        if not checked_samples:
            self.mass_canvas.draw()
            self.stress_canvas.draw()
            self.var_canvas.draw()
            self.ai_text_edit.clear()
            self.var_chart_title.setText("📐 关键变量对峰值应力的影响")  # 重置标题
            return

        trend_data = []
        ai_prompt = "我正在进行一组材料/试样性能对比实验。以下是整理好的数据，包含配方差异、关键变量以及对应的实验结果（质量变化率和峰值应力）。请帮我分析这些变量对试样性能的影响规律，并尝试推测背后的科学机制：\n\n"

        # 记录第一个被选中的试样的变量名称，用于更新图表标题
        current_key_var_name = "关键变量"

        for i, (p_name, s_id) in enumerate(checked_samples):
            color = COLOR_CYCLE[i % len(COLOR_CYCLE)]
            label = f"{s_id}"

            # 读取信息
            info = self.file_manager.get_sample_info(p_name, s_id)
            if not info: continue

            init_mass = float(info.get("initial_mass", 0))
            records = info.get("weight_records", [])
            key_var = float(info.get("key_variable", 0))
            key_var_name = info.get("key_variable_name", "关键变量")
            recipe = info.get("recipe", "无配方")

            # 获取第一个试样的变量名
            if i == 0:
                current_key_var_name = key_var_name

            # --- 1. 处理质量数据 ---
            x_data = []
            y_data = []
            final_mass_rate = 0.0

            if init_mass > 0:
                x_data.append(0)
                y_data.append(0)
                for r in records:
                    try:
                        day = float(r.get("days", 0))
                        mass = float(r.get("mass", 0))
                        rate = ((mass - init_mass) / init_mass) * 100
                        x_data.append(day)
                        y_data.append(rate)
                        final_mass_rate = rate
                    except:
                        continue

                combined = sorted(zip(x_data, y_data))
                if combined:
                    x_data, y_data = zip(*combined)
                    self.mass_ax.plot(x_data, y_data, marker='o', markersize=4,
                                      linewidth=2, color=color, label=label)

            # --- 2. 处理应力应变 & 计算峰值 ---
            stress_data = self.file_manager.get_stress_data(p_name, s_id)
            peak_stress_val = 0.0

            if stress_data:
                sx = [p['strain'] for p in stress_data]
                sy = [p['stress'] for p in stress_data]
                self.stress_ax.plot(sx, sy, linewidth=2, color=color, label=label)

                if len(sy) > 0:
                    peak_stress_val = max(sy)
                    trend_data.append((key_var, peak_stress_val, label, color))

            # --- 3. 添加到 AI Prompt ---
            ai_prompt += f"【试样 {label}】\n"
            ai_prompt += f"- 配方描述: {recipe}\n"
            ai_prompt += f"- {key_var_name}: {key_var}\n"
            ai_prompt += f"- 最终质量增加率: {final_mass_rate:.2f}%\n"
            ai_prompt += f"- 峰值应力 (UCS): {peak_stress_val:.2f} kPa\n\n"

        # --- 绘制变量趋势图 ---
        # 【修改】动态更新标题和横坐标标签
        self.var_chart_title.setText(f"📐 {current_key_var_name}对峰值应力的影响")
        self.var_ax.set_xlabel(current_key_var_name, fontsize=8)

        if trend_data:
            trend_data.sort(key=lambda x: x[0])
            tx = [item[0] for item in trend_data]
            ty = [item[1] for item in trend_data]

            self.var_ax.plot(tx, ty, color='#999999', linestyle='--', linewidth=1.5, zorder=1)
            for k_var, p_stress, s_label, s_color in trend_data:
                self.var_ax.scatter(k_var, p_stress, color=s_color, s=60, zorder=2, label=s_label)

        # 刷新图例
        if checked_samples:
            self.mass_ax.legend(frameon=False, fontsize=8)
            self.stress_ax.legend(frameon=False, fontsize=8)
            self.var_ax.legend(frameon=False, fontsize=8)

        self.mass_canvas.draw()
        self.stress_canvas.draw()
        self.var_canvas.draw()

        self.ai_text_edit.setPlainText(ai_prompt)

    def reset_charts(self):
        """重置画布背景和坐标轴"""
        for ax in [self.mass_ax, self.stress_ax, self.var_ax]:
            ax.clear()
            ax.set_facecolor('white')
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(direction='in')

        self.mass_ax.set_xlabel("时间 (天)", fontsize=8)
        self.mass_ax.set_ylabel("质量变化率 (%)", fontsize=8)

        self.stress_ax.set_xlabel("应变 (%)", fontsize=8)
        self.stress_ax.set_ylabel("应力 (kPa)", fontsize=8)

        # 默认标题
        self.var_ax.set_xlabel("关键变量", fontsize=8)
        self.var_ax.set_ylabel("峰值应力 (kPa)", fontsize=8)