import os
import subprocess
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame,
                               QScrollArea, QGridLayout, QMenu, QMessageBox,
                               QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                               QSizePolicy, QComboBox, QFileDialog, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor

from src.views.dialogs import AddWeightDialog, EditSampleDialog, AddStressDialog
from src.views.chart_widget import MassTrendChart
from src.views.stress_chart import StressStrainChart
from src.utils.data_importer import DataImporter
from src.utils.template_manager import TemplateManager

# === 样式常量 ===
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
BTN_GHOST_STYLE = """
    QPushButton {
        background-color: transparent; border: 1px solid #dcdfe6; 
        color: #606266; border-radius: 6px; padding: 3px 10px; font-size: 11px;
        min-width: 60px;
    }
    QPushButton:hover { border-color: #409eff; color: #409eff; background-color: #ecf5ff; }
"""
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


class ModernCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCard")
        self.setStyleSheet(CARD_STYLE)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15);
        shadow.setColor(QColor(0, 0, 0, 10));
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0);
        self.layout_main.setSpacing(0)
        self.header = QFrame();
        self.header.setObjectName("ModernCardHeader")
        self.header_layout = QHBoxLayout(self.header);
        self.header_layout.setContentsMargins(12, 8, 12, 8)
        self.lbl_title = QLabel(title);
        self.lbl_title.setStyleSheet(TITLE_STYLE)
        self.header_layout.addWidget(self.lbl_title);
        self.header_layout.addStretch()
        self.content = QWidget();
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12);
        self.content_layout.setSpacing(10)
        self.layout_main.addWidget(self.header);
        self.layout_main.addWidget(self.content)

    def add_header_widget(self, widget):
        self.header_layout.addWidget(widget)


