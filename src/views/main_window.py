import os
import json
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QSplitter, QTreeWidget, QTreeWidgetItem,
                               QToolBar, QMessageBox, QMenu, QInputDialog, QStyle, QFrame, QApplication,
                               QAbstractItemView)
from PySide6.QtGui import QAction, QIcon, QColor, QPalette, QDrag, QPixmap, QPainter, QFont
from PySide6.QtCore import Qt, QSize, QMimeData

from src.controllers.file_manager import FileManager
import config
from src.views.dialogs import NewProjectDialog, NewSampleDialog, BatchCopyWeightDialog
from src.views.sample_view import SampleDetailView

# 已删除: from src.views.analysis_dialog import AnalysisDialog


class FileTreeWidget(QTreeWidget):
    def __init__(self, parent=None, file_manager=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        super().dropEvent(event)
        if self.file_manager:
            new_structure = {}
            root = self.invisibleRootItem()
            project_count = root.childCount()
            for i in range(project_count):
                project_item = root.child(i)
                project_name = project_item.text(0)
                samples = []
                sample_count = project_item.childCount()
                for j in range(sample_count):
                    sample_item = project_item.child(j)
                    if sample_item.data(0, Qt.UserRole) == "sample":
                        samples.append(sample_item.text(0))
                new_structure[project_name] = samples
            self.file_manager.update_structure_order(new_structure)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_manager = FileManager()
        self.setWindowTitle(" 试样记录管理中心 v.1.2.0")

        self.resize(1200, 800)
        self.center_on_screen()

        # === 工具栏 ===
        toolbar = QToolBar("MainToolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar { background: white; border-bottom: 1px solid #e0e0e0; padding: 5px; spacing: 10px; }
            QToolButton { background: transparent; border-radius: 4px; padding: 5px 10px; font-weight: bold; color: #555; }
            QToolButton:hover { background-color: #f0f2f5; color: #3498db; }
        """)
        self.addToolBar(toolbar)

        new_proj_action = QAction("📁 新建项目", self)
        new_proj_action.triggered.connect(self.on_new_project)
        toolbar.addAction(new_proj_action)

        new_sample_action = QAction("🧪 新建试样", self)
        new_sample_action.triggered.connect(self.on_new_sample)
        toolbar.addAction(new_sample_action)

        # 已删除: AI 分析按钮及分隔符

        # === 主界面 ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #dcdfe6; }")

        # === 左侧 ===
        self.project_tree = FileTreeWidget(file_manager=self.file_manager)
        self.project_tree.setHeaderHidden(True)
        self.project_tree.setMinimumWidth(220)
        self.project_tree.setIconSize(QSize(24, 24))
        self.project_tree.setIndentation(20)
        self.project_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.project_tree.itemClicked.connect(self.on_item_selected)

        self.project_tree.setStyleSheet("""
            QTreeWidget { background-color: #2c3e50; color: #ecf0f1; border: none; padding-top: 10px; font-size: 13px; }
            QTreeWidget::item { height: 35px; padding-left: 5px; border-radius: 4px; margin: 2px 5px; }
            QTreeWidget::item:hover { background-color: #34495e; }
            QTreeWidget::item:selected { background-color: #3498db; color: white; }
        """)

        # === 右侧 ===
        self.detail_view = SampleDetailView(self.file_manager)
        self.detail_view.require_refresh.connect(self.refresh_data)

        splitter.addWidget(self.project_tree)
        splitter.addWidget(self.detail_view)
        splitter.setSizes([220, 980])
        main_layout.addWidget(splitter)
        self.refresh_data()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def _create_emoji_icon(self, emoji_char):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        font = QFont("Segoe UI Emoji", 24)
        if not font.exactMatch(): font = QFont("Apple Color Emoji", 24)

        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji_char)
        painter.end()
        return QIcon(pixmap)

    def refresh_data(self):
        expanded_items = set()
        root = self.project_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.isExpanded():
                expanded_items.add(item.text(0))

        self.project_tree.clear()
        data = self.file_manager.get_project_structure()

        for project_name, samples in data.items():
            project_item = QTreeWidgetItem(self.project_tree, [project_name])
            project_item.setData(0, Qt.UserRole, "project")
            project_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
            project_item.setFlags(project_item.flags() | Qt.ItemIsDropEnabled)
            font = project_item.font(0);
            font.setBold(True);
            font.setPointSize(10);
            project_item.setFont(0, font)

            if project_name in expanded_items: project_item.setExpanded(True)

            for sample_name in samples:
                sample_item = QTreeWidgetItem(project_item, [sample_name])
                sample_item.setData(0, Qt.UserRole, "sample")
                sample_item.setFlags(sample_item.flags() & ~Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)

                # 读取 JSON 获取 Emoji
                emoji_icon = None
                try:
                    json_path = os.path.join(config.DATA_ROOT, project_name, sample_name, "sample_info.json")
                    if os.path.exists(json_path):
                        with open(json_path, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            emoji_char = info.get("icon_emoji", "🧪")
                            emoji_icon = self._create_emoji_icon(emoji_char)
                except:
                    pass

                if emoji_icon:
                    sample_item.setIcon(0, emoji_icon)
                else:
                    sample_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))

            project_item.setExpanded(True)

    def on_item_selected(self, item, column):
        item_type = item.data(0, Qt.UserRole)
        name = item.text(0)
        if item_type == "sample":
            project_name = item.parent().text(0)
            self.detail_view.load_sample(project_name, name)
        else:
            self.detail_view.show_welcome(name)

    def show_tree_context_menu(self, pos):
        item = self.project_tree.itemAt(pos)
        if not item: return
        item_type = item.data(0, Qt.UserRole)
        name = item.text(0)
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: white; border: 1px solid #ddd; } QMenu::item { padding: 5px 20px; } QMenu::item:selected { background: #3498db; color: white; }")

        if item_type == "project":
            rename = QAction("✏️ 重命名项目", self);
            rename.triggered.connect(lambda: self.rename_project_ui(name));
            menu.addAction(rename)
            delete = QAction("🗑️ 删除项目", self);
            delete.triggered.connect(lambda: self.delete_project_ui(name));
            menu.addAction(delete)
        elif item_type == "sample":
            project_name = item.parent().text(0)

            copy_action = QAction("📄 复制参数新建", self)
            copy_action.triggered.connect(lambda: self.copy_sample_ui(project_name, name))
            menu.addAction(copy_action)

            batch_copy_w = QAction("📊 批量应用质量记录...", self)
            batch_copy_w.triggered.connect(lambda: self.open_batch_weight_ui(project_name, name))
            menu.addAction(batch_copy_w)

            menu.addSeparator()

            rename = QAction("✏️ 重命名试样", self);
            rename.triggered.connect(lambda: self.rename_sample_ui(project_name, name));
            menu.addAction(rename)
            delete = QAction("🗑️ 删除试样", self);
            delete.triggered.connect(lambda: self.delete_sample_ui(project_name, name));
            menu.addAction(delete)

        menu.exec(self.project_tree.mapToGlobal(pos))

    # 已删除: on_open_ai_analysis 方法

    def copy_sample_ui(self, project_name, sample_id):
        source_data = self.file_manager.get_sample_info(project_name, sample_id)
        if not source_data: return
        dialog = NewSampleDialog(self, template_data=source_data)
        if dialog.exec():
            d = dialog.get_data()
            if d["id"]:
                if self.file_manager.create_sample(project_name, d["id"], d):
                    self.refresh_data()
                    self.statusBar().showMessage(f"试样 {d['id']} 创建成功 (复制自 {sample_id})")
                else:
                    QMessageBox.warning(self, "错误", f"创建失败，可能编号 {d['id']} 已存在")

    def open_batch_weight_ui(self, project_name, source_id):
        structure = self.file_manager.get_project_structure()
        all_samples = structure.get(project_name, [])
        if len(all_samples) <= 1:
            QMessageBox.information(self, "提示", "该项目下没有其他试样可供复制。")
            return
        dialog = BatchCopyWeightDialog(source_id, all_samples, self)
        if dialog.exec():
            data = dialog.get_data()
            target_ids = data["target_ids"]
            overwrite = data["overwrite"]
            if not target_ids: return
            count = self.file_manager.batch_copy_weights(project_name, source_id, target_ids, overwrite)
            if self.detail_view.current_project == project_name and self.detail_view.current_sample in target_ids:
                self.detail_view.load_sample(project_name, self.detail_view.current_sample)
            QMessageBox.information(self, "完成", f"成功将质量记录应用到了 {count} 个试样。")

    def rename_project_ui(self, old_name):
        new_name, ok = QInputDialog.getText(self, "重命名项目", "请输入新项目名:", text=old_name)
        if ok and new_name and new_name != old_name:
            if self.file_manager.rename_project(old_name, new_name):
                self.refresh_data()
            else:
                QMessageBox.warning(self, "错误", "重命名失败")

    def delete_project_ui(self, name):
        if QMessageBox.question(self, "确认", f"删除项目 {name}？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if self.file_manager.delete_project(name): self.refresh_data(); self.detail_view.show_welcome()

    def rename_sample_ui(self, p_name, old_id):
        new_id, ok = QInputDialog.getText(self, "重命名试样", "新编号:", text=old_id)
        if ok and new_id != old_id:
            if self.file_manager.rename_sample(p_name, old_id, new_id):
                self.refresh_data()
                if self.detail_view.current_sample == old_id: self.detail_view.load_sample(p_name, new_id)

    def delete_sample_ui(self, p_name, s_id):
        if QMessageBox.question(self, "确认", f"删除试样 {s_id}？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if self.file_manager.delete_sample(p_name, s_id):
                self.refresh_data()
                if self.detail_view.current_sample == s_id: self.detail_view.show_welcome()

    def on_new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec():
            d = dialog.get_data()
            if d["name"] and self.file_manager.create_project(d["name"], d["description"]):
                self.refresh_data()
                self.statusBar().showMessage(f"项目 {d['name']} 创建成功")

    def on_new_sample(self):
        item = self.project_tree.currentItem()
        if not item: return
        p_name = item.parent().text(0) if item.data(0, Qt.UserRole) == "sample" else item.text(0)
        dialog = NewSampleDialog(self)
        if dialog.exec():
            d = dialog.get_data()
            if d["id"] and self.file_manager.create_sample(p_name, d["id"], d):
                self.refresh_data()
                self.statusBar().showMessage(f"试样 {d['id']} 创建成功")