import os
import gazu
from dotenv import load_dotenv
from app.config import Settings

load_dotenv()

gazu_client = gazu
try:
    gazu_client.set_host(Settings().KITSU_API_URL)
    print(gazu_client.client.get_api_version())
except Exception as e:
    gazu_client.set_host(Settings().KITSU_ALT_API_URL)
    print(gazu_client.client.get_api_version())