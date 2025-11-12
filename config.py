# Configuration
TARGET_URL = "https://dreamina.capcut.com/ai-tool/generate?type=image"
COOKIES_FILE = "cookies/A (221).json"
BROWSER_WAIT_TIME = 30
DESIRED_ASPECT_RATIO = "16:9"  # Can be: AUTO, 21:9, 16:9, 3:2, 4:3, 1:1, 3:4, 2:3, 9:16

# Aspect ratio mapping từ setting sang HTML value
ASPECT_RATIO_MAP = {
    "AUTO": "",
    "21:9": "21:9",
    "16:9": "16:9",
    "3:2": "3:2",
    "4:3": "4:3",
    "1:1": "1:1",
    "3:4": "3:4",
    "2:3": "2:3",
    "9:16": "9:16"
}
