#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dreamina Multi-Account Image Generator (UI-based)
- Loads prompts from file
- Generates images via UI interaction with Playwright
- Automatically switches accounts when credits run out
"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import time

# Import our modules
from config import (
    COOKIES_FOLDER, PROMPT_FILE, IMAGE_COUNT, CREDITS_PER_GENERATION,
    BROWSER_HEADLESS, TARGET_URL
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
    
    # Get aspect ratio from env
    aspect_ratio = os.getenv('ASPECT_RATIO', '16:9')
    print(f"📐 Aspect ratio: {aspect_ratio}")
    print(f"🎨 Images per prompt: {IMAGE_COUNT}")
    print(f"💰 Credits per generation: {CREDITS_PER_GENERATION}")
    
    # Start browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=BROWSER_HEADLESS)
        
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
                    timezone_id='America/New_York'
                )
                context.add_cookies(clean_cookies(account["cookies"]))
                page = context.new_page()
                
                try:
                    # Navigate to generation page
                    print(f"\n   🌐 Navigating to generation page...")
                    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(2)
                    
                    # Handle any modal
                    try:
                        modal = page.locator('div[class*="lv-modal-wrapper"]')
                        modal.wait_for(state="visible", timeout=3000)
                        page.keyboard.press("Escape")
                        time.sleep(1)
                    except:
                        pass
                    
                    # Process prompts for this account (one by one with credit check)
                    processed_count = 0
                    
                    for i, prompt in enumerate(remaining_prompts[:prompts_to_process], 1):
                        print(f"\n   {'─' * 60}")
                        print(f"   🎨 Prompt {i}/{prompts_to_process} (#{global_prompt_counter})")
                        
                        # Generate via UI
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
                            time.sleep(2)  # Wait for credit update
                            
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
