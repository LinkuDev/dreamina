import json
import asyncio
from pathlib import Path
from config import ASPECT_RATIO_MAP

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

async def select_aspect_ratio(page, desired_ratio: str):
    """Select aspect ratio from the UI"""
    try:
        print(f"🎯 Selecting aspect ratio: {desired_ratio}")
        
        # Map user input to HTML value
        if desired_ratio.upper() not in ASPECT_RATIO_MAP:
            print(f"❌ Invalid aspect ratio: {desired_ratio}")
            print(f"   Available options: {list(ASPECT_RATIO_MAP.keys())}")
            return False
        
        html_value = ASPECT_RATIO_MAP[desired_ratio.upper()]
        print(f"   📐 Mapping {desired_ratio} -> '{html_value}'")
        
        # Wait for aspect ratio section to be visible
        radio_group = page.locator('.lv-radio-group')
        await radio_group.wait_for(state="visible", timeout=10000)
        print("   ✅ Found aspect ratio section")
        
        # Find and click the desired ratio
        if html_value == "":
            # Special case for AUTO (empty value)
            ratio_option = page.locator('input[type="radio"][value=""]')
        else:
            ratio_option = page.locator(f'input[type="radio"][value="{html_value}"]')
        
        # Check if option exists
        if await ratio_option.count() == 0:
            print(f"   ❌ Aspect ratio option '{html_value}' not found")
            return False
        
        # Click the option
        await ratio_option.click()
        print(f"   ✅ Clicked aspect ratio: {desired_ratio}")
        
        # Wait a bit for UI to update
        await asyncio.sleep(1)
        
        # Verify selection
        is_checked = await ratio_option.is_checked()
        if is_checked:
            print(f"   ✅ Aspect ratio {desired_ratio} selected successfully")
            return True
        else:
            print(f"   ❌ Failed to select aspect ratio {desired_ratio}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error selecting aspect ratio: {e}")
        return False
