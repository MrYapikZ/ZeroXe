from app.core.gazu_client import gazu_client

class AppState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            # Create the instance
            cls._instance = super(AppState, cls).__new__(cls)

            cls.access_token = None
            cls.user_data = None
            cls.username = None
            cls.avatar = None

        return cls._instance

    def set_access_token(self, access_token):
        self.access_token = access_token
        
    def set_user_data(self, user_data):
        self.user_data = user_data