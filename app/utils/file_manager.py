from datetime import datetime
from pathlib import Path

class FileManager:
    @staticmethod
    def get_file_last_modified(path: str):
        return datetime.fromtimestamp(Path(path).stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
