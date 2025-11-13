import json
import asyncio
from pathlib import Path

async def safe_navigate(page, target_url: str, max_attempts: int = 3):
    """Robust navigation with retries and modal handling."""
    for attempt in range(max_attempts):
        try:
            print(f"   Navigation attempt {attempt + 1}/{max_attempts} → {target_url}")
            
            # First load without waiting for networkidle to avoid modal blocking
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            
            # Give modal time to appear (since it's not immediate)
            print("   ⏳ Waiting for modal to potentially appear...")
            await asyncio.sleep(2)
            
            # Check and close any modal that might have appeared
            try:
                print("   🔍 Checking for modal after delay...")
                modal_locator = page.locator('div.lv-modal-mask')
                await modal_locator.wait_for(state="visible", timeout=3000)
                print("   📱 Modal detected during navigation, closing...")
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)  # Wait for modal close animation
                await modal_locator.wait_for(state="hidden", timeout=5000)
                print("   ✅ Modal closed")
            except:
                print("   ✅ No modal appeared")
            
            # Now wait for networkidle after modal is handled
            print("   ⏳ Waiting for page to be fully loaded...")
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check for gateway timeout
            content = await page.content()
            if "gateway timeout" in content.lower():
                raise Exception("Gateway timeout detected")
                
            print("   ✅ Page loaded successfully")
            return
            
        except Exception as e:
            print(f"   ⚠️  Attempt {attempt + 1} failed: {e}")
            if attempt == max_attempts - 1:
                print("   ❌ All navigation attempts failed")
                raise
            print(f"   🔄 Waiting 3s before retry...")
            await asyncio.sleep(3)

async def handle_modals(page):
    """Handle any modal pop-ups that might appear"""
    print("🔍 Checking for modal pop-ups...")
    
    # Multiple modal selectors to check
    modal_selectors = [
        'div.lv-modal-mask',  # From modal.html
        'div[class*="modal-mask"]',
        'div[class*="modal"]',
        'div[aria-hidden="true"][class*="modal"]'
    ]
    
    modal_found = False
    
    for selector in modal_selectors:
        try:
            modal_locator = page.locator(selector)
            await modal_locator.wait_for(state="visible", timeout=2000)
            print(f"   📱 Modal detected with selector: {selector}")
            
            # Try multiple ways to close modal
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
            # Check if modal is hidden
            await modal_locator.wait_for(state="hidden", timeout=3000)
            print("   ✅ Modal closed successfully")
            modal_found = True
            break
            
        except:
            continue
    
    if not modal_found:
        print("   ✅ No modal detected")

