#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dreamina Multi-Account Image Generator (UI-based)
- Loads prompts from file
- Generates images via UI interaction with Playwright
- Automatically switches accounts when credits run out
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dreamina Multi-Account Image Generator (UI-based)
- Loads prompts from file
- Generates images via UI interaction with Playwright
- Automatically switches accounts when credits run out
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dreamina Multi-Account Image Generator (UI-based)
- Loads prompts from file
- Generates images via UI interaction with Playwright
- Automatically switches accounts when credits run out
"""

# IMPORT ENCODING FIX TRƯỚC TIÊN - TRIỆT ĐỂ FIX
from encoding_fix import safe_print
import builtins
builtins.print = safe_print  # Override print globally

import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import time

# Import our modules
from config import (
    COOKIES_FOLDER, PROMPT_FILE, IMAGE_COUNT, CREDITS_PER_GENERATION,
    BROWSER_HEADLESS, TARGET_URL, BROWSER_ARGS, BROWSER_VIEWPORT, BROWSER_ZOOM_LEVEL
)
from cookie_handler import load_accounts, clean_cookies
from prompt_loader import load_prompts_from_file
from credit_checker import check_account_credits
from ui_generator import generate_image_via_ui

# Load environment
load_dotenv()

def main():
    print("=" * 80)
    print("🚀 Dreamina Multi-Account Image Generator (UI-based)")
    print("=" * 80)
    
    # Load accounts
    accounts = load_accounts(COOKIES_FOLDER)
    if not accounts:
        print("❌ No accounts found. Exiting.")
        return
    
    # Get prompt file from env or ask user
    prompt_file = PROMPT_FILE
    if not prompt_file:
        prompt_file = input("📁 Enter prompt file path: ").strip("'\"")
    
    if not prompt_file or not Path(prompt_file).exists():
        print(f"❌ Prompt file not found: {prompt_file}")
        return
    
    # Load prompts
    try:
        prompts = load_prompts_from_file(prompt_file)
    except Exception as exc:
        print(f"❌ Error loading prompts: {exc}")
        return
    
    if not prompts:
        print("❌ No prompts found")
        return
    
    print(f"\n📝 Total prompts to generate: {len(prompts)}")
    
    # Get aspect ratio from env (will be single ratio per worker, set by launcher)
    aspect_ratio = os.getenv('ASPECT_RATIO', '16:9')
    print(f"📐 Aspect ratio: {aspect_ratio}")
    print(f"🎨 Images per prompt: {IMAGE_COUNT}")
    print(f"💰 Credits per generation: {CREDITS_PER_GENERATION}")
    
    # Start browser
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=BROWSER_HEADLESS,
            args=BROWSER_ARGS
        )
        
        try:
            remaining_prompts = prompts[:]
            account_index = 0
            global_prompt_counter = 1
            
            while remaining_prompts and account_index < len(accounts):
                account = accounts[account_index]
                
                print(f"\n{'=' * 80}")
                print(f"👤 Account: {account['name']}")
                print(f"{'=' * 80}")
                
                # Check credits
                credits = check_account_credits(account, browser)
                if credits is None or credits < CREDITS_PER_GENERATION:
                    print(f"   ⚠️  Insufficient credits, switching account...")
                    account_index += 1
                    continue
                
                # Calculate how many prompts this account can handle
                max_generations = credits // CREDITS_PER_GENERATION
                prompts_to_process = min(max_generations, len(remaining_prompts))
                
                print(f"   💰 Available credits: {credits}")
                print(f"   📊 Can process: {prompts_to_process} prompt(s)")
                
                # Create browser context for this account
                context = browser.new_context(
                    locale='en-US',
                    timezone_id='America/New_York',
                    viewport=BROWSER_VIEWPORT  # Full HD viewport
                )
                context.add_cookies(clean_cookies(account["cookies"]))
                page = context.new_page()
                
                try:
                    # Navigate to generation page
                    print(f"\n   🌐 Navigating to generation page...")
                    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                    
                    # Extended wait for page to load completely
                    print(f"   ⏳ Waiting for generation page to fully load...")
                    time.sleep(4)
                    
                    # Ensure we're on the correct generation URL before proceeding
                    generation_url = "https://dreamina.capcut.com/ai-tool/generate?type=image"
                    current_url = page.url
                    if generation_url not in current_url:
                        print(f"   🔄 Not on generation page, navigating to: {generation_url}")
                        page.goto(generation_url, wait_until="domcontentloaded", timeout=60000)
                        time.sleep(3)
                        print(f"   ✅ Now on generation page")
                    else:
                        print(f"   ✅ Already on generation page")
                    
                    # Apply zoom after page loads for better image quality
                    try:
                        print(f"   🔍 Applying {int(BROWSER_ZOOM_LEVEL * 100)}% zoom for sharper images...")
                        page.evaluate(f"""
                            document.body.style.zoom = '{BROWSER_ZOOM_LEVEL}';
                            document.documentElement.style.zoom = '{BROWSER_ZOOM_LEVEL}';
                        """)
                        time.sleep(2)  # Extended wait after zoom
                    except Exception as e:
                        print(f"   ⚠️  Could not apply zoom: {e}")
                    
                    # Handle any modal
                    try:
                        modal = page.locator('div[class*="lv-modal-wrapper"]')
                        modal.first.wait_for(state="visible", timeout=3000)
                        print("   📱 Modal detected, closing...")
                        
                        # Handle multiple modals by closing them one by one
                        modal_count = modal.count()
                        print(f"   📱 Found {modal_count} modal(s)")
                        
                        for i in range(modal_count):
                            try:
                                # Press Escape to close modals
                                page.keyboard.press("Escape")
                                time.sleep(0.5)  # Small delay between key presses
                            except Exception as e:
                                print(f"   ⚠️  Error closing modal {i+1}: {e}")
                        
                        # Wait for all modals to disappear
                        try:
                            # Wait for the modals to be hidden with a reasonable timeout
                            page.wait_for_function(
                                "() => document.querySelectorAll('div[class*=\"lv-modal-wrapper\"]').length === 0 || "
                                "Array.from(document.querySelectorAll('div[class*=\"lv-modal-wrapper\"]')).every(el => "
                                "getComputedStyle(el).display === 'none' || getComputedStyle(el).visibility === 'hidden')",
                                timeout=5000
                            )
                            print("   ✅ All modals closed")
                        except PlaywrightTimeoutError:
                            print("   ⚠️  Some modals may still be visible")
                        
                        time.sleep(2)  # Extended wait after modal close
                    except:
                        pass
                    
                    # Additional wait for UI to stabilize
                    print("   ⏳ Waiting for UI to stabilize...")
                    time.sleep(3)
                    
                    # Verify we're on the generation page and UI is ready
                    print("   🔍 Verifying page state...")
                    try:
                        # Wait for key UI elements to be present
                        page.wait_for_function(
                            "() => document.readyState === 'complete'",
                            timeout=10000
                        )
                        
                        # Check if we can find any generation-related elements
                        ui_indicators = [
                            'textarea[placeholder*="prompt"]',
                            'textarea[placeholder*="描述"]',
                            'button[class*="button"]',
                            'div[class*="ratio"]'
                        ]
                        
                        found_ui = False
                        for selector in ui_indicators:
                            try:
                                if page.locator(selector).count() > 0:
                                    print(f"   ✅ Found UI element: {selector}")
                                    found_ui = True
                                    break
                            except:
                                continue
                        
                        if not found_ui:
                            print("   ⚠️  No UI elements found, but continuing anyway...")
                        else:
                            print("   ✅ Page UI is ready for interaction")
                        
                    except Exception as e:
                        print(f"   ⚠️  UI verification failed: {e}, but continuing...")
                    
                    # Process prompts for this account (one by one with credit check)
                    processed_count = 0
                    
                    for i, prompt in enumerate(remaining_prompts[:prompts_to_process], 1):
                        print(f"\n   {'─' * 60}")
                        print(f"   🎨 Prompt {i}/{prompts_to_process} (#{global_prompt_counter})")
                        
                        # Ensure we're on the correct generation URL before each generation
                        generation_url = "https://dreamina.capcut.com/ai-tool/generate?type=image"
                        current_url = page.url
                        if generation_url not in current_url:
                            print(f"   🔄 Redirected away, navigating back to: {generation_url}")
                            page.goto(generation_url, wait_until="domcontentloaded", timeout=60000)
                            time.sleep(5)  # Longer wait for page to load completely
                            
                            # Handle modals again after navigation
                            try:
                                modal = page.locator('div[class*="lv-modal-wrapper"]')
                                modal.first.wait_for(state="visible", timeout=3000)
                                print("   📱 Modal detected after navigation, closing...")
                                modal_count = modal.count()
                                for i in range(modal_count):
                                    page.keyboard.press("Escape")
                                    time.sleep(0.5)
                                time.sleep(2)
                            except:
                                pass
                            
                            print(f"   ✅ Back on generation page")
                        
                        # Additional verification that page is ready
                        print("   🔍 Verifying page is ready for generation...")
                        try:
                            page.wait_for_function(
                                "() => document.readyState === 'complete'",
                                timeout=5000
                            )
                            time.sleep(1)  # Extra stabilization time
                        except:
                            print("   ⚠️  Page readiness check failed, continuing anyway...")
                        
                        # Generate via UI (aspect_ratio is fixed per worker)
                        success = generate_image_via_ui(page, prompt, aspect_ratio)
                        
                        if success:
                            print(f"   ✅ Generation #{global_prompt_counter} completed")
                            processed_count += 1
                        else:
                            print(f"   ❌ Generation #{global_prompt_counter} failed")
                        
                        global_prompt_counter += 1
                        
                        # Check credit after generation (before processing next prompt)
                        if i < prompts_to_process:
                            print(f"\n   💰 Checking remaining credits...")
                            time.sleep(3)  # Extended wait for credit update
                            
                            # Check credit by navigating to user profile
                            try:
                                remaining_credits = check_account_credits(account, browser, existing_context=context)
                                
                                if remaining_credits is None:
                                    print(f"   ⚠️  Could not check credits, continuing anyway...")
                                elif remaining_credits < CREDITS_PER_GENERATION:
                                    print(f"   ⚠️  Insufficient credits ({remaining_credits} < {CREDITS_PER_GENERATION})")
                                    print(f"   🔄 Stopping this account, will switch to next...")
                                    break  # Exit loop to switch account
                                else:
                                    print(f"   ✅ Remaining credits: {remaining_credits} (enough for next gen)")
                            except Exception as e:
                                print(f"   ⚠️  Error checking credits: {e}")
                                print(f"   ⚠️  Continuing anyway...")
                            
                            # Wait between generations
                            print(f"   ⏳ Waiting 3s before next generation...")
                            time.sleep(3)
                    
                    # Remove processed prompts
                    remaining_prompts = remaining_prompts[processed_count:]
                    
                except Exception as e:
                    print(f"   ❌ Error during generation: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    page.close()
                    context.close()
                    time.sleep(1)  # Cleanup delay
                
                account_index += 1
            
            # Summary
            print(f"\n{'=' * 80}")
            print("🎉 Generation Complete!")
            print(f"{'=' * 80}")
            print(f"✅ Processed: {len(prompts) - len(remaining_prompts)} prompt(s)")
            if remaining_prompts:
                print(f"⚠️  Remaining: {len(remaining_prompts)} prompt(s) (no credits)")
            
        finally:
            browser.close()

if __name__ == "__main__":
    main()
