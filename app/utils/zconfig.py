class ZConfigManager:
    @staticmethod
    def check_data(data):
        if "departments" not in data:
            data = {"departments": {}}
            return data, False
        return data, True