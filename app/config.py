import os
import platform
import json
from cryptography.fernet import Fernet

def get_config_dir(app_name="myapp") -> str:
    system = platform.system()

    if system == "Windows":
        return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming")), app_name)
    elif system == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~/Library/Application Support"), app_name)
    else:  # Linux and others
        return os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), app_name)


class Settings:
    APP_NAME = "ZerØXe"
    BUILD_VERSION = "v0.0.8"

    KITSU_API_URL="http://192.168.99.38/api"
    KITSU_ALT_API_URL="http://patokitsu.synology.me/api"

    VERSIONING_FOLDER="progress"
    VERSIONING_LOG_FOLDER=".zeroxe"
    VERSIONING_STARTWITH="v"

    CONFIG_DIR = get_config_dir(APP_NAME)
    SESSION_FILE = os.path.join(CONFIG_DIR, "user", "user_data.dat")
    FILES_DIR = os.path.join(CONFIG_DIR, "files")
    AVATAR_FILE = os.path.join(FILES_DIR, "user", "avatar.png")

    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(AVATAR_FILE), exist_ok=True)

    def __init__(self):
        fernet_key = ""
        if not fernet_key:
            raise ValueError("FERNET_KEY environment variable not set. Please configure it in your .env file.")
        # Fernet expects the key as bytes (already base64-encoded from .env)
        key_bytes = fernet_key.encode() if isinstance(fernet_key, str) else fernet_key
        self.cipher = Fernet(key_bytes)

    def save_user_data(self, data):
        os.makedirs(os.path.dirname(self.SESSION_FILE), exist_ok=True)

        json_data = json.dumps(data).encode()
        encrypted_json = self.cipher.encrypt(json_data)

        with open(self.SESSION_FILE, "wb") as f:
            f.write(encrypted_json)

    def read_user_data(self):
        if os.path.exists(self.SESSION_FILE):
            with open(self.SESSION_FILE, "rb") as f:
                encrypted = f.read()
                if encrypted:
                    try:
                        decrypted = self.cipher.decrypt(encrypted)
                        return json.loads(decrypted.decode())
                    except Exception as e:
                        print("Decrypt error:", e)
        return None

    def update_user_field(self, key, value):
        data = self.read_user_data() or {}
        data[key] = value
        self.save_user_data(data)