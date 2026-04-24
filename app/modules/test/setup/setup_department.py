import json
import os
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QTreeWidgetItem,
    QListWidgetItem,
    QPushButton,
    QHeaderView,
    QStyleOptionButton,
    QHBoxLayout,
    QAbstractItemView,
    QSizePolicy,
    QApplication,
    QMessageBox,
    QFileDialog,
)

from app.ui.test.setup.setup_department_ui import Ui_Form

from app.utils.json_manager import JsonManager
from app.utils.zconfig import ZConfigManager
from app.utils.api.gazu.person import PersonServices
from app.utils.api.gazu.asset import AssetServices
from app.utils.api.gazu.project import ProjectServices
from app.utils.api.gazu.shot import ShotServices


class HandleSetupDepartment(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.json_path = "data.json"
        self.paths = []
        self.json_data = {}
        self.current_department = {}

        self.departments = []
        self.asset_type_list = []
        self.based = "shot"
        self.based_list = ["shot", "asset"]
        self.setting_list = ["departments", "mastershots", "library", "addons", "other"]
        self.asset_type = {}

        self.load_json()
        self.init_data()
        self.mount_function()

    def mount_function(self):
        self.ui.comboBox_based.currentIndexChanged.connect(self.refresh_based_asset)
        self.ui.pushButton_save.clicked.connect(self.write_json)
        self.ui.pushButton_demo.clicked.connect(self.demo_print_json)
        self.ui.toolButton_presetAdd.clicked.connect(self.add_preset)
        self.ui.toolButton_presetRemove.clicked.connect(self.remove_preset)
        self.ui.comboBox_presetList.currentIndexChanged.connect(
            self.refresh_preset_field
        )
        self.ui.comboBox_department.currentIndexChanged.connect(self.reload_data)
        self.ui.comboBox_assetType.currentIndexChanged.connect(self.refresh_asset_field)
        self.ui.pushButton_saveAssetType.clicked.connect(self.save_asset_type)
        self.ui.comboBox_project.currentIndexChanged.connect(self.on_project_change)
        self.ui.comboBox_settings.currentIndexChanged.connect(
            self.refresh_other_settings
        )
        self.ui.comboBox_fieldList.currentIndexChanged.connect(self.refresh_other_field)
        self.ui.toolButton_fieldAdd.clicked.connect(self.add_other_field)
        self.ui.toolButton_fieldRemove.clicked.connect(self.remove_other_field)

    def init_data(self):
        # Settings
        for setting in self.setting_list:
            self.ui.comboBox_settings.addItem(setting)

        # Project
        projects = ProjectServices.get_projects()
        self.projects = projects
        self.ui.comboBox_project.clear()
        for project in projects:
            self.ui.comboBox_project.addItem(project["name"], project["id"])

        # Department
        departments = PersonServices.get_departments()
        self.departments = departments
        self.ui.comboBox_department.clear()
        self.ui.comboBox_sourceDepartment.clear()
        self.ui.comboBox_sourceDepartment.addItem("null")
        self.ui.comboBox_sourceDepartment.addItem("init")
        for i in self.departments:
            self.ui.comboBox_department.addItem(i["name"])
            self.ui.comboBox_sourceDepartment.addItem(i["name"])

        # Based
        self.ui.comboBox_based.clear()
        for i in self.based_list:
            self.ui.comboBox_based.addItem(i)

        # Assets
        asset_type = AssetServices.get_asset_types()
        self.asset_type_list = asset_type
        self.ui.comboBox_assetType.clear()
        for i in self.asset_type_list:
            self.ui.comboBox_assetType.addItem(i["name"])

        self.refresh_other_settings()

    def on_project_change(self):
        project_id = self.ui.comboBox_project.currentData()
        if project_id is None:
            return

        self.paths = []
        episodes = ShotServices.get_episodes_by_project_id(project_id)
        for episode in episodes:
            if episode["name"].startswith("setting"):
                bpaths = ShotServices.get_shots_by_episode_id(episode["id"])
                asset_bpaths = AssetServices.get_assets_by_episode_id(episode["id"])
                self.paths = bpaths + asset_bpaths
                continue

        self.json_path = ""
        path_data = [
            p
            for p in self.paths
            if p.get("name", "").lower().startswith("bpath-")
            and p.get("name", "").lower().endswith("zeroxe_conf")
        ]
        if path_data:
            self.json_path = path_data[0].get("description", "")
        print(self.json_path)
        self.load_json()
        self.reload_data()

    def reload_data(self):
        if not self.json_data:
            return
        self.ui.comboBox_sourceDepartment.setCurrentText("null")
        if self.ui.comboBox_settings.currentText() == "departments":
            current_department = self.json_data.get("departments", {}).get(
                self.ui.comboBox_department.currentText(), {}
            )
            self.current_department = current_department
            self.ui.lineEdit_fileCode.setText(current_department.get("code", ""))
            self.ui.comboBox_sourceDepartment.setCurrentText(
                current_department.get("source", "null")
            )
            self.ui.comboBox_based.setCurrentText(
                current_department.get("based", "shot")
            )
            self.asset_type = {}
            if (
                current_department.get("based")
                and current_department["based"] == "shot"
            ):
                self.ui.lineEdit_basePath.setText(
                    current_department.get("base_path", "")
                )
            elif (
                current_department.get("based")
                and current_department["based"] == "asset"
            ):
                if current_department.get("asset_type"):
                    self.asset_type = current_department["asset_type"]
            else:
                self.ui.lineEdit_basePath.clear()

            self.update_preset_ui()
            self.refresh_asset_field()
            self.refresh_based_asset()
        else:
            self.ui.comboBox_fieldList.clear()
            other_data = self.json_data.get(self.ui.comboBox_settings.currentText(), {})
            for i in other_data:
                self.ui.comboBox_fieldList.addItem(i)
            self.refresh_other_field()

    def refresh_based_asset(self):
        if self.ui.comboBox_based.currentText() == "asset":
            self.ui.label_basePath.setVisible(False)
            self.ui.lineEdit_basePath.setVisible(False)
            self.ui.label_sourceDepartment.setVisible(False)
            self.ui.comboBox_sourceDepartment.setVisible(False)
            for i in range(self.ui.gridLayout_Preset.count()):
                item = self.ui.gridLayout_Preset.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
            for i in range(self.ui.gridLayout_assets.count()):
                item = self.ui.gridLayout_assets.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(True)
        else:
            self.ui.label_basePath.setVisible(True)
            self.ui.lineEdit_basePath.setVisible(True)
            self.ui.label_sourceDepartment.setVisible(True)
            self.ui.comboBox_sourceDepartment.setVisible(True)
            for i in range(self.ui.gridLayout_Preset.count()):
                item = self.ui.gridLayout_Preset.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(True)
            for i in range(self.ui.gridLayout_assets.count()):
                item = self.ui.gridLayout_assets.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)

    # region Presets
    def update_preset_ui(self):
        self.ui.comboBox_presetList.clear()
        # Sorting them makes the UI much easier for users to navigate
        if (
            not self.json_data.get("departments", {})
            .get(self.ui.comboBox_department.currentText(), {})
            .get("presets")
        ):
            return
        for name in sorted(
            self.json_data["departments"][self.ui.comboBox_department.currentText()][
                "presets"
            ].keys()
        ):
            self.ui.comboBox_presetList.addItem(name)
        self.refresh_preset_field()

    def refresh_preset_field(self):
        self.ui.lineEdit_presetName.clear()
        self.ui.lineEdit_presetPath.clear()
        if (
            not self.json_data.get("departments", {})
            .get(self.ui.comboBox_department.currentText(), {})
            .get("presets")
        ):
            return
        current_preset = self.ui.comboBox_presetList.currentText()
        preset_data = (
            self.json_data.get("departments", {})
            .get(self.ui.comboBox_department.currentText(), {})
            .get("presets", {})
            .get(current_preset)
        )
        if preset_data:
            self.ui.lineEdit_presetName.setText(
                self.ui.comboBox_presetList.currentText()
            )
            self.ui.lineEdit_presetPath.setText(preset_data.get("path", ""))

    def add_preset(self):
        if (
            not self.json_data.get("departments", {})
            .get(self.ui.comboBox_department.currentText(), {})
            .get("presets")
        ):
            return
        name = self.ui.lineEdit_presetName.text()
        if name:
            self.json_data["departments"][self.ui.comboBox_department.currentText()][
                "presets"
            ][name] = {"path": self.ui.lineEdit_presetPath.text()}
            self.update_preset_ui()

    def remove_preset(self):
        if (
            not self.json_data.get("departments", {})
            .get(self.ui.comboBox_department.currentText(), {})
            .get("presets")
        ):
            return
        current_preset = self.ui.comboBox_presetList.currentText()
        if (
            current_preset
            in self.json_data["departments"][self.ui.comboBox_department.currentText()][
                "presets"
            ]
        ):
            del self.json_data["departments"][
                self.ui.comboBox_department.currentText()
            ]["presets"][current_preset]
            self.update_preset_ui()

    # endregion

    # region Asset Type
    def refresh_asset_field(self):
        current_asset_type = self.ui.comboBox_assetType.currentText()
        asset_type_data = self.asset_type.get(current_asset_type)
        if asset_type_data:
            self.ui.lineEdit_assetCode.setText(asset_type_data.get("code", ""))
            self.ui.lineEdit_assetPrefix.setText(asset_type_data.get("prefix", ""))
            self.ui.lineEdit_assetSuffix.setText(asset_type_data.get("suffix", ""))
            self.ui.lineEdit_assetBasePath.setText(asset_type_data.get("base_path", ""))
        else:
            self.ui.lineEdit_assetCode.clear()
            self.ui.lineEdit_assetPrefix.clear()
            self.ui.lineEdit_assetSuffix.clear()
            self.ui.lineEdit_assetBasePath.clear()

    def save_asset_type(self):
        self.asset_type[self.ui.comboBox_assetType.currentText()] = {
            "code": self.ui.lineEdit_assetCode.text(),
            "prefix": self.ui.lineEdit_assetPrefix.text(),
            "suffix": self.ui.lineEdit_assetSuffix.text(),
            "base_path": self.ui.lineEdit_assetBasePath.text(),
        }
        self.refresh_asset_field()

    # endregion

    # region Other settings
    def refresh_other_settings(self):
        if self.ui.comboBox_settings.currentText() == "departments":
            # Department settings
            for i in range(self.ui.verticalLayout_department.count()):
                item = self.ui.verticalLayout_department.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(True)
            for i in range(self.ui.gridLayout_general.count()):
                item = self.ui.gridLayout_general.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(True)
            # Other settings
            for i in range(self.ui.gridLayout_other.count()):
                item = self.ui.gridLayout_other.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
        else:
            # Department settings
            for i in range(self.ui.verticalLayout_department.count()):
                item = self.ui.verticalLayout_department.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
            for i in range(self.ui.gridLayout_general.count()):
                item = self.ui.gridLayout_general.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
            for i in range(self.ui.gridLayout_Preset.count()):
                item = self.ui.gridLayout_Preset.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
            for i in range(self.ui.gridLayout_assets.count()):
                item = self.ui.gridLayout_assets.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(False)
            # Other settings
            for i in range(self.ui.gridLayout_other.count()):
                item = self.ui.gridLayout_other.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget is not None:
                        widget.setVisible(True)
            if self.ui.comboBox_settings.currentText() == "library":
                self.ui.label_fieldPrefix.setVisible(True)
                self.ui.label_fieldSuffix.setVisible(True)
                self.ui.lineEdit_fieldPrefix.setVisible(True)
                self.ui.lineEdit_fieldSuffix.setVisible(True)
            else:
                self.ui.label_fieldPrefix.setVisible(False)
                self.ui.label_fieldSuffix.setVisible(False)
                self.ui.lineEdit_fieldPrefix.setVisible(False)
                self.ui.lineEdit_fieldSuffix.setVisible(False)
        self.reload_data()

    def refresh_other_field(self):
        other_data = self.json_data.get(self.ui.comboBox_settings.currentText(), {})
        self.ui.lineEdit_fieldName.setText(self.ui.comboBox_fieldList.currentText())
        self.ui.lineEdit_fieldBasePath.setText(
            other_data.get(self.ui.comboBox_fieldList.currentText(), {}).get(
                "base_path", ""
            )
        )
        if self.ui.comboBox_settings.currentText() == "library":
            self.ui.lineEdit_fieldPrefix.setText(
                other_data.get(self.ui.comboBox_fieldList.currentText(), {}).get(
                    "prefix", ""
                )
            )
            self.ui.lineEdit_fieldSuffix.setText(
                other_data.get(self.ui.comboBox_fieldList.currentText(), {}).get(
                    "suffix", ""
                )
            )

    def add_other_field(self):
        if not self.json_data.get(self.ui.comboBox_settings.currentText(), {}):
            return
        name = self.ui.lineEdit_fieldName.text()
        if name:
            self.json_data[self.ui.comboBox_settings.currentText()][name] = {
                "code": self.ui.lineEdit_fieldCode.text(),
                "base_path": self.ui.lineEdit_fieldBasePath.text(),
            }
            if self.ui.comboBox_settings.currentText() == "library":
                self.json_data[self.ui.comboBox_settings.currentText()][name] = {
                    "code": self.ui.lineEdit_fieldCode.text(),
                    "prefix": self.ui.lineEdit_fieldPrefix.text(),
                    "suffix": self.ui.lineEdit_fieldSuffix.text(),
                    "base_path": self.ui.lineEdit_fieldSuffix.text(),
                }
            self.ui.comboBox_fieldList.clear()
            other_data = self.json_data.get(self.ui.comboBox_settings.currentText(), {})
            for i in other_data:
                self.ui.comboBox_fieldList.addItem(i)
            self.refresh_other_field()

    def remove_other_field(self):
        if not self.json_data.get(self.ui.comboBox_settings.currentText(), {}):
            return
        current_field = self.ui.comboBox_fieldList.currentText()
        if current_field in self.json_data.get(
            self.ui.comboBox_settings.currentText(), {}
        ):
            del self.json_data[self.ui.comboBox_settings.currentText()][current_field]
            self.ui.comboBox_fieldList.clear()
            other_data = self.json_data.get(self.ui.comboBox_settings.currentText(), {})
            for i in other_data:
                self.ui.comboBox_fieldList.addItem(i)
            self.refresh_other_field()

    # endregion

    # region JSON
    def load_json(self):
        if os.path.exists(self.json_path) and os.path.isfile(self.json_path):
            json_data = JsonManager.load_json(self.json_path)

            data, found = ZConfigManager.check_data(json_data)
            self.json_data = data
        else:
            self.json_data = {
                "departments": {},
                "mastershots": {},
                "library": {},
                "addons": {},
            }

    def write_json(self):
        full_data = self.json_data
        dept_name = self.ui.comboBox_department.currentText()
        if self.ui.comboBox_settings.currentText() == "departments":
            if self.ui.comboBox_based.currentText() == "shot":
                full_data["departments"][dept_name] = {
                    "code": self.ui.lineEdit_fileCode.text(),
                    "source": self.ui.comboBox_sourceDepartment.currentText(),
                    "based": self.ui.comboBox_based.currentText(),
                    "base_path": self.ui.lineEdit_basePath.text(),
                    "presets": self.json_data.get("departments", {})
                    .get(dept_name, {})
                    .get("presets", {}),
                }
            else:
                full_data["departments"][dept_name] = {
                    "code": self.ui.lineEdit_fileCode.text(),
                    "based": self.ui.comboBox_based.currentText(),
                    "asset_type": self.asset_type,
                }
        else:
            full_data[self.ui.comboBox_settings.currentText()][
                self.ui.lineEdit_fieldName.text()
            ] = {
                "code": self.ui.lineEdit_fieldCode.text(),
                "base_path": self.ui.lineEdit_fieldBasePath.text(),
            }
            if self.ui.comboBox_settings.currentText() == "library":
                full_data[self.ui.comboBox_settings.currentText()][
                    self.ui.lineEdit_fieldName.text()
                ] = {
                    "code": self.ui.lineEdit_fieldCode.text(),
                    "prefix": self.ui.lineEdit_fieldPrefix.text(),
                    "suffix": self.ui.lineEdit_fieldSuffix.text(),
                    "base_path": self.ui.lineEdit_fieldSuffix.text(),
                }
        JsonManager.save_json(self.json_path, full_data)

    def demo_print_json(self):
        full_data = self.json_data
        departments = full_data.get("departments", {})

        for dept_name, dept_info in departments.items():
            source_name = dept_info.get("source")

            # Check if the 'source' name exists as a department key
            if source_name in departments:
                # If you want to link to the actual dictionary object of that source:
                dept_info["source"] = departments[source_name]
                print(dept_info)
                # print(f"Department: {dept_name} is sourced from: {source_name}")
            else:
                print(
                    f"Department: {dept_name} has no valid source matching an existing department."
                )

    # endregion
