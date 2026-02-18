import os
import gazu
from dotenv import load_dotenv

load_dotenv()

gazu_client = gazu
gazu_client.set_host(os.getenv("KITSU_API_URL") or os.getenv("KITSU_ALT_API_URL"))