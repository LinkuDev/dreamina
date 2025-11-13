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
    
    # Ensure each cookie has a valid sameSite value
    valid_same_site = {"Strict", "Lax", "None"}
    for cookie in cookies:
        if cookie.get("sameSite") not in valid_same_site:
            cookie["sameSite"] = "Lax"
    
    print(f"   🧹 Cleaned {len(cookies)} cookies")
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

def load_accounts(folder: str = "cookies") -> list[dict]:
    """
    Load all cookie files from folder as accounts
    
    Args:
        folder: Path to cookies folder
    
    Returns:
        List of account dicts with 'name', 'session_id', 'cookies', 'filepath'
    """
    print(f"🔑 Loading accounts from '{folder}'...")
    accounts = []
    folder_path = Path(folder)
    
    if not folder_path.is_dir():
        print(f"❌ Folder not found: {folder}")
        return []
    
    # Load all JSON files
    for file_path in sorted(folder_path.glob("*.json")):
        try:
            with file_path.open(encoding="utf-8") as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                print(f"   ⚠️  {file_path.name}: not enough lines, skipping")
                continue
            
            session_id = lines[0].strip()
            cookies = json.loads("".join(lines[1:]))
            
            accounts.append({
                "name": file_path.stem,
                "session_id": session_id,
                "cookies": cookies,
                "filepath": file_path,
            })
            
            print(f"   ✅ Loaded {file_path.name}")
            
        except (json.JSONDecodeError, IndexError) as exc:
            print(f"   ⚠️  {file_path.name}: bad format ({exc})")
    
    if not accounts:
        print("❌ No usable accounts found")
    else:
        print(f"✅ {len(accounts)} account(s) ready\n")
    
    return accounts
