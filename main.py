import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Import our utility modules
from config import TARGET_URL
from cookie_handler import get_first_cookie_file, load_cookies_from_file
from browser_utils import safe_navigate, handle_modals, select_aspect_ratio
from auth_checker import check_authentication_status

# Load environment variables
load_dotenv()

async def main():
    """Main automation function"""
    print("🚀 Starting Dreamina authentication checker...")
    
    # Get cookie file
    cookie_file = get_first_cookie_file()
    if not cookie_file:
        return
    
    # Load cookies
    cookies = load_cookies_from_file(cookie_file)
    if not cookies:
        print("❌ No valid cookies loaded")
        return
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Add cookies to browser context
            await context.add_cookies(cookies)
            print(f"✅ Added {len(cookies)} cookies to browser context")
            
            # Navigate to target URL with modal handling
            await safe_navigate(page, TARGET_URL)
            
            # Handle any remaining modals
            await handle_modals(page)
            
            # Check authentication status
            is_authenticated, details = await check_authentication_status(page)
            
            if is_authenticated:
                print(f"\n✅ SUCCESS: User is authenticated")
                print(f"   📋 Details: {details}")
                
                # Optional: Select aspect ratio if specified in environment
                aspect_ratio = os.getenv('ASPECT_RATIO', '').strip()
                if aspect_ratio:
                    print(f"\n🎯 Attempting to select aspect ratio: {aspect_ratio}")
                    success = await select_aspect_ratio(page, aspect_ratio)
                    if success:
                        print("✅ Aspect ratio selected successfully")
                    else:
                        print("❌ Failed to select aspect ratio")
            else:
                print(f"\n❌ FAILED: User is not authenticated")
                print(f"   📋 Details: {details}")
            
            # Keep browser open for inspection
            print("\n⏸️  Keeping browser open for manual inspection...")
            print("   Press Ctrl+C to close")
            
            # Wait indefinitely until user stops
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Closing browser...")
                
        except Exception as e:
            print(f"\n❌ Error during execution: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
