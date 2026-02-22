import re
from pathlib import Path
from app.config import Settings
from app.utils.file_manager import FileManager
from app.utils.json_manager import JsonManager


class VersioningSystem:
    @staticmethod
    def get_version_folder(path: str):
        return Path(path) / Settings.VERSIONING_FOLDER

    @staticmethod
    def get_version_log_folder(path: str):
        return Path(path) / Settings.VERSIONING_LOG_FOLDER / "logs"

    @staticmethod
    def get_version_log_file(path: str):
        return Path(path) / Settings.VERSIONING_LOG_FOLDER / "log.json"

    @staticmethod
    def get_version_files(path: str):
        files = re.findall(
            r"^" + Settings.VERSIONING_STARTWITH + r"\d+",
            Path(path).iterdir(),
            re.IGNORECASE,
        )
        return files

    @staticmethod
    def get_version_files_with_date(path: str):
        files = VersioningSystem.get_version_files(path)
        files_with_date = []
        for file in files:
            files_with_date.append(
                (file, FileManager.get_file_last_modified(path / file))
            )
        return files_with_date

    @staticmethod
    def get_version_file_with_date(path: str):
        file = VersioningSystem.get_latest_version(path)
        if not file:
            return None
        return (file, FileManager.get_file_last_modified(path / file))

    @staticmethod
    def get_latest_version(path: str):
        files = VersioningSystem.get_version_files(path)
        if not files:
            return None
        return max(files)

    @staticmethod
    def get_latest_version_path(path: str):
        latest_version = VersioningSystem.get_latest_version(path)
        if not latest_version:
            return None
        return VersioningSystem.get_version_folder(path) / latest_version

    @staticmethod
    def init_log(data: dict):
        if not data:
            return {}

        base_path = data.get("base_path")
        file_name = data.get("file")
        locked = data.get("locked")
        timestamp = data.get("timestamp")
        author = data.get("author")

        if not file_name:
            return {}

        log_folder = VersioningSystem.get_version_log_folder(base_path)
        log_file = log_folder / f"{file_name}.json"
        JsonManager.save_json(
            log_file,
            {
                "file": file_name,
                "locked": locked,
                "logs": [
                    {"log": 1, "date": timestamp, "author": author, "locked": locked}
                ],
            },
        )

    @staticmethod
    def update_log(data: dict):
        if not data:
            return {}

        base_path = data.get("base_path")
        file_name = data.get("file")
        locked = data.get("locked")
        timestamp = data.get("timestamp")
        author = data.get("author")

        if not file_name:
            return {}

        log_folder = VersioningSystem.get_version_log_folder(base_path)
        log_file = log_folder / f"{file_name}.json"

        log_data = JsonManager.load_json(log_file)
        next_log_id = len(log_data.get("logs", [])) + 1
        log_data["locked"] = locked
        log_data["logs"].append({"log": next_log_id, "date": timestamp, "author": author, "locked": locked})
        JsonManager.update_json(log_file, log_data)
