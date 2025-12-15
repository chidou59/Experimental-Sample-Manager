from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                               QLineEdit, QDialogButtonBox, QTextEdit, QPushButton,
                               QLabel, QHBoxLayout, QDoubleSpinBox, QComboBox,
                               QStackedWidget, QWidget, QListView, QListWidget,
                               QListWidgetItem, QCheckBox)
from PySide6.QtCore import QTime, Qt, QDateTime
from PySide6.QtGui import QFont

from src.views.dialog_utils import (SAMPLE_ICONS, apply_dialog_theme, create_datetime_edit)


class NewSampleDialog(QDialog):
    def __init__(self, parent=None, template_data=None):
        super().__init__(parent)
        self.setWindowTitle("新建试样")
        if template_data:
            self.setWindowTitle("新建试样 (复制自 " + template_data.get('id', '') + ")")

        self.resize(550, 700)  # 稍微减小高度，因为少了一个框

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("例如: A1-Ca0.5 (必填)")
        form_layout.addRow("试样编号*:", self.id_input)

        self.icon_combo = QComboBox()
        self.icon_combo.setView(QListView())
        self.icon_combo.addItems(SAMPLE_ICONS)
        self.icon_combo.setCurrentIndex(0)
        font = QFont()
        font.setPointSize(16)
        self.icon_combo.setFont(font)

        form_layout.addRow("试样图标:", self.icon_combo)

        self.mass_input = QDoubleSpinBox()
        self.mass_input.setRange(0, 9999.99);
        self.mass_input.setDecimals(2);
        self.mass_input.setSuffix(" g")
        form_layout.addRow("初始质量:", self.mass_input)

        self.shape_combo = QComboBox()
        self.shape_combo.setView(QListView(self.shape_combo))
        self.shape_combo.addItems(["未指定", "圆柱体 (Cylinder)", "正方体 (Cube)", "长方体 (Cuboid)"])
        form_layout.addRow("试样形状:", self.shape_combo)

        self.dim_stack = QStackedWidget()
        self.dim_stack.addWidget(QWidget())  # 0

        # 1. 圆柱体
        page_cyl = QWidget();
        lay_cyl = QFormLayout(page_cyl);
        lay_cyl.setContentsMargins(0, 0, 0, 0)
        self.cyl_r = QDoubleSpinBox();
        self.cyl_r.setRange(0, 9999);
        self.cyl_r.setDecimals(0);
        self.cyl_r.setSuffix(" mm")
        self.cyl_h = QDoubleSpinBox();
        self.cyl_h.setRange(0, 9999);
        self.cyl_h.setDecimals(0);
        self.cyl_h.setSuffix(" mm")
        lay_cyl.addRow("半径 (r):", self.cyl_r);
        lay_cyl.addRow("高度 (h):", self.cyl_h)
        self.dim_stack.addWidget(page_cyl)

        # 2. 正方体
        page_cube = QWidget();
        lay_cube = QFormLayout(page_cube);
        lay_cube.setContentsMargins(0, 0, 0, 0)
        self.cube_a = QDoubleSpinBox();
        self.cube_a.setRange(0, 9999);
        self.cube_a.setDecimals(0);
        self.cube_a.setSuffix(" mm")
        lay_cube.addRow("边长 (a):", self.cube_a)
        self.dim_stack.addWidget(page_cube)

        # 3. 长方体
        page_cuboid = QWidget();
        lay_cuboid = QFormLayout(page_cuboid);
        lay_cuboid.setContentsMargins(0, 0, 0, 0)
        self.cuboid_l = QDoubleSpinBox();
        self.cuboid_l.setRange(0, 9999);
        self.cuboid_l.setDecimals(0);
        self.cuboid_l.setSuffix(" mm")
        self.cuboid_w = QDoubleSpinBox();
        self.cuboid_w.setRange(0, 9999);
        self.cuboid_w.setDecimals(0);
        self.cuboid_w.setSuffix(" mm")
        self.cuboid_h = QDoubleSpinBox();
        self.cuboid_h.setRange(0, 9999);
        self.cuboid_h.setDecimals(0);
        self.cuboid_h.setSuffix(" mm")
        lay_cuboid.addRow("长度 (L):", self.cuboid_l);
        lay_cuboid.addRow("宽度 (W):", self.cuboid_w);
        lay_cuboid.addRow("高度 (H):", self.cuboid_h)
        self.dim_stack.addWidget(page_cuboid)

        form_layout.addRow("几何尺寸:", self.dim_stack)
        self.shape_combo.currentIndexChanged.connect(self.dim_stack.setCurrentIndex)

        # 【核心修改】合并了配方和描述
        self.recipe_input = QTextEdit()
        self.recipe_input.setPlaceholderText("试样的配方、描述，方便后续分析")
        self.recipe_input.setMaximumHeight(80)  # 稍微增加高度
        form_layout.addRow("试样配方/描述:", self.recipe_input)

        # 关键变量 (拆分为 名称 + 数值)
        key_var_layout = QHBoxLayout()
        self.key_var_name = QLineEdit()
        self.key_var_name.setPlaceholderText("如: 浓度")
        self.key_var_name.setFixedWidth(120)

        self.key_var_input = QDoubleSpinBox()
        self.key_var_input.setRange(-99999, 99999)
        self.key_var_input.setDecimals(3)
        self.key_var_input.setToolTip("用于对比分析的数值")

        key_var_layout.addWidget(self.key_var_name)
        key_var_layout.addWidget(self.key_var_input)

        form_layout.addRow("关键配方变量:", key_var_layout)

        # 【已删除】删除了独立的 desc_input

        self.date_prep = create_datetime_edit()
        self.date_complete = create_datetime_edit()
        self.date_demold = create_datetime_edit()
        self.date_test = create_datetime_edit()
        form_layout.addRow("制样时间:", self.date_prep)
        form_layout.addRow("完成时间:", self.date_complete)
        form_layout.addRow("拆模时间:", self.date_demold)
        form_layout.addRow("测试时间:", self.date_test)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept);
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        apply_dialog_theme(self, self.buttons)

        # 如果有模板数据，则自动回填
        if template_data:
            self.fill_from_template(template_data)

    def fill_from_template(self, data):
        self.id_input.setText(f"{data.get('id', '')}_copy")
        self.id_input.selectAll()
        self.id_input.setFocus()

        emoji = data.get("icon_emoji", "🧪")
        idx = self.icon_combo.findText(emoji)
        if idx >= 0: self.icon_combo.setCurrentIndex(idx)

        self.mass_input.setValue(float(data.get("initial_mass", 0)))

        shape_str = data.get("shape", "未指定")
        idx = self.shape_combo.findText(shape_str)
        if idx >= 0: self.shape_combo.setCurrentIndex(idx)

        self.cyl_r.setValue(float(data.get("radius", 0)))
        self.cyl_h.setValue(float(data.get("height", 0)))
        self.cube_a.setValue(float(data.get("side_length", 0)))
        self.cuboid_l.setValue(float(data.get("length", 0)))
        self.cuboid_w.setValue(float(data.get("width", 0)))
        if "height" in data:
            self.cuboid_h.setValue(float(data.get("height", 0)))

        # 【核心修改】合并旧数据中的配方和描述
        rec = data.get("recipe", "")
        desc = data.get("description", "")
        combined = f"{rec}\n{desc}".strip()  # 如果都有，换行拼接
        self.recipe_input.setPlainText(combined)

        # 回填关键变量
        self.key_var_name.setText(data.get("key_variable_name", ""))
        self.key_var_input.setValue(float(data.get("key_variable", 0)))

        def set_dt(widget, val):
            if val and val != "-":
                dt = QDateTime.fromString(val, "yyyy-MM-dd-HH:00")
                if not dt.isValid():
                    dt = QDateTime.fromString(val, "yyyy-MM-dd")
                    dt.setTime(QTime(0, 0, 0))
                if dt.isValid():
                    widget.setDateTime(dt)

        set_dt(self.date_prep, data.get("date_prep"))
        set_dt(self.date_complete, data.get("date_complete"))
        set_dt(self.date_demold, data.get("date_demold"))
        set_dt(self.date_test, data.get("date_test"))

    def get_data(self):
        data = {
            "id": self.id_input.text().strip(),
            "initial_mass": self.mass_input.value(),
            "recipe": self.recipe_input.toPlainText(),  # 统一存入 recipe
            "key_variable": self.key_var_input.value(),
            "key_variable_name": self.key_var_name.text().strip(),
            "icon_emoji": self.icon_combo.currentText(),
            "date_prep": self.date_prep.text(),
            "date_complete": self.date_complete.text(),
            "date_demold": self.date_demold.text(),
            "date_test": self.date_test.text(),
            "shape": self.shape_combo.currentText()
        }
        shape_idx = self.shape_combo.currentIndex()
        if shape_idx == 1:
            data["radius"] = self.cyl_r.value()
            data["height"] = self.cyl_h.value()
        elif shape_idx == 2:
            data["side_length"] = self.cube_a.value()
        elif shape_idx == 3:
            data["length"] = self.cuboid_l.value()
            data["width"] = self.cuboid_w.value()
            data["height"] = self.cuboid_h.value()
        return data


