from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                               QLineEdit, QDialogButtonBox, QTextEdit, QPushButton,
                               QLabel, QHBoxLayout, QDoubleSpinBox, QComboBox,
                               QStackedWidget, QWidget, QListView, QListWidget,
                               QListWidgetItem, QCheckBox, QGroupBox, QScrollArea, QSizePolicy, QFrame)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
import json

from src.views.dialog_utils import (SAMPLE_ICONS, apply_dialog_theme, create_datetime_edit)
from src.utils.template_manager import TemplateManager


class NewSampleDialog(QDialog):
    def __init__(self, parent=None, template_id="micp_sand", template_data=None):
        """
        :param template_id: 从项目继承来的模板ID
        :param template_data: 如果是"复制新建"，这里传入源数据
        """
        super().__init__(parent)
        self.setWindowTitle("新建试样")
        if template_data:
            self.setWindowTitle("新建试样 (复制自 " + str(template_data.get('id', '')) + ")")

        # 调整窗口大小
        self.resize(550, 750)
        self.template_id = template_id

        # === 主布局 (垂直) ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === 1. 滚动区域 (Scroll Area) ===
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 滚动区的内容容器
        self.content_widget = QWidget()
        # 强制白色背景，圆角，防止黑色背景问题
        self.content_widget.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QGroupBox { 
                font-weight: bold; color: #333; 
                border: 1px solid #dcdfe6; border-radius: 6px; 
                margin-top: 10px; padding-top: 15px; font-size: 13px; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)

        self.form_layout = QVBoxLayout(self.content_widget)
        self.form_layout.setContentsMargins(25, 25, 25, 25)
        self.form_layout.setSpacing(20)

        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

        # === 2. 填充内容 ===

        # --- Group 1: 基础信息 ---
        self.base_group = QGroupBox("基础信息")
        base_layout = QFormLayout(self.base_group)
        base_layout.setVerticalSpacing(12)

        # 模板名称
        t_config = TemplateManager.get_template(self.template_id)
        t_name_lbl = QLabel(t_config.get("name", "未知模板"))
        t_name_lbl.setStyleSheet("color: #409eff; font-weight: bold; font-size: 13px;")
        base_layout.addRow("所属模板:", t_name_lbl)

        # 编号
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("例如: A1-Group1 (必填)")
        self.id_input.setStyleSheet("padding: 6px; border: 1px solid #ccc; border-radius: 4px;")
        base_layout.addRow("试样编号*:", self.id_input)

        # 图标
        self.icon_combo = QComboBox()
        self.icon_combo.setView(QListView())
        self.icon_combo.addItems(SAMPLE_ICONS)
        self.icon_combo.setStyleSheet("padding: 4px;")
        font = QFont();
        font.setPointSize(14);
        self.icon_combo.setFont(font)
        base_layout.addRow("图标:", self.icon_combo)

        self.form_layout.addWidget(self.base_group)

        # --- Group 2: 动态属性 (根据模板) ---
        self.attr_group = QGroupBox("材料属性")
        self.attr_layout = QFormLayout(self.attr_group)
        self.attr_layout.setVerticalSpacing(12)
        self.form_layout.addWidget(self.attr_group)

        self.dynamic_widgets = {}
        self._init_attributes_ui()  # 动态生成输入框

        # --- Group 3: 几何与质量 ---
        self.geom_group = QGroupBox("几何与质量")
        geom_layout = QFormLayout(self.geom_group)
        geom_layout.setVerticalSpacing(12)

        self.mass_input = QDoubleSpinBox()
        self.mass_input.setRange(0, 9999.99);
        self.mass_input.setDecimals(2);
        self.mass_input.setSuffix(" g")
        self.mass_input.setStyleSheet("padding: 4px;")
        geom_layout.addRow("初始质量:", self.mass_input)

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["未指定", "圆柱体 (Cylinder)", "正方体 (Cube)", "长方体 (Cuboid)"])
        self.shape_combo.setStyleSheet("padding: 4px;")
        geom_layout.addRow("形状:", self.shape_combo)

        # 尺寸堆栈 (QStackedWidget)
        self.dim_stack = QStackedWidget()
        self.dim_stack.addWidget(QWidget())  # Index 0: 空

        # Index 1: 圆柱
        page_cyl = QWidget();
        l_cyl = QFormLayout(page_cyl);
        l_cyl.setContentsMargins(0, 0, 0, 0)
        self.cyl_r = QDoubleSpinBox();
        self.cyl_r.setRange(0, 9999);
        self.cyl_r.setSuffix(" mm")
        self.cyl_h = QDoubleSpinBox();
        self.cyl_h.setRange(0, 9999);
        self.cyl_h.setSuffix(" mm")
        l_cyl.addRow("半径 (r):", self.cyl_r);
        l_cyl.addRow("高度 (h):", self.cyl_h)
        self.dim_stack.addWidget(page_cyl)

        # Index 2: 正方体
        page_cube = QWidget();
        l_cube = QFormLayout(page_cube);
        l_cube.setContentsMargins(0, 0, 0, 0)
        self.cube_a = QDoubleSpinBox();
        self.cube_a.setRange(0, 9999);
        self.cube_a.setSuffix(" mm")
        l_cube.addRow("边长 (a):", self.cube_a)
        self.dim_stack.addWidget(page_cube)

        # Index 3: 长方体
        page_rect = QWidget();
        l_rect = QFormLayout(page_rect);
        l_rect.setContentsMargins(0, 0, 0, 0)
        self.rect_l = QDoubleSpinBox();
        self.rect_l.setRange(0, 9999);
        self.rect_l.setSuffix(" mm")
        self.rect_w = QDoubleSpinBox();
        self.rect_w.setRange(0, 9999);
        self.rect_w.setSuffix(" mm")
        self.rect_h = QDoubleSpinBox();
        self.rect_h.setRange(0, 9999);
        self.rect_h.setSuffix(" mm")
        l_rect.addRow("长 (L):", self.rect_l);
        l_rect.addRow("宽 (W):", self.rect_w);
        l_rect.addRow("高 (H):", self.rect_h)
        self.dim_stack.addWidget(page_rect)

        geom_layout.addRow("尺寸参数:", self.dim_stack)
        self.shape_combo.currentIndexChanged.connect(self.dim_stack.setCurrentIndex)

        self.form_layout.addWidget(self.geom_group)

        # --- Group 4: 时间信息 ---
        self.time_group = QGroupBox("时间轴")
        time_layout = QFormLayout(self.time_group)
        time_layout.setVerticalSpacing(12)

        self.date_prep = create_datetime_edit()
        self.date_test = create_datetime_edit()

        time_layout.addRow("制样时间:", self.date_prep)
        time_layout.addRow("测试时间:", self.date_test)
        self.form_layout.addWidget(self.time_group)

        # --- Group 5: 备注 (新增) ---
        self.note_group = QGroupBox("备注 / Description")
        note_layout = QVBoxLayout(self.note_group)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("在此填写配方详情、实验现象或其他备注...")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 5px;")
        note_layout.addWidget(self.desc_input)
        self.form_layout.addWidget(self.note_group)

        # === 3. 底部按钮 (固定不滚动) ===
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(20, 15, 20, 15)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # 美化按钮
        self.buttons.button(QDialogButtonBox.Ok).setText("确定创建")
        self.buttons.button(QDialogButtonBox.Cancel).setText("取消")
        apply_dialog_theme(self, self.buttons)

        btn_layout.addStretch()
        btn_layout.addWidget(self.buttons)

        self.main_layout.addWidget(btn_container)

        # 如果是复制新建，回填数据
        if template_data:
            self.fill_from_template(template_data)

    def _init_attributes_ui(self):
        """根据传入的 template_id 初始化属性输入框"""
        config = TemplateManager.get_template(self.template_id)
        attrs = config.get("attributes", [])

        if not attrs:
            self.attr_group.hide()
            return

        for attr in attrs:
            key = attr["key"]
            label_text = attr["label"]
            w_type = attr["type"]
            unit = attr.get("unit", "")
            default_val = attr.get("default")

            widget = None
            if w_type == "float" or w_type == "int":
                widget = QDoubleSpinBox()
                widget.setRange(-99999, 99999)
                widget.setStyleSheet("padding: 4px;")
                if w_type == "int":
                    widget.setDecimals(0)
                else:
                    widget.setDecimals(2)
                if unit: widget.setSuffix(f" {unit}")
                if default_val is not None: widget.setValue(float(default_val))
            else:
                widget = QLineEdit()
                widget.setStyleSheet("padding: 4px;")
                if default_val: widget.setText(str(default_val))

            self.attr_layout.addRow(f"{label_text}:", widget)
            self.dynamic_widgets[key] = widget

    def get_data(self):
        custom_attributes = {}
        for key, widget in self.dynamic_widgets.items():
            if isinstance(widget, QDoubleSpinBox):
                custom_attributes[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                custom_attributes[key] = widget.text().strip()

        data = {
            "id": self.id_input.text().strip(),
            "template_id": self.template_id,
            "attributes": custom_attributes,
            "initial_mass": self.mass_input.value(),
            "shape": self.shape_combo.currentText(),
            "icon_emoji": self.icon_combo.currentText(),
            "date_prep": self.date_prep.text(),
            "date_test": self.date_test.text(),
            "description": self.desc_input.toPlainText().strip(),  # 保存备注
            "recipe": json.dumps(custom_attributes, ensure_ascii=False)
        }

        s_idx = self.shape_combo.currentIndex()
        if s_idx == 1:
            data.update({"radius": self.cyl_r.value(), "height": self.cyl_h.value()})
        elif s_idx == 2:
            data.update({"side_length": self.cube_a.value()})
        elif s_idx == 3:
            data.update({"length": self.rect_l.value(), "width": self.rect_w.value(), "height": self.rect_h.value()})

        return data

    def fill_from_template(self, data):
        """安全回填数据，防止崩溃"""
        try:
            # 1. 基础
            self.id_input.setText(f"{data.get('id', '')}_copy")
            emoji = data.get("icon_emoji", "🧪")
            idx = self.icon_combo.findText(emoji)
            if idx >= 0: self.icon_combo.setCurrentIndex(idx)

            # 2. 动态属性
            attrs = data.get("attributes", {})
            for key, val in attrs.items():
                if key in self.dynamic_widgets:
                    w = self.dynamic_widgets[key]
                    if isinstance(w, QDoubleSpinBox):
                        try:
                            w.setValue(float(val))
                        except:
                            pass
                    elif isinstance(w, QLineEdit):
                        w.setText(str(val))

            # 3. 质量与几何
            try:
                self.mass_input.setValue(float(data.get("initial_mass", 0)))
            except:
                pass

            shape_str = data.get("shape", "未指定")
            idx = self.shape_combo.findText(shape_str)
            if idx >= 0: self.shape_combo.setCurrentIndex(idx)

            try:
                self.cyl_r.setValue(float(data.get("radius", 0)))
            except:
                pass
            try:
                self.cyl_h.setValue(float(data.get("height", 0)))
            except:
                pass
            try:
                self.cube_a.setValue(float(data.get("side_length", 0)))
            except:
                pass
            try:
                self.rect_l.setValue(float(data.get("length", 0)))
            except:
                pass
            try:
                self.rect_w.setValue(float(data.get("width", 0)))
            except:
                pass
            try:
                self.rect_h.setValue(float(data.get("height", 0)))
            except:
                pass

            # 4. 时间
            def set_time(w, t_str):
                if not t_str or t_str == "-": return
                dt = QDateTime.fromString(t_str, "yyyy-MM-dd-HH:00")
                if dt.isValid(): w.setDateTime(dt)

            set_time(self.date_prep, data.get("date_prep"))
            set_time(self.date_test, data.get("date_test"))

            # 5. 备注 (回填)
            self.desc_input.setPlainText(data.get("description", ""))

        except Exception as e:
            print(f"回填数据出错: {e}")


class EditSampleDialog(NewSampleDialog):
    def __init__(self, current_data, parent=None):
        t_id = current_data.get("template_id", "micp_sand")
        super().__init__(parent, template_id=t_id, template_data=current_data)
        self.setWindowTitle("编辑试样信息")
        self.id_input.setText(current_data.get("id"))
        self.buttons.button(QDialogButtonBox.Ok).setText("保存修改")


# === 新建项目弹窗 ===
class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.resize(450, 350)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(QLabel("创建新实验项目"))

        form = QFormLayout()
        form.setVerticalSpacing(15)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: 2025_砂柱实验")
        self.name_input.setStyleSheet("padding: 6px;")

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("简单描述实验目的...")
        self.desc_input.setStyleSheet("padding: 6px;")

        self.template_combo = QComboBox()
        self.template_combo.setStyleSheet("padding: 6px;")
        for t_id, t_name in TemplateManager.get_template_names():
            self.template_combo.addItem(t_name, t_id)

        self.hint_lbl = QLabel("提示: 该项目下的所有试样将默认使用此模板。")
        self.hint_lbl.setStyleSheet("color: #909399; font-size: 11px;")

        form.addRow("项目名称:", self.name_input)
        form.addRow("项目描述:", self.desc_input)
        form.addRow("材料模板:", self.template_combo)
        form.addRow("", self.hint_lbl)

        layout.addLayout(form)
        layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.Ok).setText("创建项目")
        self.buttons.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(self.buttons)

        apply_dialog_theme(self, self.buttons)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip(),
            "template_id": self.template_combo.currentData()
        }


