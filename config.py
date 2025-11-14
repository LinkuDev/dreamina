# Configuration constants
import os
from dotenv import load_dotenv

load_dotenv()

# URLs
TARGET_URL = os.getenv('TARGET_URL', 'https://dreamina.capcut.com/ai-tool/generate?type=image')
DREAMINA_HOME_URL = os.getenv('DREAMINA_HOME_URL', 'https://dreamina.capcut.com/ai-tool/home')
DREAMINA_CREATIONS_URL = os.getenv('DREAMINA_CREATIONS_URL', 'https://dreamina.capcut.com/ai-tool/asset')
DREAMINA_ROOT_URL = "https://dreamina.capcut.com"

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/v1')
MODEL_NAME = "jimeng-3.0"

# Paths
COOKIES_FOLDER = os.getenv('COOKIES_FOLDER', 'cookies')
PROMPT_FILE = os.getenv('PROMPT_FILE', '')

# Generation Settings
IMAGE_COUNT = int(os.getenv('IMAGE_COUNT', '4'))
SAMPLE_STRENGTH = 0.5
CREDITS_PER_GENERATION = 5

# Browser Settings
BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true'
BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30'))

# Browser launch arguments for optimized experience with zoom
BROWSER_ARGS = [
    "--start-maximized",          # Start with maximized window  
    "--window-size=1920,1080",    # Set large window size
    "--disable-web-security",     # Disable web security for better compatibility
    "--disable-features=VizDisplayCompositor",
    "--no-default-browser-check", # Skip default browser check
    "--disable-extensions",       # Disable extensions for better performance
    "--force-device-scale-factor=1.0",  # Ensure consistent scaling
]

# Default viewport settings for full HD experience
BROWSER_VIEWPORT = {'width': 1920, 'height': 1080}

# Browser zoom level for sharper images (50% = 0.5, 75% = 0.75, etc.)
BROWSER_ZOOM_LEVEL = 0.75  # 75% zoom for better image quality

# Advanced Settings
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
MAX_CONCURRENT_JOBS = 3
PROMPT_CHUNK_SIZE = 6
GALLERY_UPDATE_DELAY = 10

# Aspect ratio mapping: UI name -> (width, height)
ASPECT_RATIOS = {
    "AUTO": (1328, 1328),
    "21:9": (2016, 864),
    "16:9": (1664, 936),
    "3:2": (1584, 1056),
    "4:3": (1472, 1104),
    "8:7": (1344, 1176),
    "1:1": (1328, 1328),
    "7:8": (1176, 1344),
    "3:4": (1104, 1472),
    "2:3": (1056, 1584),
    "9:16": (936, 1664),
}

def get_aspect_ratio_dimensions(ratio_string: str) -> tuple:
    """Get width and height for given aspect ratio string"""
    ratio_key = ratio_string.upper()
    if ratio_key in ASPECT_RATIOS:
        return ASPECT_RATIOS[ratio_key]
    # Default to 1:1
    return ASPECT_RATIOS["1:1"]
