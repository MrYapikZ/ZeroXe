import os
import gazu
from dotenv import load_dotenv

load_dotenv()

gazu_client = gazu
try:
    gazu_client.set_host(os.getenv("KITSU_API_URL"))
    print(gazu_client.client.get_api_version())
except Exception as e:
    gazu_client.set_host(os.getenv("KITSU_ALT_API_URL"))
    print(gazu_client.client.get_api_version())