import re
from pathlib import Path
from typing import Dict, Optional

# Aspect ratio mapping từ user input sang HTML value
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

def load_settings(settings_file: str = "settings.txt") -> Dict[str, str]:
    """Load settings từ file settings.txt"""
    settings = {}
    settings_path = Path(settings_file)
    
    if not settings_path.exists():
        print(f"❌ Settings file not found: {settings_file}")
        return settings
    
    print(f"📖 Loading settings từ {settings_file}...")
    
    with settings_path.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip comments và empty lines
            if not line or line.startswith('#'):
                continue
                
            # Parse KEY: VALUE format
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().upper()
                value = value.strip()
                settings[key] = value
                print(f"   • {key}: {value}")
    
    return settings

def get_aspect_ratio_value(ratio_setting: str) -> Optional[str]:
    """Convert user setting sang HTML value cho aspect ratio"""
    ratio_upper = ratio_setting.upper().strip()
    
    if ratio_upper in ASPECT_RATIO_MAP:
        html_value = ASPECT_RATIO_MAP[ratio_upper]
        print(f"✅ Aspect ratio mapping: {ratio_setting} -> '{html_value}'")
        return html_value
    else:
        print(f"❌ Invalid aspect ratio: {ratio_setting}")
        print(f"   Available options: {list(ASPECT_RATIO_MAP.keys())}")
        return None

def validate_settings(settings: Dict[str, str]) -> bool:
    """Validate settings values"""
    valid = True
    
    # Check aspect ratio
    if 'RATIO' in settings:
        if get_aspect_ratio_value(settings['RATIO']) is None:
            valid = False
    
    # Check image count
    if 'IMAGE_COUNT' in settings:
        try:
            count = int(settings['IMAGE_COUNT'])
            if count < 1 or count > 4:
                print(f"❌ Invalid IMAGE_COUNT: {count}. Must be 1-4")
                valid = False
        except ValueError:
            print(f"❌ Invalid IMAGE_COUNT: {settings['IMAGE_COUNT']}. Must be a number")
            valid = False
    
    return valid

def get_setting_or_default(settings: Dict[str, str], key: str, default: str) -> str:
    """Get setting value hoặc return default"""
    return settings.get(key.upper(), default)

# Test function
def test_settings():
    """Test settings loading và validation"""
    print("🧪 Testing settings...")
    settings = load_settings()
    
    if settings:
        print(f"\n📋 Loaded {len(settings)} settings:")
        for key, value in settings.items():
            print(f"   {key}: {value}")
        
        if validate_settings(settings):
            print("\n✅ All settings valid!")
            
            # Show mapped values
            if 'RATIO' in settings:
                html_value = get_aspect_ratio_value(settings['RATIO'])
                print(f"   Aspect ratio HTML value: '{html_value}'")
                
        else:
            print("\n❌ Some settings invalid!")
    else:
        print("❌ No settings loaded")

if __name__ == "__main__":
    test_settings()
