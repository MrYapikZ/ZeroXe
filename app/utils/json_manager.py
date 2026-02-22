import json

class JsonManager:
    @staticmethod
    def load_json(file_path: str):
        with open(file_path, "r") as f:
            return json.load(f)
    
    @staticmethod
    def save_json(file_path: str, data: dict):
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    
    @staticmethod
    def update_json(file_path: str, data: dict):
        with open(file_path, "r") as f:
            existing_data = json.load(f)
        existing_data.update(data)
        with open(file_path, "w") as f:
            json.dump(existing_data, f, indent=4)