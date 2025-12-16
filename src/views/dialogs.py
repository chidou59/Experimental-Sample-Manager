from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                               QLineEdit, QDialogButtonBox, QTextEdit, QPushButton,
                               QLabel, QHBoxLayout, QDoubleSpinBox, QComboBox,
                               QStackedWidget, QWidget, QListView, QListWidget,
                               QListWidgetItem, QCheckBox, QGroupBox, QScrollArea, QSizePolicy, QFrame)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
import json

from src.views.dialog_utils import (SAMPLE_ICONS, apply_dialog_theme, create_datetime_edit)


class NewSampleDialog(QDialog):
    def __init__(self, parent=None, template_data=None):
        super().__init__(parent)
        self.setWindowTitle("新建试样")
        if template_data:
            self.setWindowTitle("新建试样 (复制自 " + str(template_data.get('id', '')) + ")")

        self.resize(550, 750)

        # === 主布局 (垂直) ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === 1. 滚动区域 ===
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
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

        # === 2. 内容填充 ===

        # --- 基础信息 ---
        self.base_group = QGroupBox("基础信息")
        base_layout = QFormLayout(self.base_group)
        base_layout.setVerticalSpacing(12)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("例如: A1-Ca0.5 (必填)")
        self.id_input.setStyleSheet("padding: 6px; border: 1px solid #ccc; border-radius: 4px;")
        base_layout.addRow("试样编号*:", self.id_input)

        self.icon_combo = QComboBox()
        self.icon_combo.setView(QListView())
        self.icon_combo.addItems(SAMPLE_ICONS)
        self.icon_combo.setStyleSheet("padding: 4px;")
        font = QFont();
        font.setPointSize(14);
        self.icon_combo.setFont(font)
        base_layout.addRow("图标:", self.icon_combo)

        self.form_layout.addWidget(self.base_group)

        # --- 几何与质量 ---
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

        self.dim_stack = QStackedWidget()
        self.dim_stack.addWidget(QWidget())

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

        page_cube = QWidget();
        l_cube = QFormLayout(page_cube);
        l_cube.setContentsMargins(0, 0, 0, 0)
        self.cube_a = QDoubleSpinBox();
        self.cube_a.setRange(0, 9999);
        self.cube_a.setSuffix(" mm")
        l_cube.addRow("边长 (a):", self.cube_a)
        self.dim_stack.addWidget(page_cube)

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

        # --- 实验详情 (恢复) ---
        self.detail_group = QGroupBox("配方与变量")
        detail_layout = QFormLayout(self.detail_group)
        detail_layout.setVerticalSpacing(12)

        self.recipe_input = QTextEdit()
        self.recipe_input.setPlaceholderText("试样的配方...")
        self.recipe_input.setMaximumHeight(60)
        self.recipe_input.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 5px;")
        detail_layout.addRow("配方:", self.recipe_input)

        # 关键变量
        key_var_layout = QHBoxLayout()
        self.key_var_name = QLineEdit()
        self.key_var_name.setPlaceholderText("变量名(如:浓度)")
        self.key_var_name.setFixedWidth(100)
        self.key_var_input = QDoubleSpinBox()
        self.key_var_input.setRange(-99999, 99999);
        self.key_var_input.setDecimals(3)
        key_var_layout.addWidget(self.key_var_name)
        key_var_layout.addWidget(self.key_var_input)
        detail_layout.addRow("关键变量:", key_var_layout)

        self.form_layout.addWidget(self.detail_group)

        # --- 时间与备注 ---
        self.time_group = QGroupBox("时间与备注")
        time_layout = QFormLayout(self.time_group)
        time_layout.setVerticalSpacing(12)

        self.date_prep = create_datetime_edit()
        self.date_complete = create_datetime_edit()
        self.date_demold = create_datetime_edit()
        self.date_test = create_datetime_edit()

        time_layout.addRow("制样时间:", self.date_prep)
        time_layout.addRow("完成时间:", self.date_complete)
        time_layout.addRow("拆模时间:", self.date_demold)
        time_layout.addRow("测试时间:", self.date_test)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("实验笔记/备注...")
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 5px;")
        time_layout.addRow("备注:", self.desc_input)

        self.form_layout.addWidget(self.time_group)

        # === 3. 底部按钮 ===
        btn_container = QWidget()
        btn_container.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(20, 15, 20, 15)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.Ok).setText("确定")
        self.buttons.button(QDialogButtonBox.Cancel).setText("取消")
        apply_dialog_theme(self, self.buttons)

        btn_layout.addStretch()
        btn_layout.addWidget(self.buttons)

        self.main_layout.addWidget(btn_container)

        if template_data:
            self.fill_from_template(template_data)

    def get_data(self):
        data = {
            "id": self.id_input.text().strip(),
            "initial_mass": self.mass_input.value(),
            "recipe": self.recipe_input.toPlainText().strip(),
            "key_variable": self.key_var_input.value(),
            "key_variable_name": self.key_var_name.text().strip(),
            "icon_emoji": self.icon_combo.currentText(),
            "date_prep": self.date_prep.text(),
            "date_complete": self.date_complete.text(),
            "date_demold": self.date_demold.text(),
            "date_test": self.date_test.text(),
            "description": self.desc_input.toPlainText().strip(),
            "shape": self.shape_combo.currentText()
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
        try:
            self.id_input.setText(f"{data.get('id', '')}_copy")
            emoji = data.get("icon_emoji", "🧪")
            idx = self.icon_combo.findText(emoji)
            if idx >= 0: self.icon_combo.setCurrentIndex(idx)

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

            self.recipe_input.setPlainText(data.get("recipe", ""))
            self.key_var_name.setText(data.get("key_variable_name", ""))
            try:
                self.key_var_input.setValue(float(data.get("key_variable", 0)))
            except:
                pass

            def set_time(w, t_str):
                if not t_str or t_str == "-": return
                dt = QDateTime.fromString(t_str, "yyyy-MM-dd-HH:00")
                if dt.isValid(): w.setDateTime(dt)

            set_time(self.date_prep, data.get("date_prep"))
            set_time(self.date_complete, data.get("date_complete"))
            set_time(self.date_demold, data.get("date_demold"))
            set_time(self.date_test, data.get("date_test"))

            self.desc_input.setPlainText(data.get("description", ""))

        except Exception as e:
            print(f"回填数据出错: {e}")


class EditSampleDialog(NewSampleDialog):
    def __init__(self, current_data, parent=None):
        super().__init__(parent, template_data=current_data)
        self.setWindowTitle("编辑试样信息")
        self.id_input.setText(current_data.get("id"))
        self.buttons.button(QDialogButtonBox.Ok).setText("保存修改")


# === NewProjectDialog (回退版，无模板) ===
class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.resize(400, 250)
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(15);
        layout.setContentsMargins(30, 30, 30, 30)

        form = QFormLayout();
        form.setVerticalSpacing(15)
        self.name_input = QLineEdit();
        self.name_input.setPlaceholderText("例如: 2025_砂柱实验")
        self.desc_input = QLineEdit();
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
        return {"name": self.name_input.text().strip(), "description": self.desc_input.text().strip()}


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