# === 简单的录入弹窗保持不变，但增加背景设置 ===
class AddWeightDialog(QDialog):
    def __init__(self, current_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("记录质量")
        self.resize(350, 200)
        self.setStyleSheet("background-color: white;")  # 修复背景
        layout = QVBoxLayout(self)
        form = QFormLayout()

        init_date = current_data.get("date") if current_data else None
        self.date_input = create_datetime_edit(init_date)

        self.mass_input = QDoubleSpinBox()
        self.mass_input.setRange(0, 9999.99);
        self.mass_input.setDecimals(2);
        self.mass_input.setSuffix(" g")
        if current_data: self.mass_input.setValue(float(current_data.get("mass", 0)))

        form.addRow("时间:", self.date_input)
        form.addRow("质量:", self.mass_input)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        apply_dialog_theme(self, btns)

    def get_data(self):
        return {"date": self.date_input.text(), "mass": self.mass_input.value()}


class BatchCopyWeightDialog(QDialog):
    def __init__(self, source_id, all_samples, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"批量应用质量记录")
        self.resize(400, 500)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"源试样: {source_id}\n选择要应用的目标试样:"))
        self.list_widget = QListWidget()
        for s in all_samples:
            if s != source_id:
                it = QListWidgetItem(s)
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Unchecked)
                self.list_widget.addItem(it)
        layout.addWidget(self.list_widget)
        self.overwrite_cb = QCheckBox("覆盖已有记录")
        layout.addWidget(self.overwrite_cb)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept);
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        apply_dialog_theme(self, btns)

    def get_data(self):
        ids = []
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).checkState() == Qt.Checked:
                ids.append(self.list_widget.item(i).text())
        return {"target_ids": ids, "overwrite": self.overwrite_cb.isChecked()}


class AddStressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据点")
        self.resize(300, 150)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.strain = QDoubleSpinBox();
        self.strain.setRange(0, 9999);
        self.strain.setDecimals(3);
        self.strain.setSuffix(" %")
        self.stress = QDoubleSpinBox();
        self.stress.setRange(0, 99999);
        self.stress.setDecimals(2);
        self.stress.setSuffix(" kPa")
        form.addRow("应变:", self.strain)
        form.addRow("应力:", self.stress)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept);
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        apply_dialog_theme(self, btns)

    def get_data(self):
        return {"strain": self.strain.value(), "stress": self.stress.value()}