class EditSampleDialog(QDialog):
    def __init__(self, current_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改信息")
        self.resize(550, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)

        self.id_input = QLineEdit(current_data.get("id", ""))
        form_layout.addRow("试样编号:", self.id_input)

        self.icon_combo = QComboBox()
        self.icon_combo.setView(QListView())
        self.icon_combo.addItems(SAMPLE_ICONS)
        font = QFont();
        font.setPointSize(16);
        self.icon_combo.setFont(font)
        current_emoji = current_data.get("icon_emoji", "🧪")
        idx = self.icon_combo.findText(current_emoji)
        if idx >= 0: self.icon_combo.setCurrentIndex(idx)
        form_layout.addRow("试样图标:", self.icon_combo)

        self.mass_input = QDoubleSpinBox()
        self.mass_input.setRange(0, 9999.99);
        self.mass_input.setDecimals(2);
        self.mass_input.setSuffix(" g")
        self.mass_input.setValue(float(current_data.get("initial_mass", 0)))
        form_layout.addRow("初始质量:", self.mass_input)

        self.shape_combo = QComboBox()
        self.shape_combo.setView(QListView(self.shape_combo))
        self.shape_combo.addItems(["未指定", "圆柱体 (Cylinder)", "正方体 (Cube)", "长方体 (Cuboid)"])
        form_layout.addRow("试样形状:", self.shape_combo)

        self.dim_stack = QStackedWidget()
        self.dim_stack.addWidget(QWidget())

        page_cyl = QWidget();
        lay_cyl = QFormLayout(page_cyl);
        lay_cyl.setContentsMargins(0, 0, 0, 0)
        self.cyl_r = QDoubleSpinBox();
        self.cyl_r.setRange(0, 9999);
        self.cyl_r.setDecimals(0);
        self.cyl_r.setSuffix(" mm")
        self.cyl_h = QDoubleSpinBox();
        self.cyl_h.setRange(0, 9999);
        self.cyl_h.setDecimals(0);
        self.cyl_h.setSuffix(" mm")
        lay_cyl.addRow("半径 (r):", self.cyl_r);
        lay_cyl.addRow("高度 (h):", self.cyl_h)
        self.dim_stack.addWidget(page_cyl)

        page_cube = QWidget();
        lay_cube = QFormLayout(page_cube);
        lay_cube.setContentsMargins(0, 0, 0, 0)
        self.cube_a = QDoubleSpinBox();
        self.cube_a.setRange(0, 9999);
        self.cube_a.setDecimals(0);
        self.cube_a.setSuffix(" mm")
        lay_cube.addRow("边长 (a):", self.cube_a)
        self.dim_stack.addWidget(page_cube)

        page_cuboid = QWidget();
        lay_cuboid = QFormLayout(page_cuboid);
        lay_cuboid.setContentsMargins(0, 0, 0, 0)
        self.cuboid_l = QDoubleSpinBox();
        self.cuboid_l.setRange(0, 9999);
        self.cuboid_l.setDecimals(0);
        self.cuboid_l.setSuffix(" mm")
        self.cuboid_w = QDoubleSpinBox();
        self.cuboid_w.setRange(0, 9999);
        self.cuboid_w.setDecimals(0);
        self.cuboid_w.setSuffix(" mm")
        self.cuboid_h = QDoubleSpinBox();
        self.cuboid_h.setRange(0, 9999);
        self.cuboid_h.setDecimals(0);
        self.cuboid_h.setSuffix(" mm")
        lay_cuboid.addRow("长度 (L):", self.cuboid_l);
        lay_cuboid.addRow("宽度 (W):", self.cuboid_w);
        lay_cuboid.addRow("高度 (H):", self.cuboid_h)
        self.dim_stack.addWidget(page_cuboid)

        form_layout.addRow("几何尺寸:", self.dim_stack)
        self.shape_combo.currentIndexChanged.connect(self.dim_stack.setCurrentIndex)

        shape_str = current_data.get("shape", "未指定")
        idx = self.shape_combo.findText(shape_str)
        if idx >= 0:
            self.shape_combo.setCurrentIndex(idx)
        else:
            self.shape_combo.setCurrentIndex(0)

        self.cyl_r.setValue(float(current_data.get("radius", 0)))
        self.cyl_h.setValue(float(current_data.get("height", 0)))
        self.cube_a.setValue(float(current_data.get("side_length", 0)))
        self.cuboid_l.setValue(float(current_data.get("length", 0)))
        self.cuboid_w.setValue(float(current_data.get("width", 0)))
        if "height" in current_data and idx == 3:
            self.cuboid_h.setValue(float(current_data.get("height", 0)))

        # 【核心修改】合并配方和描述到同一个文本框
        self.recipe_input = QTextEdit()
        rec_text = current_data.get("recipe", "")
        desc_text = current_data.get("description", "") or current_data.get("note", "")
        combined_text = rec_text
        if desc_text and desc_text not in rec_text:  # 简单去重避免重复拼接
            combined_text += f"\n{desc_text}"
        self.recipe_input.setPlainText(combined_text.strip())

        self.recipe_input.setMaximumHeight(80)
        form_layout.addRow("试样配方/描述:", self.recipe_input)

        # 关键配方变量 (拆分为 名称 + 数值)
        key_var_layout = QHBoxLayout()
        self.key_var_name = QLineEdit()
        self.key_var_name.setPlaceholderText("变量名 (如: 浓度)")
        self.key_var_name.setText(current_data.get("key_variable_name", ""))
        self.key_var_name.setFixedWidth(120)

        self.key_var_input = QDoubleSpinBox()
        self.key_var_input.setRange(-99999, 99999)
        self.key_var_input.setDecimals(3)
        self.key_var_input.setValue(float(current_data.get("key_variable", 0)))

        key_var_layout.addWidget(self.key_var_name)
        key_var_layout.addWidget(self.key_var_input)

        form_layout.addRow("关键配方变量:", key_var_layout)

        # 【已删除】删除了独立的 desc_input

        self.date_prep = create_datetime_edit(current_data.get("date_prep"))
        self.date_complete = create_datetime_edit(current_data.get("date_complete"))
        self.date_demold = create_datetime_edit(current_data.get("date_demold"))
        self.date_test = create_datetime_edit(current_data.get("date_test"))
        form_layout.addRow("制样时间:", self.date_prep)
        form_layout.addRow("完成时间:", self.date_complete)
        form_layout.addRow("拆模时间:", self.date_demold)
        form_layout.addRow("测试时间:", self.date_test)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept);
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        apply_dialog_theme(self, self.buttons)

    def get_data(self):
        data = {
            "id": self.id_input.text().strip(),
            "initial_mass": self.mass_input.value(),
            "recipe": self.recipe_input.toPlainText(),  # 统一存入 recipe
            "key_variable": self.key_var_input.value(),
            "key_variable_name": self.key_var_name.text().strip(),  # 新增字段
            "icon_emoji": self.icon_combo.currentText(),
            "date_prep": self.date_prep.text(),
            "date_complete": self.date_complete.text(),
            "date_demold": self.date_demold.text(),
            "date_test": self.date_test.text(),
            "shape": self.shape_combo.currentText()
        }
        shape_idx = self.shape_combo.currentIndex()
        if shape_idx == 1:
            data["radius"] = self.cyl_r.value()
            data["height"] = self.cyl_h.value()
        elif shape_idx == 2:
            data["side_length"] = self.cube_a.value()
        elif shape_idx == 3:
            data["length"] = self.cuboid_l.value()
            data["width"] = self.cuboid_w.value()
            data["height"] = self.cuboid_h.value()
        return data