class AttachmentCard(QFrame):
    doubleClicked = Signal()

    def __init__(self, file_data, parent=None):
        super().__init__(parent)
        self.setFixedSize(90, 110)
        self.setStyleSheet(
            "AttachmentCard { background: #ffffff; border: 1px solid #ebeef5; border-radius: 8px; } AttachmentCard:hover { border-color: #409eff; background: #ecf5ff; margin-top: -2px; }")
        layout = QVBoxLayout(self);
        layout.setContentsMargins(4, 8, 4, 4);
        layout.setSpacing(4)
        self.icon_lbl = QLabel();
        self.icon_lbl.setAlignment(Qt.AlignCenter);
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        if file_data['type'] == 'image':
            pix = QPixmap(file_data['thumb'])
            if not pix.isNull():
                pix = pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation); self.icon_lbl.setPixmap(pix)
            else:
                self.icon_lbl.setText("🖼️"); self.icon_lbl.setStyleSheet(
                    "font-size: 28px; border: none; background: transparent;")
        else:
            self.icon_lbl.setText("📄");
            self.icon_lbl.setStyleSheet("font-size: 28px; border: none; background: transparent;")
        self.name_lbl = QLabel(file_data['name']);
        self.name_lbl.setAlignment(Qt.AlignCenter);
        self.name_lbl.setWordWrap(True)
        self.name_lbl.setStyleSheet("color: #606266; font-size: 10px; border: none; background: transparent;")
        layout.addWidget(self.icon_lbl);
        layout.addWidget(self.name_lbl);
        layout.addStretch()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton: self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class SampleDetailView(QWidget):
    require_refresh = Signal()

    def __init__(self, file_manager):
        super().__init__()
        self.file_manager = file_manager
        self.current_project = None
        self.current_sample = None
        self.current_info = None
        self.setAcceptDrops(True)

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; }")

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: transparent;")

        # Grid 布局
        self.main_layout = QGridLayout(self.content_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)
        # 列宽均分 (两列)
        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        # 顶部对齐
        self.main_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.content_widget)
        self.outer_layout.addWidget(self.scroll_area)

        # 初始化模块
        self._init_header_section()
        self._init_mass_section()
        self._init_stress_section()
        self._init_gallery_section()
        self._init_welcome_section()

        self.outer_layout.addWidget(self.welcome_container)

        self.show_welcome()

    def _init_header_section(self):
        self.header_card = ModernCard("📋 试样概览")
        h_layout = QHBoxLayout();
        h_layout.setContentsMargins(0, 5, 0, 5)
        self.emoji_label = QLabel("🧪");
        self.emoji_label.setStyleSheet("font-size: 32px; margin-right: 10px;")

        # 1. 信息区：标题 + 尺寸 + 动态属性 + 备注
        info_layout = QVBoxLayout();
        info_layout.setSpacing(4)

        # 第一行：标题 + 形状/尺寸 Label
        title_line = QHBoxLayout();
        title_line.setSpacing(8)
        self.title_label = QLabel("未选择");
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #303133;")
        self.shape_label = QLabel("");
        self.shape_label.setStyleSheet(
            "color: #409eff; font-size: 11px; font-weight: bold; background: #ecf5ff; border-radius: 4px; padding: 1px 6px; border: 1px solid #d9ecff;")
        title_line.addWidget(self.title_label);
        title_line.addWidget(self.shape_label);
        title_line.addStretch()
        info_layout.addLayout(title_line)

        # 动态属性容器
        self.dynamic_attr_container = QWidget()
        self.dynamic_attr_layout = QVBoxLayout(self.dynamic_attr_container)
        self.dynamic_attr_layout.setContentsMargins(0, 0, 0, 0);
        self.dynamic_attr_layout.setSpacing(2)
        info_layout.addWidget(self.dynamic_attr_container)

        # 备注显示
        self.desc_label = QLabel("备注: -")
        self.desc_label.setStyleSheet("color: #909399; font-size: 11px; font-style: italic; margin-top: 4px;")
        self.desc_label.setWordWrap(True)
        info_layout.addWidget(self.desc_label)

        h_layout.addWidget(self.emoji_label)
        h_layout.addLayout(info_layout, 1)  # 左侧信息占 1 份

        # 2. 右侧：时间生命周期图 (恢复功能)
        self.time_container = QWidget()
        time_layout = QHBoxLayout(self.time_container)
        time_layout.setSpacing(2)
        time_layout.setContentsMargins(10, 0, 0, 0)  # 左边留点空隙

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

        # 让时间容器靠右对齐
        h_layout.addWidget(self.time_container, 0, Qt.AlignRight | Qt.AlignTop)

        self.edit_btn = QPushButton("✎ 修改")
        self.edit_btn.setStyleSheet(BTN_GHOST_STYLE)
        self.edit_btn.clicked.connect(self.on_edit_info_click)
        self.header_card.add_header_widget(self.edit_btn)

        container = QWidget();
        container.setLayout(h_layout)
        self.header_card.content_layout.addWidget(container)

    # === 辅助方法：创建时间盒子 ===
    def _create_mini_time_box(self, title, color):
        lbl = QLabel(f"{title}\n-")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 10px; font-weight: bold; color: {color}; 
                border: 1px solid {color}; border-radius: 4px; padding: 2px 4px;
                background-color: #ffffff;
                font-family: "Microsoft YaHei";
                min-width: 36px;
            }}
        """)
        return lbl

    def _create_arrow(self):
        l = QLabel("›")
        l.setStyleSheet("color: #dcdfe6; font-size: 16px; font-weight: bold; margin-bottom: 2px;")
        return l

    def _init_mass_section(self):
        self.mass_card = ModernCard("📊 质量监控")
        self.mass_card.setMinimumHeight(240);
        self.mass_card.setMaximumHeight(450)
        self.mass_chart_type = QComboBox();
        self.mass_chart_type.addItems(["质量(g)", "变化率(%)"])
        self.mass_chart_type.setStyleSheet(
            "QComboBox { border: 1px solid #dcdfe6; border-radius: 4px; padding: 2px 4px; font-size: 11px; }")
        self.mass_chart_type.currentIndexChanged.connect(self.update_mass_chart)
        self.mass_card.add_header_widget(self.mass_chart_type)
        self.add_mass_btn = QPushButton("➕ 记录");
        self.add_mass_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        self.add_mass_btn.clicked.connect(self.on_add_weight_click)
        self.mass_card.add_header_widget(self.add_mass_btn)

        l = QVBoxLayout();
        l.setSpacing(8)
        self.mass_chart = MassTrendChart(self, width=5, height=2.8)
        self.mass_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mass_table = QTableWidget();
        self.mass_table.setColumnCount(4)
        self.mass_table.setHorizontalHeaderLabels(["日期", "天数", "质量(g)", "变化(%)"])
        self.mass_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);
        self.mass_table.verticalHeader().setVisible(False)
        self.mass_table.setStyleSheet(TABLE_STYLE);
        self.mass_table.setSelectionBehavior(QTableWidget.SelectRows);
        self.mass_table.setMaximumHeight(100)
        self.mass_table.setContextMenuPolicy(Qt.CustomContextMenu);
        self.mass_table.customContextMenuRequested.connect(self.show_mass_menu)
        l.addWidget(self.mass_chart, stretch=10);
        l.addWidget(self.mass_table, stretch=0)
        c = QWidget();
        c.setLayout(l);
        self.mass_card.content_layout.addWidget(c)

    def _init_stress_section(self):
        self.stress_card = ModernCard("📈 应力应变 (UCS)")
        self.stress_card.setMinimumHeight(300);
        self.stress_card.setMaximumHeight(450)
        self.add_stress_btn = QPushButton("➕ 记录点");
        self.add_stress_btn.setStyleSheet(BTN_GHOST_STYLE)
        self.add_stress_btn.clicked.connect(self.on_add_stress_click)
        self.import_stress_btn = QPushButton("📥 导入");
        self.import_stress_btn.setStyleSheet(BTN_SUCCESS_STYLE)
        self.import_stress_btn.clicked.connect(self.on_import_stress_click)
        self.stress_card.add_header_widget(self.add_stress_btn)
        self.stress_card.add_header_widget(self.import_stress_btn)

        l = QVBoxLayout();
        l.setSpacing(5)
        self.stress_chart = StressStrainChart(self, width=5, height=2.8)
        self.stress_chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stress_chart.data_modified.connect(
            lambda data: self.file_manager.save_stress_data(self.current_project, self.current_sample, data))
        self.stress_chart.file_dropped.connect(self.process_imported_stress_file)
        l.addWidget(self.stress_chart)
        c = QWidget();
        c.setLayout(l);
        self.stress_card.content_layout.addWidget(c)

    def _init_gallery_section(self):
        self.gallery_card = ModernCard("🗂️ 附件画廊")
        self.gallery_card.add_header_widget(QLabel("支持拖拽上传"))
        self.image_container = QWidget()
        self.image_grid = QGridLayout(self.image_container)
        self.image_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft);
        self.image_grid.setSpacing(12);
        self.image_grid.setContentsMargins(0, 0, 0, 0)
        self.gallery_card.content_layout.addWidget(self.image_container)

    def _init_welcome_section(self):
        self.welcome_container = QWidget()
        self.welcome_container.setStyleSheet("background-color: transparent;")
        l = QVBoxLayout(self.welcome_container)
        l.setAlignment(Qt.AlignCenter)
        l.setSpacing(20)

        l.addStretch()

        icon_lbl = QLabel("🔬")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 80px; font-family: 'Segoe UI Emoji'; background: transparent;")
        l.addWidget(icon_lbl)

        title_lbl = QLabel("欢迎使用试样记录管理中心")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #2c3e50; font-family: 'Microsoft YaHei'; background: transparent;")
        l.addWidget(title_lbl)

        guide_text = """
        <div style='color: #7f8c8d; font-size: 14px; line-height: 1.5;'>
            <p>👈 <b>开始工作：</b>请在左侧点击“新建项目”或选择已有试样。</p>
            <p>📊 <b>功能亮点：</b>支持 UCS 数据导入、质量变化追踪及附件管理。</p>
            <p>💡 <b>提示：</b>右键点击列表项可进行更多操作。</p>
        </div>
        """
        guide_lbl = QLabel(guide_text)
        guide_lbl.setAlignment(Qt.AlignCenter)
        guide_lbl.setTextFormat(Qt.RichText)
        guide_lbl.setStyleSheet("background: transparent;")
        l.addWidget(guide_lbl)

        l.addStretch()

    def show_welcome(self, message=None):
        self.scroll_area.hide()
        self.welcome_container.show()
        self.current_sample = None

    def load_sample(self, project_name, sample_id):
        self.welcome_container.hide()
        self.scroll_area.show()

        self.current_project = project_name
        self.current_sample = sample_id

        info = self.file_manager.get_sample_info(project_name, sample_id)
        self.current_info = info
        if not info: return

        template_id = info.get("template_id", "micp_sand")
        template_config = TemplateManager.get_template(template_id)

        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self.main_layout.addWidget(self.header_card, 0, 0, 1, 2)
        self.header_card.show()

        cards_to_show = template_config.get("cards", [])

        active_cards = []
        if "mass_card" in cards_to_show:
            self._update_mass_content(info)
            self.mass_card.show()
            active_cards.append(self.mass_card)
        if "stress_card" in cards_to_show:
            self._update_stress_content(info)
            self.stress_card.show()
            active_cards.append(self.stress_card)

        curr_row = 1
        curr_col = 0
        for card in active_cards:
            self.main_layout.addWidget(card, curr_row, curr_col)
            curr_col += 1
            if curr_col > 1:
                curr_col = 0
                curr_row += 1

        if curr_col == 1:
            curr_row += 1

        if "gallery_card" in cards_to_show:
            self.main_layout.addWidget(self.gallery_card, curr_row, 0, 1, 2)
            self.gallery_card.show()
            self.refresh_gallery()

        self.emoji_label.setText(info.get("icon_emoji", "🧪"))
        self.title_label.setText(info.get('id'))

        # 1. 恢复尺寸显示
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
            self.shape_label.setText(shape)
            self.shape_label.show()

        # 2. 恢复备注显示
        desc = info.get("description", "")
        if desc:
            self.desc_label.setText(f"备注: {desc}")
            self.desc_label.show()
        else:
            self.desc_label.hide()

        # 3. 恢复全生命周期时间图
        def set_time_box(lbl, val):
            short = val.replace("-", "/").split(" ")[0] if (val and val != "-") else "-"
            title = lbl.text().splitlines()[0]
            lbl.setText(f"{title}\n{short}")

        set_time_box(self.lbl_prep, info.get('date_prep', '-'))
        set_time_box(self.lbl_comp, info.get('date_complete', '-'))  # 完成字段在 dialog 中删了，如果旧数据有就显示，没有就 -
        # 注意：现在 dialog 只有 prep 和 test，所以 comp 和 demold 可能没数据，正常显示 "-" 即可
        set_time_box(self.lbl_demold, info.get('date_demold', '-'))
        set_time_box(self.lbl_test, info.get('date_test', '-'))

        # 动态属性显示
        while self.dynamic_attr_layout.count():
            item = self.dynamic_attr_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        attributes = info.get("attributes", {})
        config_attrs = template_config.get("attributes", [])

        for attr_def in config_attrs:
            key = attr_def["key"]
            label = attr_def["label"]
            val = attributes.get(key, "-")
            unit = attr_def.get("unit", "")

            row_widget = QWidget()
            row_l = QHBoxLayout(row_widget);
            row_l.setContentsMargins(0, 0, 0, 0);
            row_l.setSpacing(5)
            name_lbl = QLabel(f"{label}:")
            name_lbl.setStyleSheet("color: #909399; font-size: 12px;")
            val_lbl = QLabel(f"{val} {unit}")
            val_lbl.setStyleSheet("color: #303133; font-size: 12px; font-weight: bold;")
            row_l.addWidget(name_lbl);
            row_l.addWidget(val_lbl);
            row_l.addStretch()
            self.dynamic_attr_layout.addWidget(row_widget)

    def _update_mass_content(self, info):
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
            self.mass_table.setItem(i, 1, QTableWidgetItem(str(rec.get("days", "-"))))
            self.mass_table.setItem(i, 2, QTableWidgetItem(f"{mass}"))
            self.mass_table.setItem(i, 3, QTableWidgetItem(rate_str))
        self.mass_chart_type.setCurrentIndex(0)
        self.update_mass_chart()

    def _update_stress_content(self, info):
        stress_data = self.file_manager.get_stress_data(self.current_project, self.current_sample)
        if stress_data:
            self.stress_chart.update_chart(stress_data)
        else:
            self.stress_chart.clear_chart()

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
            self.process_imported_stress_file(file_path)

    def process_imported_stress_file(self, file_path):
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
        menu.setStyleSheet(MENU_STYLE)
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
        menu.setStyleSheet(MENU_STYLE)
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