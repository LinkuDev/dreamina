import requests
import json
import time
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import API_BASE_URL, MODEL_NAME, SAMPLE_STRENGTH
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_retry_session() -> requests.Session:
    """Create requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def generate_image_via_api(prompt: str, 
                          session_id: str,
                          width: int,
                          height: int,
                          n: int = 4) -> list[str]:
    """
    Generate images via API and return list of URLs
    
    Args:
        prompt: The text prompt for generation
        session_id: Session ID from cookie file
        width: Image width in pixels
        height: Image height in pixels
        n: Number of images to generate (1-4)
    
    Returns:
        List of image URLs
    """
    try:
        endpoint = f"{API_BASE_URL}/images/generations"
        headers = {
            "Authorization": f"Bearer {session_id}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "width": width,
            "height": height,
            "n": n,
            "sample_strength": SAMPLE_STRENGTH
        }
        
        session = create_retry_session()
        print(f"   🎨 Generating {n} image(s) for: {prompt[:60]}...")
        
        resp = session.post(
            endpoint,
            headers=headers,
            data=json.dumps(payload),
            timeout=300
        )
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("data"):
            print(f"   ⚠️  No images returned for prompt")
            return []
        
        urls = [d["url"] for d in data["data"]]
        print(f"   ✅ Generated {len(urls)} image(s)")
        return urls
        
    except Exception as exc:
        print(f"   ❌ API error: {exc}")
        return []

def download_image(url: str, output_path: Path, session: requests.Session = None) -> bool:
    """Download image from URL to file"""
    try:
        if session is None:
            session = create_retry_session()
        
        resp = session.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        
        return True
    except Exception as exc:
        print(f"   ❌ Download failed: {exc}")
        return False