class AddWeightDialog(QDialog):
    def __init__(self, current_data=None, parent=None):
        super().__init__(parent)
        title = "修改质量记录" if current_data else "记录质量"
        self.setWindowTitle(title)
        self.resize(350, 220)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        form = QFormLayout()
        form.setVerticalSpacing(15)
        form.setHorizontalSpacing(15)

        init_date = current_data.get("date") if current_data else None
        self.date_input = create_datetime_edit(init_date)

        self.mass_input = QDoubleSpinBox()
        self.mass_input.setRange(0, 9999.99)
        self.mass_input.setDecimals(2)
        self.mass_input.setSuffix(" g")

        if current_data:
            self.mass_input.setValue(float(current_data.get("mass", 0)))

        form.addRow("称重时间:", self.date_input)
        form.addRow("当前质量:", self.mass_input)

        layout.addLayout(form)
        layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        apply_dialog_theme(self, self.buttons)

    def get_data(self):
        return {
            "date": self.date_input.text(),
            "mass": self.mass_input.value()
        }


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.resize(400, 250)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        form = QFormLayout()
        form.setVerticalSpacing(15)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: 2025_砂柱实验")

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("简单描述实验目的...")

        form.addRow("项目名称:", self.name_input)
        form.addRow("项目描述:", self.desc_input)

        layout.addLayout(form)
        layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        apply_dialog_theme(self, self.buttons)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip()
        }


