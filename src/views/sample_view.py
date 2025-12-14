import os
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame,
                               QScrollArea, QGridLayout, QMenu, QMessageBox,
                               QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                               QSizePolicy, QComboBox, QFileDialog, QSplitter, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon, QAction, QColor, QFont

from src.views.dialogs import AddWeightDialog, EditSampleDialog, AddStressDialog
from src.views.chart_widget import MassTrendChart
from src.views.stress_chart import StressStrainChart
from src.utils.data_importer import DataImporter

# === 样式常量 (美化版) ===

# 卡片：增加阴影和更柔和的边框
CARD_STYLE = """
    QFrame#ModernCard {
        background-color: white;
        border: 1px solid #ebeef5;
        border-radius: 8px;
    }
    QFrame#ModernCardHeader {
        background-color: #fafafa;
        border-bottom: 1px solid #ebeef5;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
"""

TITLE_STYLE = """
    QLabel { font-size: 13px; font-weight: bold; color: #2c3e50; font-family: "Segoe UI Emoji", "Microsoft YaHei"; }
"""

# 幽灵按钮：增加圆角
BTN_GHOST_STYLE = """
    QPushButton {
        background-color: transparent; border: 1px solid #dcdfe6; 
        color: #606266; border-radius: 6px; padding: 3px 10px; font-size: 11px;
        min-width: 60px;
    }
    QPushButton:hover { border-color: #409eff; color: #409eff; background-color: #ecf5ff; }
"""

# 主按钮：增加渐变质感
BTN_PRIMARY_STYLE = """
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #409eff, stop:1 #3a8ee6);
        border: none; 
        color: white; border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: bold;
        min-width: 70px; 
    }
    QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #66b1ff, stop:1 #409eff); }
    QPushButton:pressed { background-color: #337ecc; }
    QPushButton:disabled { background-color: #a0cfff; }
"""

# 绿色按钮：增加渐变质感
BTN_SUCCESS_STYLE = """
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #67c23a, stop:1 #5daf34);
        border: none; 
        color: white; border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: bold;
        min-width: 70px;
    }
    QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #85ce61, stop:1 #67c23a); }
    QPushButton:pressed { background-color: #529b2e; }
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
        font-family: "Segoe UI Emoji", "Microsoft YaHei";
    }
    QTableWidget::item { padding: 4px; }
    QTableWidget::item:selected { background-color: #ecf5ff; color: #409eff; }
"""

# 右键菜单通用样式（解决黑底问题）
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


# === 1. 统一的卡片容器 (美化版) ===
class ModernCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCard")
        self.setStyleSheet(CARD_STYLE)

        # 可选：添加轻微阴影 (如果卡顿可注释掉)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)

        # 标题栏
        self.header = QFrame()
        self.header.setObjectName("ModernCardHeader")
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(12, 8, 12, 8)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(TITLE_STYLE)
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()

        # 内容区
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(10)

        self.layout_main.addWidget(self.header)
        self.layout_main.addWidget(self.content)

    def add_header_widget(self, widget):
        """向标题栏右侧添加按钮等"""
        self.header_layout.addWidget(widget)


