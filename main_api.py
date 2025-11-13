#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dreamina Multi-Account Image Generator
- Loads prompts from file
- Generates images via API with multiple accounts
- Automatically switches accounts when credits run out
"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Import our modules
from config import (
    COOKIES_FOLDER, PROMPT_FILE, IMAGE_COUNT, CREDITS_PER_GENERATION,
    BROWSER_HEADLESS, get_aspect_ratio_dimensions
)
from cookie_handler import load_accounts
from prompt_loader import load_prompts_from_file
from credit_checker import check_account_credits
from api_generator import generate_image_via_api, download_image, create_retry_session

# Load environment
load_dotenv()

def main():
    print("=" * 80)
    print("🚀 Dreamina Multi-Account Image Generator")
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
    width, height = get_aspect_ratio_dimensions(aspect_ratio)
    print(f"📐 Aspect ratio: {aspect_ratio} ({width}x{height})")
    print(f"🎨 Images per prompt: {IMAGE_COUNT}")
    print(f"💰 Credits per generation: {CREDITS_PER_GENERATION}")
    
    # Setup output directory
    file_stem = Path(prompt_file).stem
    ratio_str = aspect_ratio.replace(":", "-")
    output_dir = Path("generated") / f"{file_stem}_{ratio_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"💾 Output directory: {output_dir}")
    
    # Start browser for credit checking
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
                
                # Process prompts for this account
                session = create_retry_session()
                
                for i, prompt in enumerate(remaining_prompts[:prompts_to_process], 1):
                    print(f"\n   🎨 Prompt {i}/{prompts_to_process} (#{global_prompt_counter})")
                    print(f"      📝 {prompt[:80]}...")
                    
                    # Generate via API
                    image_urls = generate_image_via_api(
                        prompt=prompt,
                        session_id=account['session_id'],
                        width=width,
                        height=height,
                        n=IMAGE_COUNT
                    )
                    
                    if not image_urls:
                        print(f"      ❌ Generation failed, skipping...")
                        continue
                    
                    # Download images
                    for img_idx, url in enumerate(image_urls):
                        letter = chr(ord('A') + img_idx)
                        filename = f"{global_prompt_counter}{letter}_{file_stem}_{ratio_str}.jpeg"
                        output_path = output_dir / filename
                        
                        print(f"      📥 Downloading {filename}...")
                        success = download_image(url, output_path, session)
                        
                        if success:
                            print(f"         ✅ Saved")
                        else:
                            print(f"         ❌ Failed")
                    
                    global_prompt_counter += 1
                
                # Remove processed prompts
                remaining_prompts = remaining_prompts[prompts_to_process:]
                account_index += 1
            
            # Summary
            print(f"\n{'=' * 80}")
            print("🎉 Generation Complete!")
            print(f"{'=' * 80}")
            print(f"✅ Processed: {len(prompts) - len(remaining_prompts)} prompt(s)")
            if remaining_prompts:
                print(f"⚠️  Remaining: {len(remaining_prompts)} prompt(s) (no credits)")
            print(f"💾 Output: {output_dir.resolve()}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    main()
