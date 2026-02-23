import time
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem, QListWidgetItem, QPushButton, QHeaderView, QStyleOptionButton, QHBoxLayout, QAbstractItemView, QSizePolicy, QApplication, QMessageBox, QFileDialog

from app.ui.modules.blender.b_launcher_ui import Ui_Form
from app.core.app_states import AppState
from app.utils.api.gazu.person import PersonServices
from app.utils.api.gazu.project import ProjectServices
from app.utils.api.gazu.shot import ShotServices
from app.utils.api.gazu.asset import AssetServices
from app.utils.api.gazu.task import TaskServices
from app.utils.subprocess import SubprocessServices
from app.utils.versioning import VersioningSystem
from app.utils.blender_functions import BlenderFunctions

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
        self.selected_path = None

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
        self.ui.listWidget_version.itemDoubleClicked.connect(self.on_widget_version_double_click)
        self.ui.toolButton_blenderPath.clicked.connect(self.on_select_blender)
        self.ui.pushButton_open.clicked.connect(self.on_open_selected_file)
        self.ui.pushButton_upMaster.clicked.connect(self.on_up_master)
        self.ui.pushButton_upVersion.clicked.connect(self.on_up_version)
        self.ui.pushButton_unlock.clicked.connect(self.on_unlock_file)
        self.ui.radioButton_showMaster.toggled.connect(lambda checked: self.load_version(checked))

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

    def on_widget_version_double_click(self, item: QListWidgetItem):
        version_name = item.text()
        version_path = item.data(Qt.ItemDataRole.UserRole)
        self.load_version_metadata(version_name, version_path)

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

    def load_latest_log(self, file_path: str = None):
        if self.selected_item is None:
            return

        asset_data = self.selected_item

        base_path = [i for i in self.paths if i["entity_type_id"] == asset_data["asset_type_id"]]
        master_path = Path(f"{base_path[0].get("description", "")}/{asset_data["name"]}")

        file_log = VersioningSystem.get_latest_log(master_path, file_path)
        if file_log:
            timestamp = file_log.get("date")
            file_log["date"] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M') if timestamp else "N/A"
            author = file_log.get("author")
            file_log["author"] = f"{PersonServices.get_person_by_id(author).get("first_name", "")} {PersonServices.get_person_by_id(author).get("last_name", "")}"
            file_log["locked"] = str(file_log["locked"])
        return file_log

    def metadata_table(self, custom_field_map: dict = None, custom_asset_data: dict = None):
        if self.selected_item is None:
            return

        asset_data = self.selected_item

        file_log = self.load_latest_log()
        if file_log:
            asset_data["date"] = file_log["date"]
            asset_data["author"] = file_log["author"]
            asset_data["locked"] = file_log["locked"]

        metadata_model = QStandardItemModel()
        metadata_model.setHorizontalHeaderLabels(["Key", "Value"])

        metadata_field_map = {
            "name": "Name",
            "status": "Status",
            "asset_type_name": "Type",
            "locked": "Locked",
            "date": "Date",
            "author": "Author",
        }
        if custom_field_map:
            metadata_field_map = custom_field_map
        if custom_asset_data:
            asset_data = custom_asset_data

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

        self.ui.tableView_metadata.setModel(metadata_model)
        self.ui.tableView_metadata.setWordWrap(True)
        
    def load_metadata(self, asset_id):
        if asset_id is None:
            return

        if self.ui.comboBox_entity.currentIndex() == 1:
            asset_data = AssetServices.get_asset_by_id(asset_id)
            asset_tasks = TaskServices.get_tasks_by_asset_id(asset_id)
            self.selected_item = asset_data

            self.metadata_table()

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

            self.ui.tableView_task.setModel(task_model)
            self.ui.tableView_task.setWordWrap(True)

        self.load_version()

    def load_version(self, show_master: bool = False):
        self.ui.listWidget_version.clear()
        base_path = [i for i in self.paths if i["entity_type_id"] == self.selected_item["asset_type_id"]]
        master_path = Path(f"{base_path[0].get("description", "")}/{self.selected_item["name"]}")
        version_folder = VersioningSystem.get_version_folder(master_path)
        version_info_list = VersioningSystem.get_version_info_list(version_folder)
        if show_master:
            master_item = QListWidgetItem("Master")
            master_item.setData(Qt.ItemDataRole.UserRole, f"{master_path}/{self.selected_item["name"]}.blend" )
            self.ui.listWidget_version.addItem(master_item)
        for version_info in version_info_list:
            item = QListWidgetItem(version_info["version"])
            item.setData(Qt.ItemDataRole.UserRole, version_info["full_path"])
            self.ui.listWidget_version.addItem(item)
        self.selected_path = f"{master_path}/{self.selected_item["name"]}.blend"

    def load_version_metadata(self, version_name: str, version_path: str):
        if self.selected_item is None:
            return

        self.selected_path = version_path

        if self.ui.comboBox_entity.currentIndex() == 1:
            custom_field_map = {
                "name": "Name",
                "status": "Status",
                "asset_type_name": "Type",
                "version": "Version",
                "date": "Date",
                "author": "Author",
                "locked": "Locked",
            }
            custom_asset_data = {
                    "name": self.selected_item["name"],
                    "status": self.selected_item["status"],
                    "asset_type_name": self.selected_item["asset_type_name"],
                    "version": version_name,
            }
            file_log = self.load_latest_log(version_path)
            if file_log:
                custom_asset_data.update({
                    "date": file_log["date"],
                    "author": file_log["author"],
                    "locked": file_log["locked"],
                })  
            self.metadata_table(custom_field_map=custom_field_map, custom_asset_data=custom_asset_data)

    def on_open_selected_file(self):     
        file_path = Path(self.selected_path)
        if (self.load_latest_log(file_path) or {}).get("locked", "").lower() == "true":
            print("locked")
            return
        
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_path is None or not blender_program:
            print("no path")
            return

        print("pass")

        base_path = [i for i in self.paths if i["entity_type_id"] == self.selected_item["asset_type_id"]]
        master_path = Path(f"{base_path[0].get("description", "")}/{self.selected_item["name"]}")

        if self.ui.comboBox_entity.currentIndex() == 1:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if not file_path.exists():
                model = self.ui.tableView_metadata.model()
                version_value = ""
                for row in range(model.rowCount()):
                    if str(model.index(row, 0).data()).strip().lower() == "version":
                        version_value = str(model.index(row, 1).data()).strip()
                        break
                if version_value in [None, "", "Master"]:
                    init_version_path = VersioningSystem.get_init_version_path(file_path)
                    init_version_path.parent.mkdir(parents=True, exist_ok=True)
                    create_script = f"import bpy; bpy.ops.wm.save_as_mainfile(filepath='{file_path}'); bpy.ops.wm.save_as_mainfile(filepath='{init_version_path}')"
                    SubprocessServices.run_command([blender_program, "-b", "--python-expr", create_script])
                    VersioningSystem.init_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))
                    file_path = init_version_path
                    VersioningSystem.init_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))
                else:
                    create_script = f"import bpy; bpy.ops.wm.save_as_mainfile(filepath='{file_path}')"
                    SubprocessServices.run_command([blender_program, "-b", "--python-expr", create_script])
                    VersioningSystem.init_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))

        SubprocessServices.popen_command_with_callback([blender_program, file_path], callback=self.on_blender_close)
        VersioningSystem.update_log(base_path=str(master_path), file_path=str(file_path), locked=True, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))

    def on_blender_close(self):
        base_path = [i for i in self.paths if i["entity_type_id"] == self.selected_item["asset_type_id"]]
        master_path = Path(f"{base_path[0].get("description", "")}/{self.selected_item["name"]}")
        file_path = Path(self.selected_path)
        if self.load_latest_log(file_path).get("locked", False):
            VersioningSystem.update_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))

    def on_up_master(self):
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_item is None or not blender_program:
            return

        if self.ui.listWidget_version.currentItem() is None:
            return

        base_path = [i for i in self.paths if i["entity_type_id"] == self.selected_item["asset_type_id"]]
        master_path = Path(f"{base_path[0].get("description", "")}/{self.selected_item["name"]}")

        if self.ui.comboBox_entity.currentIndex() == 1:
            version_selected = self.ui.listWidget_version.currentItem()
            script, version_path, master_blend_path = BlenderFunctions.up_master(version_selected.data(Qt.ItemDataRole.UserRole))
            print(script)
            SubprocessServices.run_command([blender_program, "-b", "--python-expr", script])
            VersioningSystem.init_log(base_path=str(master_path), file_path=str(version_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))
            VersioningSystem.update_log(base_path=str(master_path), file_path=str(master_blend_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))
    
    def on_up_version(self):
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_item is None or not blender_program:
            return

        base_path = [i for i in self.paths if i["entity_type_id"] == self.selected_item["asset_type_id"]]
        master_path = Path(f"{base_path[0].get("description", "")}/{self.selected_item["name"]}")

        if self.ui.comboBox_entity.currentIndex() == 1:
            version_selected = self.ui.listWidget_version.currentItem()
            script, version_path = BlenderFunctions.up_version(version_selected.data(Qt.ItemDataRole.UserRole))
            SubprocessServices.run_command([blender_program, "-b", "--python-expr", script])
            VersioningSystem.init_log(base_path=str(master_path), file_path=str(version_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))

    def on_unlock_file(self):
        base_path = [i for i in self.paths if i["entity_type_id"] == self.selected_item["asset_type_id"]]
        master_path = Path(f"{base_path[0].get("description", "")}/{self.selected_item["name"]}")
        file_path = Path(self.selected_path)
        if self.load_latest_log(file_path).get("locked", False):
            VersioningSystem.update_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=AppState().user_data.get("user", "").get("id", ""))

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