class BatchCopyWeightDialog(QDialog):
    def __init__(self, source_id, all_samples, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"批量应用质量记录 - 源: {source_id}")
        self.resize(450, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl = QLabel(f"请选择要将 [{source_id}] 的质量记录应用到哪些试样？")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { border: 1px solid #ccc; border-radius: 4px; padding: 5px; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:hover { background: #f0f2f5; }
        """)
        for s_id in all_samples:
            if s_id == source_id: continue
            item = QListWidgetItem(s_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_all = QPushButton("全选")
        self.btn_none = QPushButton("全不选")

        mini_btn_style = "QPushButton { padding: 4px 10px; font-size: 12px; background: #eee; border: none; border-radius: 3px; } QPushButton:hover { background: #ddd; }"
        self.btn_all.setStyleSheet(mini_btn_style)
        self.btn_none.setStyleSheet(mini_btn_style)

        self.btn_all.clicked.connect(lambda: self.set_all_checked(True))
        self.btn_none.clicked.connect(lambda: self.set_all_checked(False))

        btn_layout.addWidget(self.btn_all)
        btn_layout.addWidget(self.btn_none)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.overwrite_cb = QCheckBox("⚠️ 完全覆盖 (清空目标原有的记录，完全替换为源记录)")
        self.overwrite_cb.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.overwrite_cb.setToolTip("如果不勾选，则为【合并模式】：保留目标已有记录，仅追加新日期的记录。")
        layout.addWidget(self.overwrite_cb)

        layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        apply_dialog_theme(self, self.buttons)

    def set_all_checked(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(state)

    def get_data(self):
        selected_ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_ids.append(item.text())

        return {
            "target_ids": selected_ids,
            "overwrite": self.overwrite_cb.isChecked()
        }


class AddStressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("记录应力应变点")
        self.resize(350, 200)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        form = QFormLayout()
        form.setVerticalSpacing(15)

        self.strain_input = QDoubleSpinBox()
        self.strain_input.setRange(0, 9999.99)
        self.strain_input.setDecimals(3)
        self.strain_input.setSuffix(" %")
        self.strain_input.setSingleStep(0.1)

        self.stress_input = QDoubleSpinBox()
        self.stress_input.setRange(0, 999999.99)
        self.stress_input.setDecimals(3)
        self.stress_input.setSuffix(" kPa")
        self.stress_input.setSingleStep(10.0)

        form.addRow("应变 (Strain):", self.strain_input)
        form.addRow("应力 (Stress):", self.stress_input)

        layout.addLayout(form)
        layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        apply_dialog_theme(self, self.buttons)

    def get_data(self):
        return {
            "strain": self.strain_input.value(),
            "stress": self.stress_input.value()
        }