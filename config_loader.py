import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BrowserConfig:
    headless: bool = False
    timeout: int = 30000
    wait_time: int = 30
    max_retries: int = 3

@dataclass  
class TargetConfig:
    url: str = "https://dreamina.capcut.com/ai-tool/generate?type=image"
    cookies_folder: str = "cookies"
    cookie_file: str = "A (221).json"

@dataclass
class GenerationConfig:
    aspect_ratio: str = "16:9"
    image_count: int = 4
    quality: str = "high"

@dataclass
class DelaysConfig:
    navigation: int = 3000
    modal: int = 3000
    auth_check: int = 3000

@dataclass
class DebugConfig:
    verbose_logging: bool = True
    screenshot_on_error: bool = True
    save_page_content: bool = False

@dataclass
class AppConfig:
    browser: BrowserConfig
    target: TargetConfig
    generation: GenerationConfig
    delays: DelaysConfig
    debug: DebugConfig
    aspect_ratio_mapping: Dict[str, str]

class ConfigLoader:
    """Load configuration từ .env hoặc JSON file"""
    
    DEFAULT_ASPECT_MAPPING = {
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
    
    @staticmethod
    def load_from_env(env_file: str = ".env") -> AppConfig:
        """Load config từ .env file"""
        env_path = Path(env_file)
        
        if env_path.exists():
            print(f"📖 Loading config từ {env_file}...")
            ConfigLoader._load_env_file(env_path)
        else:
            print(f"⚠️  {env_file} not found, using environment variables...")
        
        # Load với fallback defaults
        browser = BrowserConfig(
            headless=ConfigLoader._get_bool("BROWSER_HEADLESS", False),
            timeout=ConfigLoader._get_int("BROWSER_TIMEOUT", 30) * 1000,  # Convert to ms
            wait_time=ConfigLoader._get_int("BROWSER_WAIT_TIME", 30),
            max_retries=ConfigLoader._get_int("MAX_RETRIES", 3)
        )
        
        target = TargetConfig(
            url=os.getenv("TARGET_URL", "https://dreamina.capcut.com/ai-tool/generate?type=image"),
            cookies_folder=os.getenv("COOKIES_FOLDER", "cookies"),
            cookie_file=os.getenv("COOKIE_FILE", "A (221).json")
        )
        
        generation = GenerationConfig(
            aspect_ratio=os.getenv("ASPECT_RATIO", "16:9"),
            image_count=ConfigLoader._get_int("IMAGE_COUNT", 4),
            quality=os.getenv("QUALITY", "high")
        )
        
        delays = DelaysConfig(
            navigation=ConfigLoader._get_int("NAVIGATION_DELAY", 3000),
            modal=ConfigLoader._get_int("MODAL_TIMEOUT", 3000), 
            auth_check=ConfigLoader._get_int("AUTH_CHECK_DELAY", 3000)
        )
        
        debug = DebugConfig(
            verbose_logging=ConfigLoader._get_bool("VERBOSE_LOGGING", True),
            screenshot_on_error=ConfigLoader._get_bool("SCREENSHOT_ON_ERROR", True),
            save_page_content=ConfigLoader._get_bool("SAVE_PAGE_CONTENT", False)
        )
        
        return AppConfig(
            browser=browser,
            target=target,
            generation=generation,
            delays=delays,
            debug=debug,
            aspect_ratio_mapping=ConfigLoader.DEFAULT_ASPECT_MAPPING
        )
    
    @staticmethod
    def load_from_json(json_file: str = "config.json") -> AppConfig:
        """Load config từ JSON file"""
        json_path = Path(json_file)
        
        if not json_path.exists():
            print(f"❌ {json_file} not found!")
            raise FileNotFoundError(f"Config file {json_file} not found")
        
        print(f"📖 Loading config từ {json_file}...")
        
        with json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        browser = BrowserConfig(**data.get("browser", {}))
        target = TargetConfig(**ConfigLoader._snake_case_keys(data.get("target", {})))
        generation = GenerationConfig(**ConfigLoader._snake_case_keys(data.get("generation", {})))
        delays = DelaysConfig(**data.get("delays", {}))
        debug = DebugConfig(**ConfigLoader._snake_case_keys(data.get("debug", {})))
        
        aspect_mapping = data.get("aspectRatioMapping", ConfigLoader.DEFAULT_ASPECT_MAPPING)
        
        return AppConfig(
            browser=browser,
            target=target, 
            generation=generation,
            delays=delays,
            debug=debug,
            aspect_ratio_mapping=aspect_mapping
        )
    
    @staticmethod
    def auto_load() -> AppConfig:
        """Tự động load config - ưu tiên JSON, fallback về .env"""
        if Path("config.json").exists():
            return ConfigLoader.load_from_json()
        elif Path(".env").exists():
            return ConfigLoader.load_from_env()
        else:
            print("⚠️  No config file found, using defaults...")
            return ConfigLoader.load_from_env()  # Will use defaults
    
    @staticmethod
    def _load_env_file(env_path: Path):
        """Load .env file vào environment"""
        with env_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    @staticmethod
    def _get_bool(key: str, default: bool) -> bool:
        """Get boolean từ env với default"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod  
    def _get_int(key: str, default: int) -> int:
        """Get integer từ env với default"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def _snake_case_keys(data: dict) -> dict:
        """Convert camelCase keys sang snake_case"""
        result = {}
        for key, value in data.items():
            # Convert camelCase to snake_case
            snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
            result[snake_key] = value
        return result

def get_aspect_ratio_html_value(config: AppConfig, ratio: str) -> Optional[str]:
    """Get HTML value cho aspect ratio từ config"""
    ratio_upper = ratio.upper().strip()
    
    if ratio_upper in config.aspect_ratio_mapping:
        html_value = config.aspect_ratio_mapping[ratio_upper]
        if config.debug.verbose_logging:
            print(f"✅ Aspect ratio mapping: {ratio} -> '{html_value}'")
        return html_value
    else:
        print(f"❌ Invalid aspect ratio: {ratio}")
        print(f"   Available options: {list(config.aspect_ratio_mapping.keys())}")
        return None

def print_config(config: AppConfig):
    """Print config summary"""
    print("\n" + "="*60)
    print("📋 CURRENT CONFIGURATION")
    print("="*60)
    print(f"🌐 Target URL: {config.target.url}")
    print(f"🍪 Cookie File: {config.target.cookies_folder}/{config.target.cookie_file}")
    print(f"📐 Aspect Ratio: {config.generation.aspect_ratio}")
    print(f"🖼️  Image Count: {config.generation.image_count}")
    print(f"⏱️  Browser Timeout: {config.browser.timeout}ms")
    print(f"🔧 Headless Mode: {config.browser.headless}")
    print(f"🐛 Debug Logging: {config.debug.verbose_logging}")
    print("="*60)

# Test function
if __name__ == "__main__":
    print("🧪 Testing config loader...")
    
    # Test JSON
    try:
        config = ConfigLoader.load_from_json()
        print("\n✅ JSON config loaded successfully!")
        print_config(config)
        
        # Test aspect ratio mapping
        html_value = get_aspect_ratio_html_value(config, config.generation.aspect_ratio)
        print(f"\n🎯 Current aspect ratio maps to: '{html_value}'")
        
    except Exception as e:
        print(f"❌ JSON failed: {e}")
        
        # Fallback to .env
        print("\n🔄 Trying .env config...")
        config = ConfigLoader.load_from_env()
        print("\n✅ ENV config loaded!")
        print_config(config)
