from pathlib import Path

from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem, QListWidgetItem, QPushButton, QHeaderView, QStyleOptionButton, QHBoxLayout, QAbstractItemView, QSizePolicy, QApplication, QMessageBox, QFileDialog

from app.ui.modules.blender.b_launcher_ui import Ui_Form
from app.utils.api.gazu.person import PersonServices
from app.utils.api.gazu.project import ProjectServices
from app.utils.api.gazu.shot import ShotServices
from app.utils.api.gazu.asset import AssetServices
from app.utils.api.gazu.task import TaskServices
from app.utils.subprocess import SubprocessServices

class HandleBLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.entities = [
            {"name": "Assets"}, 
            # {"name": "Shots"}
            ]
        self.departments = []
        self.projects = []
        self.sequences = []
        self.shots = []
        self.paths = []
        self.assets = []
        self.asset_types = []

        self.selected_item = None

        self.load_departments() 
        self.mount_function()
        self.wire_search_list()


    def mount_function(self):
        self.ui.comboBox_department.currentIndexChanged.connect(self.on_department_change)
        self.ui.comboBox_project.currentIndexChanged.connect(self.on_project_change)
        self.ui.comboBox_entity.currentIndexChanged.connect(self.on_entity_change)
        self.ui.comboBox_episode.currentIndexChanged.connect(self.on_episode_change)
        self.ui.comboBox_type.currentIndexChanged.connect(self.on_asset_type_change)
        self.ui.listWidget_list.itemDoubleClicked.connect(self.on_widget_list_double_click)
        self.ui.toolButton_blenderPath.clicked.connect(self.on_select_blender)
        self.ui.pushButton_open.clicked.connect(self.open_selected_file)

    def load_departments(self):
        departments = PersonServices.get_departments()
        self.departments = departments

        self.ui.comboBox_department.clear()
        self.ui.comboBox_department.addItem("--- Select Department ---", None)
        for department in departments:
            self.ui.comboBox_department.addItem(department["name"], department["id"])

        self.ui.comboBox_project.setEnabled(False)
        self.ui.comboBox_entity.setEnabled(False)
        self.ui.comboBox_episode.setEnabled(False)
        self.ui.comboBox_type.setEnabled(False)

    def on_department_change(self):
        projects = ProjectServices.get_projects()
        self.projects = projects

        self.ui.comboBox_project.clear()
        self.ui.comboBox_project.addItem("--- Select Project ---", None)
        for project in projects:
            self.ui.comboBox_project.addItem(project["name"], project["id"])

        self.ui.comboBox_project.setEnabled(True)
        self.ui.comboBox_entity.setEnabled(False)
        self.ui.comboBox_episode.setEnabled(False)
        self.ui.comboBox_type.setEnabled(False)

    def on_project_change(self):
        self.ui.comboBox_entity.clear()
        self.ui.comboBox_entity.addItem("--- Select Entity ---", None)
        self.ui.comboBox_entity.addItems([entity["name"] for entity in self.entities])

        self.ui.comboBox_entity.setEnabled(True)
        self.ui.comboBox_episode.setEnabled(False)
        self.ui.comboBox_type.setEnabled(False)
    
    def on_entity_change(self):
        project_id = self.ui.comboBox_project.currentData()
        if project_id is None:
            self.ui.comboBox_episode.clear()
            self.ui.comboBox_episode.setEnabled(False)
            return

        episodes = ShotServices.get_episodes_by_project_id(project_id)
        self.ui.comboBox_episode.clear()
        self.ui.comboBox_episode.addItem("--- Select Episode ---", None)
        for episode in episodes:
            self.ui.comboBox_episode.addItem(episode["name"], episode["id"])

        entity = self.ui.comboBox_entity.currentIndex()
        self.ui.listWidget_list.clear()
        self.paths = []
        if entity == 1:
            self.load_assets()
            self.ui.label_type.setVisible(True)
            self.ui.comboBox_type.setVisible(True)
            self.ui.comboBox_type.setEnabled(True)
            self.ui.label_episode.setVisible(False)
            self.ui.comboBox_episode.setVisible(False)
            self.ui.comboBox_episode.setEnabled(False)
        elif entity == 2:
            self.load_sequence_and_shot()
            self.ui.label_type.setVisible(False)
            self.ui.comboBox_type.setVisible(False)
            self.ui.comboBox_type.setEnabled(False)
            self.ui.label_episode.setVisible(True)
            self.ui.comboBox_episode.setVisible(True)
            self.ui.comboBox_episode.setEnabled(True)

    # TODO: Implement episode change
    def on_episode_change(self):
        pass

    def on_asset_type_change(self):
        self.ui.listWidget_list.clear()
        asset_type_id = self.ui.comboBox_type.currentData()
        if asset_type_id is None:
            return

        for asset in self.assets:
            if asset["entity_type_id"] == asset_type_id:
                item = QListWidgetItem(asset["name"])
                item.setData(Qt.ItemDataRole.UserRole, asset["id"])
                self.ui.listWidget_list.addItem(item)

    def on_widget_list_double_click(self, item: QListWidgetItem):
        asset_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_metadata(asset_id)

    def on_select_blender(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Blender", "", "All Files (*)")
        if file_path:
            self.ui.lineEdit_blenderPath.setText(file_path)

    def load_assets(self):
        project_id = self.ui.comboBox_project.currentData()
        assets = AssetServices.get_assets_by_project_id(project_id)

        asset_types = AssetServices.get_asset_types_by_project_id(project_id)
        self.asset_types = asset_types

        self.ui.comboBox_type.clear()
        self.ui.comboBox_type.addItem("--- Select Type ---", None)
        for asset_type in asset_types:
            self.ui.comboBox_type.addItem(asset_type["name"], asset_type["id"])
        
        self.assets = []
        self.paths = []
        for asset in assets:
            if asset["name"].startswith("bpath-"):
                self.paths.append(asset)
                continue
            item = QListWidgetItem(asset["name"])
            item.setData(Qt.ItemDataRole.UserRole, asset["id"])
            self.ui.listWidget_list.addItem(item)
            self.assets.append(asset)

    # TODO: Load sequence and shot
    def load_sequence_and_shot(self):
        episode_id = self.ui.comboBox_episode.currentData()
        if episode_id is None:
            return

        sequences = ShotServices.get_sequences_by_episode_id(episode_id)
        self.sequences = sequences

        shots = ShotServices.get_shots_by_episode_id(episode_id)
        self.shots = shots

        self.ui.listWidget_sequence.clear()
        
    def load_metadata(self, asset_id):
        if asset_id is None:
            return

        if self.ui.comboBox_entity.currentIndex() == 1:
            asset_data = AssetServices.get_asset_by_id(asset_id)
            asset_tasks = TaskServices.get_tasks_by_asset_id(asset_id)
            self.selected_item = asset_data

            metadata_model = QStandardItemModel()
            metadata_model.setHorizontalHeaderLabels(["Key", "Value"])

            metadata_field_map = {
                "name": "Name",
                "status": "Status",
                "asset_type_name": "Type",
            }

            for key, label in metadata_field_map.items():
                key_value = asset_data.get(key, "")
                if key_value:
                    label = QStandardItem(label)
                    label.setEditable(False)
                    item = QStandardItem(key_value)
                    item.setEditable(False)
                    metadata_model.appendRow([
                        label,
                        item
                    ])

            task_model = QStandardItemModel()
            task_model.setHorizontalHeaderLabels(["Name", "Status"])

            task_field_map = {
                "task_type_name": "task_status_name",
            }

            for name, status in task_field_map.items():
                for task in asset_tasks:
                    task_type_name = task.get(name, "")
                    task_status_name = task.get(status, "")
                    if task_type_name and task_status_name:
                        item_name = QStandardItem(task_type_name)
                        item_name.setEditable(False)
                        item_status = QStandardItem(task_status_name)
                        item_status.setEditable(False)
                        task_model.appendRow([
                            item_name,
                            item_status
                        ])

            self.ui.tableView_metadata.setModel(metadata_model)
            self.ui.tableView_task.setModel(task_model)

            self.ui.tableView_metadata.setWordWrap(True)
            self.ui.tableView_task.setWordWrap(True)
            
    def open_selected_file(self):
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_item is None or not blender_program:
            return

        if self.ui.comboBox_entity.currentIndex() == 1:
            base_path = [i for i in self.paths if i["entity_type_id"] == self.selected_item["asset_type_id"]]
            if not base_path:
                return
            file_path = Path(f"{base_path[0].get("description", "")}/{self.selected_item["name"]}/{self.selected_item["name"]}.blend")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if not file_path.exists():
                create_script = f"import bpy; bpy.ops.wm.save_as_mainfile(filepath='{file_path}')"
                SubprocessServices.run_command([blender_program, "-b", "--python-expr", create_script])

        SubprocessServices.popen_command([blender_program, file_path])

    
    def wire_search_list(self):
        le = self.ui.lineEdit_list
        if le:
            le.textChanged.connect(self.filter_list)

    def filter_list(self, text: str):
        lw = self.ui.listWidget_list
        text_low = (text or "").lower().strip()
        for i in range(lw.count()):
            item = lw.item(i)
            item.setHidden(text_low not in item.text().lower())