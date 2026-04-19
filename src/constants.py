from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(".env")
BASE_DIR = str(Path(__file__).parents[1])
CHROME_DRIVER_PATH = os.path.join(BASE_DIR, "CHROME_DRIVERS")
OUTPUT_DIR = os.path.join(BASE_DIR, "OUTPUT_DIR")
HEADERS = {"User-Agent": "Mozilla/5.0"}

MAX_WORKERS = int(os.getenv("MAX_WORKERS", 1))
PROXY = os.getenv("PROXY", None)
