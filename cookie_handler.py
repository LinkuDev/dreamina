import json
from pathlib import Path

def load_cookies_from_file(cookie_file_path: str):
    """Load cookies from custom file format (session_id on first line, JSON on remaining lines)"""
    try:
        with open(cookie_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        session_id = lines[0].strip()
        json_content = ''.join(lines[1:])
        cookie_data = json.loads(json_content)
        
        print(f"   📁 Loaded {len(cookie_data)} cookies from {Path(cookie_file_path).name}")
        print(f"   🔑 Session ID: {session_id[:20]}...")
        
        return clean_cookies(cookie_data)
        
    except Exception as e:
        print(f"   ❌ Error loading cookies from {cookie_file_path}: {e}")
        return []

def clean_cookies(cookies):
    """Clean sameSite field from cookies to avoid browser compatibility issues"""
    if not cookies:
        return []
        
    for cookie in cookies:
        if 'sameSite' in cookie:
            del cookie['sameSite']
    
    print(f"   🧹 Cleaned sameSite from {len(cookies)} cookies")
    return cookies

def get_first_cookie_file(cookies_dir: str = "cookies"):
    """Get the first available cookie file"""
    cookies_path = Path(cookies_dir)
    
    if not cookies_path.exists():
        print(f"❌ Cookies directory '{cookies_dir}' not found")
        return None
    
    # Find JSON files
    json_files = list(cookies_path.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON cookie files found in '{cookies_dir}'")
        return None
    
    # Sort and take first
    first_file = sorted(json_files)[0]
    print(f"🍪 Using cookie file: {first_file.name}")
    
    return str(first_file)
