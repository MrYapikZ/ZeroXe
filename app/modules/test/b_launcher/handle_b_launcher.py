import time
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import QWidget, QTreeWidgetItem, QListWidgetItem, QPushButton, QHeaderView, QStyleOptionButton, QHBoxLayout, QAbstractItemView, QSizePolicy, QApplication, QMessageBox, QFileDialog
from gazu import project

from app.config import Settings
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
from app.utils.path_builder import PathBuilder

class HandleBLauncherPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.entities = [
            {"name": "Assets"}, 
            {"name": "Shots"}
            ]
        self.departments = []
        self.projects = []
        self.sequences = []
        self.shots = []
        self.paths = []
        self.assets = []
        self.asset_types = []

        self.selected_item = {}
        self.selected_path = ""
        self.user_id = ""

        self.get_user_id()
        self.load_departments() 
        self.mount_function()
        self.wire_search_list()

        self.load_user_data()

    def load_user_data(self):
        user_data = Settings().read_user_data()
        if user_data and user_data.get("blender_path", None):
            self.ui.lineEdit_blenderPath.setText(user_data["blender_path"])
        else:
            self.on_select_blender()

    def get_user_id(self):
        if AppState().user_data is None:
            QMessageBox.warning(self, "Warning", "User data not found. Please log in again.")
            return
        user_data = AppState().user_data or {}
        user_dict = user_data.get("user", {}) or {}
        user_id = user_dict.get("id", "")
        self.user_id = user_id

    # region ui trigger
    def mount_function(self):
        self.ui.comboBox_department.currentIndexChanged.connect(self.on_department_change)
        self.ui.comboBox_project.currentIndexChanged.connect(self.on_project_change)
        self.ui.comboBox_entity.currentIndexChanged.connect(self.on_entity_change)
        self.ui.comboBox_episode.currentIndexChanged.connect(self.on_episode_change)
        self.ui.comboBox_type.currentIndexChanged.connect(self.on_asset_type_change)
        self.ui.listWidget_list.itemClicked.connect(self.on_widget_list_double_click)
        self.ui.listWidget_version.itemClicked.connect(self.on_widget_version_double_click)
        self.ui.toolButton_blenderPath.clicked.connect(self.on_select_blender)
        self.ui.pushButton_open.clicked.connect(self.on_open_selected_file)
        self.ui.pushButton_upMaster.clicked.connect(self.on_up_master)
        self.ui.pushButton_upVersion.clicked.connect(self.on_up_version)
        self.ui.pushButton_unlock.clicked.connect(self.on_unlock_file)
        self.ui.pushButton_replace.clicked.connect(self.on_replace_file)
        self.ui.radioButton_showMaster.toggled.connect(lambda checked: self.load_version(checked))

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
            if episode["name"].startswith("setting"):
                bpaths = ShotServices.get_shots_by_episode_id(episode["id"])
                asset_bpaths = AssetServices.get_assets_by_episode_id(episode["id"])
                self.paths = bpaths + asset_bpaths
                continue
            self.ui.comboBox_episode.addItem(episode["name"], episode["id"])

        entity = self.ui.comboBox_entity.currentIndex()
        self.ui.listWidget_list.clear()
        
        if entity == 1:
            self.load_assets()
            self.ui.label_type.setVisible(True)
            self.ui.comboBox_type.setVisible(True)
            self.ui.comboBox_type.setEnabled(True)
            self.ui.label_episode.setVisible(False)
            self.ui.comboBox_episode.setVisible(False)
            self.ui.comboBox_episode.setEnabled(False)
        elif entity == 2:
            self.ui.label_type.setVisible(False)
            self.ui.comboBox_type.setVisible(False)
            self.ui.comboBox_type.setEnabled(False)
            self.ui.label_episode.setVisible(True)
            self.ui.comboBox_episode.setVisible(True)
            self.ui.comboBox_episode.setEnabled(True)

    def on_episode_change(self):
        self.load_sequence_and_shot()

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
        if self.ui.comboBox_entity.currentIndex() == 1:
            asset_id = item.data(Qt.ItemDataRole.UserRole)
            self.load_metadata(asset_id)
        elif self.ui.comboBox_entity.currentIndex() == 2:
            shot_data = item.data(Qt.ItemDataRole.UserRole)
            self.load_metadata(shot_data["shot_id"])

    def on_widget_version_double_click(self, item: QListWidgetItem):
        version_name = item.text()
        version_path = item.data(Qt.ItemDataRole.UserRole)
        self.load_version_metadata(version_name, version_path)

    def on_select_blender(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Blender", "", "All Files (*)")
        if file_path:
            self.ui.lineEdit_blenderPath.setText(file_path)
            Settings().update_user_field(key="blender_path", value=file_path)

    def on_open_selected_file(self):
        if self.selected_path is None:
            return
        file_path = Path(self.selected_path)
        if (self.load_latest_log(str(file_path)) or {}).get("locked", "").lower() == "true":
            QMessageBox.warning(self, "Warning", "This file is locked.")
            return
        
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_path is None or not blender_program:
            QMessageBox.warning(self, "Warning", "Please select a path and blender program.")
            return

        asset_data = self.selected_item
        if asset_data is None:
            QMessageBox.warning(self, "Warning", "Please select an item.")
            return
        
        master_path, _ = self.shot_or_asset_path()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            model = self.ui.tableView_metadata.model()
            version_value = ""
            if model is not None:
                for row in range(model.rowCount()):
                    if str(model.index(row, 0).data()).strip().lower() == "version":
                        version_value = str(model.index(row, 1).data()).strip()
                        break
            if version_value in [None, "", "Master"]:
                self.create_and_replace_file()
            else:
                create_script = f"import bpy; bpy.ops.wm.save_as_mainfile(filepath='{file_path}')"
                SubprocessServices.run_command([blender_program, "-b", "--python-expr", create_script])
                VersioningSystem.init_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=self.user_id)

        SubprocessServices.popen_command_with_callback([blender_program, file_path], callback=self.on_blender_close)
        VersioningSystem.update_log(base_path=str(master_path), file_path=str(file_path), locked=True, timestamp=time.time(), author=self.user_id)
        self.reload_version_metadata()

    def on_blender_close(self):
        if self.selected_item is None:
            return
        master_path, _ = self.shot_or_asset_path()
        file_path = Path(str(self.selected_path))
        logs = self.load_latest_log(str(file_path))
        if logs and logs.get("locked", False):
            VersioningSystem.update_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=self.user_id)
        self.reload_version_metadata()

    def on_up_master(self):
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_item is None or not blender_program:
            return

        if self.ui.listWidget_version.currentItem() is None:
            return

        master_path, _ = self.shot_or_asset_path()

        version_selected = self.ui.listWidget_version.currentItem()
        if version_selected is None:
            QMessageBox.warning(self, "Warning", "Please select a version to up master.")
            return
        if self.ui.comboBox_department.currentText().lower().startswith("animation"):
            presets = [p for p in self.paths if
                       p.get("name", "").lower().startswith("preset-") and p.get("name", "").lower().endswith("bake_animation")]
            preset = presets[0].get("description", "") if presets else ""
            script, master_blend_path = BlenderFunctions.up_master(version_selected.data(Qt.ItemDataRole.UserRole), {"script": preset})
        else:
            script, master_blend_path = BlenderFunctions.up_master(version_selected.data(Qt.ItemDataRole.UserRole))
        SubprocessServices.run_command([blender_program, "-b", "--python-expr", script])
        VersioningSystem.update_log(base_path=str(master_path), file_path=str(master_blend_path), locked=False, timestamp=time.time(), author=self.user_id)
        self.reload_version_metadata()
        self.load_version(show_master=self.ui.radioButton_showMaster.isChecked())
        QMessageBox.information(self, "Info", "Successfully up master.")

    def on_up_version(self):
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_item is None or not blender_program:
            return

        master_path, _ = self.shot_or_asset_path()
        
        version_selected = self.ui.listWidget_version.currentItem()
        if version_selected is None:
            QMessageBox.warning(self, "Warning", "Please select a version to upversion.")
            return 
        script, version_path = BlenderFunctions.up_version(version_selected.data(Qt.ItemDataRole.UserRole))
        SubprocessServices.run_command([blender_program, "-b", "--python-expr", script])
        VersioningSystem.init_log(base_path=str(master_path), file_path=str(version_path), locked=False, timestamp=time.time(), author=self.user_id)
        self.reload_version_metadata()
        self.load_version(show_master=self.ui.radioButton_showMaster.isChecked())
        QMessageBox.information(self, "Info", "Successfully up version.")

    def on_unlock_file(self):
        master_path, _ = self.shot_or_asset_path()
        file_path = Path(str(self.selected_path))
        logs = self.load_latest_log(str(file_path))
        if logs and logs.get("locked", False):
            VersioningSystem.update_log(base_path=str(master_path), file_path=str(file_path), locked=False, timestamp=time.time(), author=self.user_id)
            QMessageBox.information(self, "Info", "Successfully unlock file.")
        else:
            QMessageBox.warning(self, "Warning", "Please select a version to unlock.")
        self.reload_version_metadata()

    def on_replace_file(self):
        reply = QMessageBox.question(self, "Confirm Replace", "Are you sure you want to replace the master file with this version?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.create_and_replace_file()
                QMessageBox.information(self, "Info", "Successfully replaced master file.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to replace master file: {str(e)}")
                
    # endregion

    # region populate data
    # Department dropdown
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
    
    # List widget for assets
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
        for asset in assets:
            if asset["name"].startswith("bpath-"):
                continue
            item = QListWidgetItem(asset["name"])
            item.setData(Qt.ItemDataRole.UserRole, asset["id"])
            self.ui.listWidget_list.addItem(item)
            self.assets.append(asset)

    # List widget for shots
    def load_sequence_and_shot(self):
        self.ui.listWidget_list.clear()
        episode_id = self.ui.comboBox_episode.currentData()
        if episode_id is None:
            return

        sequences = ShotServices.get_sequences_by_episode_id(episode_id)
        self.sequences = sequences

        shots = ShotServices.get_shots_by_episode_id(episode_id)
        self.shots = shots

        seq_lookup = {seq["id"]: seq["name"] for seq in sequences}
        for shot in shots:
            seq_name = seq_lookup.get(shot["parent_id"]) or ""
            shot_name = shot["name"]
            item_name = f"{seq_name}_{shot_name}"

            item = QListWidgetItem(item_name)
            item.setData(Qt.ItemDataRole.UserRole, {
                "sequence_id": shot["parent_id"],
                "shot_id": shot["id"],
                "sequence_name": seq_name,
                "shot_name": shot_name
            })
            self.ui.listWidget_list.addItem(item)

    # .zeroxe log data
    def load_latest_log(self, file_path: str | None = None):
        if self.selected_item is None:
            return

        master_path, full_path = self.shot_or_asset_path()

        if full_path and file_path is None:
            file_path = str(full_path)
        file_log = VersioningSystem.get_latest_log(str(master_path), file_path)
        if file_log:
            timestamp = file_log.get("date")
            file_log["date"] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M') if timestamp else "N/A"
            author = file_log.get("author")
            file_log["author"] = f"{PersonServices.get_person_by_id(author).get("first_name", "")} {PersonServices.get_person_by_id(author).get("last_name", "")}"
            file_log["locked"] = str(file_log["locked"])
        return file_log

    # Table view metadata
    def metadata_table(self, custom_field_map: dict | None = None, custom_item_data: dict | None = None):
        if self.selected_item is None:
            return

        item_data = self.selected_item

        file_log = self.load_latest_log()
        if file_log:
            item_data["date"] = file_log["date"]
            item_data["author"] = file_log["author"]
            item_data["locked"] = file_log["locked"]

        metadata_model = QStandardItemModel()
        metadata_model.setHorizontalHeaderLabels(["Key", "Value"])

        metadata_field_map = {
            "name": "Name",
            "status": "Status",
        }
        if self.ui.comboBox_entity.currentIndex() == 1:
            metadata_field_map["asset_type_name"] = "Type"
        metadata_field_map.update({
            "locked": "Locked",
            "date": "Date",
            "author": "Author",
        })
        if custom_field_map:
            metadata_field_map = custom_field_map
        if custom_item_data:
            item_data = custom_item_data

        for key, label in metadata_field_map.items():
            key_value = item_data.get(key, "")
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
    
    # Table view task and metadata trigger
    def load_metadata(self, asset_or_shot_id):
        if asset_or_shot_id is None:
            return

        if self.ui.comboBox_entity.currentIndex() == 1:
            asset_data = AssetServices.get_asset_by_id(asset_or_shot_id)
            asset_tasks = TaskServices.get_tasks_by_asset_id(asset_or_shot_id)
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
        elif self.ui.comboBox_entity.currentIndex() == 2:
            shot_data = ShotServices.get_shot_by_id(asset_or_shot_id)
            shot_tasks = TaskServices.get_tasks_by_shot_id(asset_or_shot_id)
            self.selected_item = shot_data

            self.metadata_table()

            task_model = QStandardItemModel()
            task_model.setHorizontalHeaderLabels(["Name", "Status"])

            task_field_map = {
                "task_type_name": "task_status_name",
            }

            for name, status in task_field_map.items():
                for task in shot_tasks:
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

    # List view version
    def load_version(self, show_master: bool = False):
        self.ui.listWidget_version.clear()
        if self.selected_item is None:
            return
        
        master_path, full_path = self.shot_or_asset_path()
        
        if self.ui.comboBox_entity.currentIndex() == 1:
            master_file_path = Path(master_path) / f"{self.selected_item['name']}.blend"
            if show_master:
                master_item = QListWidgetItem("Master")
                master_item.setData(Qt.ItemDataRole.UserRole, master_file_path)
                self.ui.listWidget_version.addItem(master_item)
            self.selected_path = str(master_file_path)
        elif self.ui.comboBox_entity.currentIndex() == 2:
            if show_master:
                master_item = QListWidgetItem("Master")
                master_item.setData(Qt.ItemDataRole.UserRole, full_path)
                self.ui.listWidget_version.addItem(master_item)
            self.selected_path = str(full_path)
        version_folder = VersioningSystem.get_version_folder(master_path)
        version_info_list = VersioningSystem.get_version_info_list(str(version_folder))
        for version_info in version_info_list:
            item = QListWidgetItem(version_info["version"])
            item.setData(Qt.ItemDataRole.UserRole, version_info["full_path"])
            self.ui.listWidget_version.addItem(item)
        self.ui.listWidget_list.sortItems()

    # Table view metadata for version
    def load_version_metadata(self, version_name: str, version_path: str):
        if self.selected_item is None:
            return

        self.selected_path = version_path

        custom_field_map, custom_asset_data = {}, {}
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
            
        elif self.ui.comboBox_entity.currentIndex() == 2:
            custom_field_map = {
                "name": "Name",
                "status": "Status",
                "department": "Department",
                "version": "Version",
                "date": "Date",
                "author": "Author",
                "locked": "Locked",
            }
            item = self.ui.listWidget_list.currentItem()
            custom_asset_data = {
                "name": item.text() if item else "Unknown",
                "status": self.selected_item["status"],
                "department": self.ui.comboBox_department.currentText(),
                "version": version_name,
            }
        file_log = self.load_latest_log(version_path)
        if file_log:
            custom_asset_data.update({
                "date": file_log["date"],
                "author": file_log["author"],
                "locked": file_log["locked"],
            })  
        self.metadata_table(custom_field_map=custom_field_map, custom_item_data=custom_asset_data)

    # Table view metadata refersh for version
    def reload_version_metadata(self):
        version_item = self.ui.listWidget_version.currentItem()
        version_name = "Master" if version_item is None else version_item.text()
        version_path = self.selected_path if version_item is None else version_item.data(Qt.ItemDataRole.UserRole)
        self.load_version_metadata(version_name, str(version_path))
    # endregion

    # TODO: Move path builder to dynamic
    # region Path builder
    # master path builder
    def build_shot_path(self, custom_department: str | None = None):
        selected = self.ui.listWidget_list.currentItem() # ui data sq and shot
        if selected is None:
            return "", ""
        
        item_data = selected.data(Qt.ItemDataRole.UserRole) # open sq and shot data
        
        selected_project_id = self.ui.comboBox_project.currentData() # ui data project id
        project = next((p for p in self.projects if p["id"] == selected_project_id), None)
        project_code = project.get("code") if project else None

        department_code = self.get_department_code(custom_department)
        
        episode_name = self.ui.comboBox_episode.currentText() # ui data episode

        base_path_list = [
            i for i in self.paths 
            if i["name"].lower().endswith(custom_department or self.ui.comboBox_department.currentText().lower()) # ui data
        ]
        if not base_path_list:
            return "", ""
        base_description = base_path_list[0].get("description", "")
        if not base_description:
            QMessageBox.warning(self, "Warning", "Base path description not found for the selected department.")
            return "", ""
        master_path = Path(base_description) / item_data.get("name", "")
        file_path = master_path / PathBuilder.build_shot_path(
            episode_name=episode_name,
            sequence_name=item_data.get("sequence_name", ""),
            shot_name=item_data.get("shot_name", "")
        )
        file_name = PathBuilder.build_shot_name(
            project_code=str(project_code) if project_code else "",
            episode_name=episode_name,
            sequence_name=item_data.get("sequence_name", ""),
            shot_name=item_data.get("shot_name", ""),
            department_code=department_code
        )
        return str(file_path), str(file_path / f"{file_name}.blend")
    
    def shot_or_asset_path(self, select: int = 0):
        asset_data = self.selected_item
        if asset_data is None:
            QMessageBox.warning(self, "Warning", "Please select an item.")
            return ""

        master_path, file_path = "", ""
        if self.ui.comboBox_entity.currentIndex() == 1 or select == 1:
            base_path = [i for i in self.paths if i["entity_type_id"] == asset_data["asset_type_id"]]
            master_path = Path(f"{base_path[0].get('description', '')}/{asset_data['name']}")
            file_path = master_path / f"{asset_data['name']}.blend"
        elif self.ui.comboBox_entity.currentIndex() == 2 or select == 2:
            master_path, file_path = self.build_shot_path()
        return str(master_path), str(file_path)
    
    def get_target_department_path(self, file_path):
        file_path = Path(file_path)
        stem = file_path.stem
        code = stem.split("_")[-1]
        department = next(
            (d for d in self.paths if d["data"].get("code", None) == code),
            None
        )
        target_code = department.get("data", {}).get("tcode") if department else ""
        if target_code == "init":
            return "", "", target_code
        target_department = self.get_department_by_code(target_code)
        # build shot path
        master_path, file_path = self.build_shot_path(target_department)
        return master_path, file_path, target_code
    # endregion

    # region Department code & path (no needed i think)
    def get_department_code(self, custom_department: str | None = None):
        selected_department = custom_department or self.ui.comboBox_department.currentText().lower()
        department = next(
            (d for d in self.paths if d["name"].lower().endswith(selected_department)), 
            None
        )
        department_code = ""
        if department:
            department_code = department.get("data", {}).get("code")
                
        return department_code

    def get_department_by_code(self, code: str | None = None):
        if not code:
            return None

        department = next(
            (d for d in self.paths if d.get("data", {}).get("code") == code),
            None
        )

        return department.get("name") if department else None
    # endregion
    
    # TODO: Move script builder to dynamic
    # region Script builder
    # region layout [DONE]
    def build_layout_file(self, file_path: str, version_path: str):
        selected_item = self.ui.listWidget_list.currentItem()
        if selected_item is None:
            return ""
        item_data = selected_item.data(Qt.ItemDataRole.UserRole)
        shot_data = [i for i in self.shots if i["id"] == item_data.get("shot_id")]
        if shot_data is None or len(shot_data) == 0:
            return ""
        
        char = [c.strip() for c in shot_data[0].get("data", {}).get("char", "").split(",") if c.strip()] if shot_data else []
        set = [s.strip() for s in shot_data[0].get("data", {}).get("set", "").split(",") if s.strip()] if shot_data else []
        prop = [p.strip() for p in shot_data[0].get("data", {}).get("prop", "").split(",") if p.strip()] if shot_data else []
        vehicle = [v.strip() for v in shot_data[0].get("data", {}).get("vehicle", "").split(",") if v.strip()] if shot_data else []

        frame_in = int(shot_data[0].get("data", {}).get("frame_in", "0"))
        frame_out = int(shot_data[0].get("data", {}).get("frame_out", "0"))
        fps = int(shot_data[0].get("data", {}).get("fps", "24"))

        res_str = str(shot_data[0].get("data", {}).get("resolution", "1920x1080"))
        resolution = [int(res.strip()) for res in res_str.split('x')] if 'x' in res_str else []

        project_id = self.ui.comboBox_project.currentData()
        # no need i just need the asset name
        assets = AssetServices.get_assets_by_project_id(project_id)
        
        char_assets = [a for a in assets if a["name"] in char]
        set_assets = [a for a in assets if a["name"] in set]
        prop_assets = [a for a in assets if a["name"] in prop]
        vehicle_assets = [a for a in assets if a["name"] in vehicle]
        
        collections = {}
        not_found_assets = []
        presets = [p for p in self.paths if p.get("name", "").lower().startswith("preset-") and p.get("name", "").lower().endswith((self.ui.comboBox_department.currentText() or "").lower())]
        # no need i can match by prefix
        for i in char_assets + set_assets + prop_assets + vehicle_assets:
            base_path = [j for j in self.paths if j["entity_type_id"] == i["entity_type_id"]]
            master_path = Path(f"{base_path[0].get('description', '')}/{i['name']}")
            asset_file_path = master_path / f"{i['name']}.blend"
            if not asset_file_path.exists():
                not_found_assets.append(i["name"])
                continue 
            # separate char, set, prop, vehicle
            base_name = base_path[0].get("name", "Unknown").replace("bpath-", "").lower()
            collections[base_name] = collections.get(base_name, []) + [str(asset_file_path)]

        setting_data = {
            "frame_in": frame_in,
            "frame_out": frame_out,
            "fps": fps,
            "resolution": resolution,
            "script": presets[0].get("description", "") if presets else "",
        }

        if not_found_assets:
            reply = QMessageBox.question(
                self,
                "Missing Assets",
                "The following assets were not found and will be skipped:\n\n"
                + "\n".join(not_found_assets)
                + "\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return ""
        create_script = BlenderFunctions.build_layout_script(filepath=file_path, version_path=version_path, collections=collections, setting_data=setting_data)
        return create_script
    # endregion

    def build_lighting_file(self, file_path: str, version_path: str):
        selected_item = self.ui.listWidget_list.currentItem()
        if selected_item is None:
            return ""
        item_data = selected_item.data(Qt.ItemDataRole.UserRole)
        shot_data = [i for i in self.shots if i["id"] == item_data.get("shot_id")]
        if shot_data is None or len(shot_data) == 0:
            return ""

        # Construct source and current department path
        anim_base_path = [p.get("description", "") for p in self.paths if p.get("name", "").lower().startswith("bpath-") and p.get("name", "").lower().endswith("animation")]
        lighting_base_path = [p.get("description", "") for p in self.paths if p.get("name", "").lower().startswith("bpath-") and p.get("name", "").lower().endswith("lighting")]
        # Get mastershot
        ms_lit_base_path = [p.get("description", "") for p in self.paths if p.get("name", "").lower().startswith("bpath-") and p.get("name", "").lower().endswith("ms_lit")]
        if not anim_base_path or not lighting_base_path or not ms_lit_base_path:
            QMessageBox.warning(self, "Warning", "Animation or Lighting or LIT base path not found for the selected department.")
            return ""
        lit_name = shot_data[0]["data"].get("ms_lit", "")
        if not lit_name:
            QMessageBox.warning(self, "Warning", "LIT name not found in shot data.")
            return ""
        lit_path = Path(ms_lit_base_path[0]) / lit_name / f"{lit_name}.blend"
        if not lit_path.exists():
            QMessageBox.warning(self, "Warning", f"LIT file not found: {lit_path}")
            return ""
        anim_department = [c.get("name", "") for c in self.paths if c.get("name", "").lower().startswith("bpath-") and c.get("name", "").lower().endswith("animation")]
        _, anim_path = self.build_shot_path(str(anim_department[0]))
        
        # Get addon preset
        blp_preset_base_path = [p.get("description", "") for p in self.paths if p.get("name", "").lower().startswith("bpath-") and p.get("name", "").lower().endswith("ops_blp")]
        blp_preset_path = Path(blp_preset_base_path[0]) / f"{lit_name}.json" if lit_name else None

        # Get lighting preset
        presets = [p for p in self.paths if
                   p.get("name", "").lower().startswith("preset-") and p.get("name", "").lower().endswith(
                       (self.ui.comboBox_department.currentText() or "").lower())]
        frame_in = int(shot_data[0].get("data", {}).get("frame_in", "0"))
        frame_out = int(shot_data[0].get("data", {}).get("frame_out", "0"))
        fps = int(shot_data[0].get("data", {}).get("fps", "24"))

        res_str = str(shot_data[0].get("data", {}).get("resolution", "1920x1080"))
        resolution = [int(res.strip()) for res in res_str.split('x')] if 'x' in res_str else []

        setting_data = {
            "frame_in": frame_in,
            "frame_out": frame_out,
            "fps": fps,
            "resolution": resolution,
            "ops_blp": str(blp_preset_path),
            "script": presets[0].get("description", "") if presets else "",
        }

        create_script = BlenderFunctions.build_lighting_script(filepath=str(file_path), version_path=str(version_path), animation_file=str(anim_path), master_file=str(lit_path), setting_data=setting_data)
        return create_script

    def build_comp_file(self, file_path: str, version_path: str):
        selected_item = self.ui.listWidget_list.currentItem()
        if selected_item is None:
            return ""
        item_data = selected_item.data(Qt.ItemDataRole.UserRole)
        shot_data = [i for i in self.shots if i["id"] == item_data.get("shot_id")]
        if shot_data is None or len(shot_data) == 0:
            return ""

        comp_base_path = [p.get("description", "") for p in self.paths if
                              p.get("name", "").lower().startswith("bpath-") and p.get("name", "").lower().endswith(
                                  "compositing")]
        ms_comp_base_path = [p.get("description", "") for p in self.paths if
                            p.get("name", "").lower().startswith("bpath-") and p.get("name", "").lower().endswith(
                                "ms_comp")]
        if not comp_base_path or not ms_comp_base_path:
            QMessageBox.warning(self, "Warning",
                                "Compositing or Compositing Master Shot base path not found for the selected department.")
            return ""
        ms_comp_name = shot_data[0]["data"].get("ms_comp", "")
        if not ms_comp_name:
            QMessageBox.warning(self, "Warning", "Compositing Master Shot name not found in shot data.")
            return ""
        ms_comp_path = Path(ms_comp_base_path[0]) / ms_comp_name / f"{ms_comp_name}.blend"
        if not ms_comp_path.exists():
            QMessageBox.warning(self, "Warning", f"Compositing Master Shot file not found: {ms_comp_path}")
            return ""

        presets = [p for p in self.paths if
                   p.get("name", "").lower().startswith("preset-") and p.get("name", "").lower().endswith(
                       (self.ui.comboBox_department.currentText() or "").lower())]
        frame_in = int(shot_data[0].get("data", {}).get("frame_in", "0"))
        frame_out = int(shot_data[0].get("data", {}).get("frame_out", "0"))
        fps = int(shot_data[0].get("data", {}).get("fps", "24"))

        res_str = str(shot_data[0].get("data", {}).get("resolution", "1920x1080"))
        resolution = [int(res.strip()) for res in res_str.split('x')] if 'x' in res_str else []

        setting_data = {
            "frame_in": frame_in,
            "frame_out": frame_out,
            "fps": fps,
            "resolution": resolution,
            "script": presets[0].get("description", "") if presets else "",
        }

        create_script = BlenderFunctions.build_comp_script(filepath=str(file_path), version_path=str(version_path), master_file=str(ms_comp_path), setting_data=setting_data)
        return create_script

    #endregion
   
    def create_and_replace_file(self):
        file_path = Path(self.selected_path)
        if (self.load_latest_log(str(file_path)) or {}).get("locked", "").lower() == "true":
            QMessageBox.warning(self, "Warning", "This file is locked.")
            return
        blender_program = self.ui.lineEdit_blenderPath.text().strip()
        if self.selected_path is None or not blender_program:
            QMessageBox.warning(self, "Warning", "Please select a path and blender program.")
            return
        master_path, _ = self.shot_or_asset_path()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # generate version
        init_version_path = VersioningSystem.get_init_version_path(str(file_path))
        init_version_path.parent.mkdir(parents=True, exist_ok=True)
        
        # region TODO: Move file maker to dynamic
        # find source path (like anm > blk)
        target_master_path, target_file_path, target = self.get_target_department_path(str(file_path))
        department_code = self.get_department_code()
        create_script = f"import bpy; bpy.ops.wm.save_as_mainfile(filepath='{file_path}'); bpy.ops.wm.save_as_mainfile(filepath='{init_version_path}')"
        # Layout [DONE]
        if target == "init":
            create_script = self.build_layout_file(file_path=str(file_path), version_path=str(init_version_path))
        # Lighting
        elif target == "anm" and department_code == "lgt":
            create_script = self.build_lighting_file(file_path=str(file_path), version_path=str(init_version_path))
        # Compositing
        elif department_code == "comp":
            create_script = self.build_comp_file(file_path=str(file_path), version_path=str(init_version_path))
        # Blocking and Animation [DONE]
        elif target != "init" and target_master_path and target_file_path:
            start_script = f"import bpy; import os; bpy.ops.wm.open_mainfile(filepath='{target_file_path}'); bpy.ops.wm.save_as_mainfile(filepath='{init_version_path}');"
            end_script = f"bpy.ops.wm.save_as_mainfile(filepath='{file_path}'); bpy.ops.wm.save_as_mainfile(filepath='{init_version_path}')"
            presets = [p for p in self.paths if
                       p.get("name", "").lower().startswith("preset-") and p.get("name", "").lower().endswith(
                           (self.ui.comboBox_department.currentText() or "").lower())]
            preset = presets[0].get("description", "") if presets else ""
            if preset:
                with open(preset, "r") as f:
                    preset_code = f.read()
                    create_script = start_script + "\n\n" + preset_code + "\n\n" + end_script
            else:
                create_script = end_script + "\n\n" + end_script
        # endregion
        
        # Conttinue in here
        SubprocessServices.run_command([blender_program, "-b", "--python-expr", create_script])
        file_path = init_version_path
        VersioningSystem.init_log(base_path=str(master_path), file_path=str(file_path), locked=False,
                                  timestamp=time.time(), author=self.user_id)
        VersioningSystem.init_log(base_path=str(master_path), file_path=str(init_version_path), locked=False,
                                  timestamp=time.time(), author=self.user_id)

    # region List search function 
    def wire_search_list(self):
        le = self.ui.lineEdit_list
        if le:
            le.textChanged.connect(self.filter_list)

    def filter_list(self, text: str):
        lw = self.ui.listWidget_list
        text_low = (text or "").lower().strip()
        for i in range(lw.count()):
            item = lw.item(i)
            if item is None:
                continue
            item.setHidden(text_low not in item.text().lower())
    # endregion