class AttachmentCard(QFrame):
    doubleClicked = Signal()

    def __init__(self, file_data, parent=None):
        super().__init__(parent)
        self.file_data = file_data
        self.setFixedSize(90, 110)
        self.setStyleSheet("""
            AttachmentCard { 
                background: #ffffff; 
                border: 1px solid #ebeef5; 
                border-radius: 8px; 
            }
            AttachmentCard:hover { 
                border-color: #409eff; 
                background: #ecf5ff; 
                margin-top: -2px; /* 悬浮上移微动效 */
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(4)

        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")

        if file_data['type'] == 'image':
            pix = QPixmap(file_data['thumb']).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_lbl.setPixmap(pix)
        else:
            txt = "📄"
            if "xls" in file_data['ext']:
                txt = "📊"
            elif "pdf" in file_data['ext']:
                txt = "📕"
            elif "txt" in file_data['ext']:
                txt = "📝"
            self.icon_lbl.setText(txt)
            self.icon_lbl.setStyleSheet("font-size: 28px; border: none; background: transparent;")

        self.name_lbl = QLabel(file_data['name'])
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setWordWrap(True)
        self.name_lbl.setStyleSheet("color: #606266; font-size: 10px; border: none; background: transparent;")

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.name_lbl)
        layout.addStretch()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


# === 2. 主视图类 ===
class SampleDetailView(QWidget):
    require_refresh = Signal()

    def __init__(self, file_manager):
        super().__init__()
        self.file_manager = file_manager
        self.current_project = None
        self.current_sample = None
        self.current_info = None

        self.setAcceptDrops(True)

        # 整体布局
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #f7f8fa; }")  # 非常淡的灰背景

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: transparent;")

        # 使用 Grid Layout 实现仪表盘布局
        self.main_grid = QGridLayout(self.content_widget)
        # [修改] 减小边距和间距，使布局更紧凑
        self.main_grid.setContentsMargins(10, 10, 10, 10)
        self.main_grid.setSpacing(10)

        self.scroll_area.setWidget(self.content_widget)
        self.outer_layout.addWidget(self.scroll_area)

        # === 初始化各个模块 ===
        self._init_header_section()  # 顶部
        self._init_mass_section()  # 左侧
        self._init_stress_section()  # 右侧
        self._init_gallery_section()  # 底部

        # 布局放置
        # Row 0: Header (span 2 cols)
        self.main_grid.addWidget(self.header_card, 0, 0, 1, 2)

        # Row 1: Mass (Col 0) & Stress (Col 1)
        self.main_grid.addWidget(self.mass_card, 1, 0)
        self.main_grid.addWidget(self.stress_card, 1, 1)

        # Row 2: Gallery (span 2 cols)
        self.main_grid.addWidget(self.gallery_card, 2, 0, 1, 2)

        # 设置列宽比例 1:1
        self.main_grid.setColumnStretch(0, 1)
        self.main_grid.setColumnStretch(1, 1)

        self.show_welcome()

    def _init_header_section(self):
        """顶部：包含基本信息和水平时间轴"""
        self.header_card = ModernCard("📋 试样概览")  # 增加标题Emoji

        # 自定义 Header 内容
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 5, 0, 5)

        # 左侧：图标 + ID + 描述
        self.emoji_label = QLabel("🧪")
        self.emoji_label.setStyleSheet("font-size: 32px; margin-right: 10px;")

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        title_line = QHBoxLayout()
        title_line.setSpacing(8)

        self.title_label = QLabel("未选择试样")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #303133;")

        self.shape_label = QLabel("")
        self.shape_label.setStyleSheet(
            "color: #409eff; font-size: 11px; font-weight: bold; background: #ecf5ff; border-radius: 4px; padding: 1px 6px; border: 1px solid #d9ecff;")

        title_line.addWidget(self.title_label)
        title_line.addWidget(self.shape_label)
        title_line.addStretch()

        self.desc_label = QLabel("暂无描述")
        self.desc_label.setStyleSheet("color: #909399; font-size: 12px;")

        info_layout.addLayout(title_line)
        info_layout.addWidget(self.desc_label)

        h_layout.addWidget(self.emoji_label)
        h_layout.addLayout(info_layout)
        h_layout.addStretch(1)

        # 右侧：时间轴 (Emoji 增强版)
        self.time_container = QWidget()
        time_layout = QHBoxLayout(self.time_container)
        time_layout.setSpacing(6)
        time_layout.setContentsMargins(0, 0, 0, 0)

        # 使用 Emoji 让时间轴更生动
        self.lbl_prep = self._create_mini_time_box("制样", "#909399")
        self.lbl_comp = self._create_mini_time_box("完成", "#3498db")
        self.lbl_demold = self._create_mini_time_box("拆模", "#9b59b6")
        self.lbl_test = self._create_mini_time_box("测试", "#67c23a")

        time_layout.addWidget(self.lbl_prep)
        time_layout.addWidget(self._create_arrow())
        time_layout.addWidget(self.lbl_comp)
        time_layout.addWidget(self._create_arrow())
        time_layout.addWidget(self.lbl_demold)
        time_layout.addWidget(self._create_arrow())
        time_layout.addWidget(self.lbl_test)

        h_layout.addWidget(self.time_container)

        container = QWidget()
        container.setLayout(h_layout)
        self.header_card.content_layout.addWidget(container)

        self.edit_btn = QPushButton("✎ 修改")
        self.edit_btn.setStyleSheet(BTN_GHOST_STYLE)
        self.edit_btn.clicked.connect(self.on_edit_info_click)
        self.header_card.add_header_widget(self.edit_btn)

    def _create_mini_time_box(self, title, color):
        lbl = QLabel(f"{title}\n-")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 11px; font-weight: bold; color: {color}; 
                border: 1px solid {color}; border-radius: 6px; padding: 3px 8px;
                background-color: #ffffff;
                font-family: "Segoe UI Emoji", "Microsoft YaHei";
            }}
        """)
        return lbl

    def _create_arrow(self):
        l = QLabel("›")
        l.setStyleSheet("color: #dcdfe6; font-size: 16px; font-weight: bold; margin-bottom: 2px;")
        return l

    def _init_mass_section(self):
        self.mass_card = ModernCard("📊 质量监控")  # Emoji Title
        # [修改] 减小最小高度，使其更紧凑
        self.mass_card.setMinimumHeight(240)

        self.mass_chart_type = QComboBox()
        self.mass_chart_type.addItems(["质量(g)", "变化率(%)"])
        self.mass_chart_type.setStyleSheet("""
            QComboBox { 
                border: 1px solid #dcdfe6; 
                border-radius: 4px; 
                padding: 2px 4px; 
                font-size: 11px; 
                color: #606266; 
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #dcdfe6;
                selection-background-color: #ecf5ff;
                selection-color: #409eff;
                color: #606266;
                outline: none;
            }
        """)
        self.mass_chart_type.currentIndexChanged.connect(self.update_mass_chart)
        self.mass_card.add_header_widget(self.mass_chart_type)

        self.add_mass_btn = QPushButton("➕ 记录")
        self.add_mass_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        self.add_mass_btn.clicked.connect(self.on_add_weight_click)
        self.mass_card.add_header_widget(self.add_mass_btn)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        self.mass_chart = MassTrendChart(self, width=5, height=3)
        self.mass_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.mass_table = QTableWidget()
        self.mass_table.setColumnCount(4)
        # 表头添加 Emoji
        self.mass_table.setHorizontalHeaderLabels(["日期", "天数", "质量(g)", "变化(%)"])
        self.mass_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mass_table.verticalHeader().setVisible(False)
        self.mass_table.setAlternatingRowColors(True)
        self.mass_table.setStyleSheet(TABLE_STYLE)
        self.mass_table.setSelectionBehavior(QTableWidget.SelectRows)
        # [修改] 减小表格最大高度
        self.mass_table.setMaximumHeight(100)
        self.mass_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mass_table.customContextMenuRequested.connect(self.show_mass_menu)

        layout.addWidget(self.mass_chart, stretch=10)
        layout.addWidget(self.mass_table, stretch=0)

        container = QWidget()
        container.setLayout(layout)
        self.mass_card.content_layout.addWidget(container)

    def _init_stress_section(self):
        self.stress_card = ModernCard("📈 应力应变 (UCS)")  # Emoji Title
        # [修改] 减小最小高度 (之前是400，现在改小以适应一屏显示)
        self.stress_card.setMinimumHeight(320)

        self.add_stress_btn = QPushButton("➕ 记录点")
        self.add_stress_btn.setStyleSheet(BTN_GHOST_STYLE)
        self.add_stress_btn.clicked.connect(self.on_add_stress_click)
        self.stress_card.add_header_widget(self.add_stress_btn)

        self.import_stress_btn = QPushButton("📥 导入")
        self.import_stress_btn.setStyleSheet(BTN_SUCCESS_STYLE)
        self.import_stress_btn.clicked.connect(self.on_import_stress_click)
        self.stress_card.add_header_widget(self.import_stress_btn)

        layout = QVBoxLayout()
        layout.setSpacing(5)

        # 初始化图表
        # [修改] 高度参数从 4 改为 3，与左侧质量图表保持一致，节省垂直空间
        self.stress_chart = StressStrainChart(self, width=5, height=3)
        self.stress_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 【关键修改】连接数据修改信号，实现右键修改/删除后的自动保存
        self.stress_chart.data_modified.connect(
            lambda data: self.file_manager.save_stress_data(self.current_project, self.current_sample, data)
        )

        self.stress_info_lbl = QLabel("💡 提示：支持导入 Excel/CSV 文件或手动添加破坏点。")
        self.stress_info_lbl.setStyleSheet("color: #909399; font-size: 10px; font-style: italic; margin-top: 2px;")

        layout.addWidget(self.stress_chart)
        layout.addWidget(self.stress_info_lbl)

        container = QWidget()
        container.setLayout(layout)
        self.stress_card.content_layout.addWidget(container)

    def _init_gallery_section(self):
        self.gallery_card = ModernCard("🗂️ 附件画廊")  # Emoji Title
        hint = QLabel("支持拖拽上传")
        hint.setStyleSheet("color: #c0c4cc; font-size: 11px;")
        self.gallery_card.add_header_widget(hint)

        self.image_container = QWidget()
        self.image_grid = QGridLayout(self.image_container)
        self.image_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.image_grid.setSpacing(12)  # 附件间距稍微大一点点
        self.image_grid.setContentsMargins(0, 0, 0, 0)

        self.gallery_card.content_layout.addWidget(self.image_container)

    # === 逻辑与数据加载 ===

    def show_welcome(self, message=None):
        self.header_card.hide()
        self.mass_card.hide()
        self.stress_card.hide()
        self.gallery_card.hide()
        self.current_sample = None

    def show_content(self):
        self.header_card.show()
        self.mass_card.show()
        self.stress_card.show()
        self.gallery_card.show()

    def parse_any_date(self, date_str):
        if not date_str or date_str == "-": return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d-%H:00")
        except:
            pass
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            pass
        return None

    def load_sample(self, project_name, sample_id):
        self.show_content()
        self.current_project = project_name
        self.current_sample = sample_id
        info = self.file_manager.get_sample_info(project_name, sample_id)
        self.current_info = info
        if not info: return

        # 1. Header Info
        self.emoji_label.setText(info.get("icon_emoji", "🧪"))
        self.title_label.setText(info.get('id'))
        self.desc_label.setText(info.get('description') or "暂无描述信息")

        # Shape Tag
        shape = info.get("shape", "未指定")
        dims = []
        if "圆柱" in shape:
            dims = [f"r={info.get('radius', 0)}", f"h={info.get('height', 0)}"]
        elif "正方" in shape:
            dims = [f"a={info.get('side_length', 0)}"]
        elif "长方" in shape:
            dims = [f"L={info.get('length', 0)}", f"W={info.get('width', 0)}", f"H={info.get('height', 0)}"]
        if dims:
            self.shape_label.setText(f"{shape} | {', '.join(dims)}")
            self.shape_label.show()
        else:
            self.shape_label.hide()

        # 2. Timeline & Curing Time
        def set_time_box(lbl, val, extra_info=""):
            short = val.replace("-", "/").split(" ")[0] if val != "-" else "-"
            title = lbl.text().splitlines()[0]
            # 保留标题中的 Emoji
            text = f"{title}\n{short}"
            if extra_info:
                text += f"\n{extra_info}"
            lbl.setText(text)

        d_prep_str = info.get('date_prep', '-')
        d_test_str = info.get('date_test', '-')

        # 计算养护时间
        curing_text = ""
        d_prep_obj = self.parse_any_date(d_prep_str)
        d_test_obj = self.parse_any_date(d_test_str)
        if d_prep_obj and d_test_obj:
            delta = d_test_obj - d_prep_obj
            # 使用灰色小字显示养护时间，不喧宾夺主
            curing_text = f"<span style='color:#909399; font-size:10px;'>({delta.days}天)</span>"

        set_time_box(self.lbl_prep, d_prep_str)
        set_time_box(self.lbl_comp, info.get('date_complete', '-'))
        set_time_box(self.lbl_demold, info.get('date_demold', '-'))

        # 将养护时长显示在测试时间节点内 (Label 支持简单的 HTML)
        self.lbl_test.setTextFormat(Qt.RichText)
        set_time_box(self.lbl_test, d_test_str, curing_text)

        # 3. Mass Data
        init_mass = float(info.get("initial_mass", 0))
        records = info.get("weight_records", [])

        self.mass_table.setRowCount(len(records))
        for i, rec in enumerate(records):
            mass = float(rec.get('mass', 0))
            rate_str = "-"
            if init_mass > 0:
                rate = ((mass - init_mass) / init_mass) * 100
                rate_str = f"{rate:+.2f}%"

            date_str = rec.get("date", "-").replace("-", "/").replace(":00", "h")

            self.mass_table.setItem(i, 0, QTableWidgetItem(date_str))

            item_days = QTableWidgetItem(str(rec.get("days", "-")))
            item_days.setTextAlignment(Qt.AlignCenter)
            self.mass_table.setItem(i, 1, item_days)

            item_mass = QTableWidgetItem(f"{mass}")
            item_mass.setTextAlignment(Qt.AlignCenter)
            self.mass_table.setItem(i, 2, item_mass)

            item_rate = QTableWidgetItem(rate_str)
            item_rate.setTextAlignment(Qt.AlignCenter)
            item_rate.setForeground(QColor("#606266"))
            if "-" not in rate_str:
                val = float(rate_str.strip('%'))
                if val > 0:
                    item_rate.setForeground(QColor("#f56c6c"))  # Red
                elif val < 0:
                    item_rate.setForeground(QColor("#67c23a"))  # Green
            self.mass_table.setItem(i, 3, item_rate)

        self.mass_chart_type.setCurrentIndex(0)
        self.update_mass_chart()

        # 4. Stress Data
        stress_data = self.file_manager.get_stress_data(project_name, sample_id)
        if stress_data:
            self.stress_chart.update_chart(stress_data)
        else:
            self.stress_chart.clear_chart()

        # 5. Gallery
        self.refresh_gallery()

    def update_mass_chart(self):
        if not self.current_info: return
        mode = "mass" if self.mass_chart_type.currentIndex() == 0 else "rate"
        init_mass = float(self.current_info.get("initial_mass", 0))
        records = self.current_info.get("weight_records", [])
        self.mass_chart.update_chart(init_mass, records, mode=mode)

    def refresh_gallery(self):
        while self.image_grid.count():
            item = self.image_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        files = self.file_manager.get_sample_files(self.current_project, self.current_sample)
        cols = 6
        for i, f_data in enumerate(files):
            card = AttachmentCard(f_data)
            card.doubleClicked.connect(lambda p=f_data['path']: self.open_file(p))
            card.setContextMenuPolicy(Qt.CustomContextMenu)
            card.customContextMenuRequested.connect(
                lambda pos, c=card, p=f_data['path']: self.show_file_menu(pos, c, p))
            self.image_grid.addWidget(card, i // cols, i % cols)

    # === 事件处理函数 ===

    def on_add_weight_click(self):
        if not self.current_info: return
        dialog = AddWeightDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            d_prep = self.current_info.get("date_prep")
            d1 = self.parse_any_date(d_prep)
            d2 = self.parse_any_date(data["date"])
            days = "-"
            if d1 and d2: days = f"{(d2 - d1).total_seconds() / 86400:.1f}"
            rec = {"date": data["date"], "mass": data["mass"], "days": days}
            self.file_manager.add_weight_record(self.current_project, self.current_sample, rec)
            self.load_sample(self.current_project, self.current_sample)

    def on_edit_info_click(self):
        if not self.current_info: return
        dialog = EditSampleDialog(self.current_info, self)
        if dialog.exec():
            new_data = dialog.get_data()
            self.file_manager.update_sample_info(self.current_project, self.current_sample, new_data)
            self.require_refresh.emit()
            self.load_sample(self.current_project, self.current_sample)

    def on_add_stress_click(self):
        if not self.current_sample: return
        dialog = AddStressDialog(parent=self)
        if dialog.exec():
            new_point = dialog.get_data()
            current_data = self.file_manager.get_stress_data(self.current_project, self.current_sample) or []
            current_data.append(new_point)
            current_data.sort(key=lambda x: x["strain"])
            if self.file_manager.save_stress_data(self.current_project, self.current_sample, current_data):
                self.stress_chart.update_chart(current_data)

    def on_import_stress_click(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "Excel/CSV Files (*.xlsx *.xls *.csv)")
        if file_path:
            data, msg = DataImporter.load_stress_strain_data(file_path)
            if data:
                if self.file_manager.save_stress_data(self.current_project, self.current_sample, data):
                    self.stress_chart.update_chart(data)
                    QMessageBox.information(self, "成功", msg)
                    if QMessageBox.question(self, "备份", "是否将此原文件作为附件保存？",
                                            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                        self.file_manager.add_file_to_sample(self.current_project, self.current_sample, file_path)
                        self.refresh_gallery()
                else:
                    QMessageBox.warning(self, "错误", "数据保存失败")
            else:
                QMessageBox.warning(self, "解析失败", msg)

    def show_mass_menu(self, pos):
        item = self.mass_table.itemAt(pos)
        if not item: return
        row = item.row()
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)  # 应用白色菜单样式
        menu.addAction("✏️ 修改", lambda: self.edit_weight_record(row))
        menu.addAction("🗑️ 删除", lambda: self.delete_weight_record_confirm(row))
        menu.exec(self.mass_table.mapToGlobal(pos))

    def edit_weight_record(self, row):
        if not self.current_info: return
        records = self.current_info.get("weight_records", [])
        if row < 0 or row >= len(records): return
        dialog = AddWeightDialog(current_data=records[row], parent=self)
        if dialog.exec():
            data = dialog.get_data()
            d_prep = self.current_info.get("date_prep")
            d1 = self.parse_any_date(d_prep)
            d2 = self.parse_any_date(data["date"])
            days = "-"
            if d1 and d2: days = f"{(d2 - d1).total_seconds() / 86400:.1f}"
            new_rec = {"date": data["date"], "mass": data["mass"], "days": days}
            if self.file_manager.update_weight_record(self.current_project, self.current_sample, row, new_rec):
                self.load_sample(self.current_project, self.current_sample)

    def delete_weight_record_confirm(self, row):
        if QMessageBox.question(self, "确认", "删除记录？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.file_manager.delete_weight_record(self.current_project, self.current_sample, row)
            self.load_sample(self.current_project, self.current_sample)

    def show_file_menu(self, pos, widget, path):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)  # 应用白色菜单样式
        menu.addAction("👁️ 打开", lambda: self.open_file(path))
        menu.addAction("📂 位置", lambda: self.open_file_location(path))
        menu.addAction("🗑️ 删除", lambda: self.delete_file_confirm(path))
        menu.exec(widget.mapToGlobal(pos))

    def open_file(self, path):
        try:
            os.startfile(path)
        except:
            pass

    def open_file_location(self, path):
        try:
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
        except:
            pass

    def delete_file_confirm(self, path):
        if QMessageBox.question(self, "确认", "删除文件？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.file_manager.delete_file(path)
            self.refresh_gallery()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if not self.current_sample: return
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                self.file_manager.add_file_to_sample(self.current_project, self.current_sample, path)
        self.refresh_gallery()