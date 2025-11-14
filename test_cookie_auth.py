#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Playwright với cookie file để verify authentication
Sử dụng logic giống main.py và credit_checker.py
"""

from playwright.sync_api import sync_playwright
import json
import time
from pathlib import Path

# Import modules từ project
from cookie_handler import load_accounts, clean_cookies

def load_cookies_from_file(cookie_file_path: str):
    """Load cookies from file format (session_id on first line, JSON on remaining lines)"""
    try:
        with open(cookie_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        session_id = lines[0].strip()
        json_content = ''.join(lines[1:])
        cookie_data = json.loads(json_content)
        
        print(f"✅ Loaded {len(cookie_data)} cookies from {Path(cookie_file_path).name}")
        print(f"🔑 Session ID: {session_id[:20]}...")
        
        return clean_cookies(cookie_data)
        
    except Exception as e:
        print(f"❌ Error loading cookies: {e}")
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
    
    print(f"🧹 Cleaned {len(cookies)} cookies")
    return cookies

def test_single_account(account: dict, browser):
    """Test authentication cho 1 account với logic giống main.py"""
    print(f"\n{'=' * 80}")
    print(f"👤 Testing Account: {account['name']}")
    print(f"🔑 Session: {account['session_id'][:20]}...")
    print(f"{'=' * 80}")
    
    # Create context với cookies (giống main.py)
    context = browser.new_context(
        locale='en-US',
        timezone_id='America/New_York',
        viewport={'width': 1920, 'height': 1080}
    )
    
    # Add cookies với clean function (giống cookie_handler.py)
    cleaned_cookies = clean_cookies(account['cookies'])
    context.add_cookies(cleaned_cookies)
    page = context.new_page()
    
    auth_status = False
    credits = None
    generation_access = False
    
    try:
        # Navigate to home page với extended timeout
        print("   🌐 Navigating to home page...")
        page.goto("https://dreamina.capcut.com/ai-tool/home", wait_until="networkidle", timeout=45000)
        
        # Wait for page to fully load - longer delay
        print("   ⏳ Waiting for page to fully load...")
        time.sleep(5)
        
        # Apply zoom (giống main.py) - after page loads
        try:
            print("   🔍 Applying zoom...")
            page.evaluate("""
                document.body.style.zoom = '0.75';
                document.documentElement.style.zoom = '0.75';
            """)
            time.sleep(1)
        except Exception as e:
            print(f"   ⚠️  Could not apply zoom: {e}")
        
        # Handle any modal popup first (giống main.py)
        try:
            print("   🔍 Checking for modal popup...")
            modal = page.locator('div[class*="lv-modal-wrapper"]')
            modal.wait_for(state="visible", timeout=3000)
            print("   📱 Modal detected, closing...")
            page.keyboard.press("Escape")
            time.sleep(2)
        except:
            print("   ✅ No modal popup found")
        
        # Wait additional time for UI to stabilize
        print("   ⏳ Waiting for UI to stabilize...")
        time.sleep(3)
        
        # Check authentication (giống credit_checker.py logic)
        print("   🔍 Checking authentication status...")
        
        # Check for login buttons với wait
        login_button_selectors = [
            'button:has-text("Sign in")',
            'button:has-text("sign in")',
            'button:has-text("Đăng nhập")',
            'a:has-text("Sign in")',
        ]
        
        login_found = False
        for selector in login_button_selectors:
            try:
                print(f"   🔍 Checking for login button: {selector}")
                element = page.locator(selector)
                # Wait a bit for element to possibly appear
                page.wait_for_timeout(1000)
                if element.count() > 0:
                    print(f"   ❌ Found login button: {selector}")
                    login_found = True
                    break
            except:
                continue
        
        if login_found:
            print("   ❌ NOT AUTHENTICATED - Found login indicators")
            return {"name": account["name"], "authenticated": False, "credits": None, "generation_access": False}
        
        # Check for user avatar với wait (giống credit_checker.py)
        auth_indicators = [
            'img.dreamina-component-avatar',
            'div.dreamina-component-avatar-container',
        ]
        
        print("   🔍 Looking for authentication indicators...")
        for selector in auth_indicators:
            try:
                print(f"   🔍 Checking for: {selector}")
                element = page.locator(selector)
                # Wait for potential authentication elements
                page.wait_for_timeout(2000)
                if element.count() > 0:
                    print(f"   ✅ AUTHENTICATED - Found: {selector}")
                    auth_status = True
                    break
            except:
                continue
        
        if not auth_status:
            print("   ❌ NOT AUTHENTICATED - No avatar found")
            return {"name": account["name"], "authenticated": False, "credits": None, "generation_access": False}
        
        # Check credits với extended wait (giống credit_checker.py)
        print("   💰 Checking credits on home page...")
        credit_selectors = [
            "div.credit-amount-text-VHUjL3",
            "div[class*='credit-amount-text']",
            "#SiderMenuCredit div[class*='credit-amount']",
            "div.credit-container-mJtuXc div[class*='credit-amount']",
        ]
        
        for selector in credit_selectors:
            try:
                print(f"   🔍 Checking credit selector: {selector}")
                credit_element = page.locator(selector).first
                
                # Extended wait for credit element
                credit_element.wait_for(state="visible", timeout=8000)
                
                text = credit_element.inner_text()
                print(f"   📝 Found credit text: {text}")
                
                import re
                numbers = re.findall(r'\d+', text)
                if numbers:
                    credits = int(numbers[0])
                    print(f"   ✅ Credits: {credits}")
                    break
            except Exception as e:
                print(f"   ⏳ Selector {selector} not found, trying next...")
                continue
        
        # If not found on home, try creations page với extended wait
        if credits is None:
            print("   🌐 Credits not found on home, trying creations page...")
            page.goto("https://dreamina.capcut.com/ai-tool/asset", wait_until="networkidle", timeout=45000)
            
            # Extended wait for creations page to load
            print("   ⏳ Waiting for creations page to load...")
            time.sleep(5)
            
            # Handle modal on creations page
            try:
                modal = page.locator('div[class*="lv-modal-wrapper"]')
                modal.wait_for(state="visible", timeout=3000)
                page.keyboard.press("Escape")
                time.sleep(2)
            except:
                pass
            
            for selector in credit_selectors:
                try:
                    print(f"   🔍 Checking credit on creations: {selector}")
                    credit_element = page.locator(selector).first
                    credit_element.wait_for(state="visible", timeout=10000)
                    
                    text = credit_element.inner_text()
                    print(f"   📝 Found credit text: {text}")
                    
                    import re
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        credits = int(numbers[0])
                        print(f"   ✅ Credits: {credits}")
                        break
                except Exception as e:
                    print(f"   ⏳ Selector {selector} not found on creations...")
                    continue
        
        # Test generation page access với extended wait
        print("   🎨 Testing generation page access...")
        page.goto("https://dreamina.capcut.com/ai-tool/generate?type=image", wait_until="networkidle", timeout=45000)
        
        # Extended wait for generation page
        print("   ⏳ Waiting for generation page to load...")
        time.sleep(5)
        
        # Handle modal on generation page (giống main.py)
        try:
            modal = page.locator('div[class*="lv-modal-wrapper"]')
            modal.wait_for(state="visible", timeout=3000)
            print("   📱 Modal on generation page, closing...")
            page.keyboard.press("Escape")
            time.sleep(2)
        except:
            print("   ✅ No modal on generation page")
        
        # Wait for generation UI to stabilize
        time.sleep(3)
        
        # Check if generation page accessible với wait
        generation_indicators = [
            'button:has-text("Generate")',
            'input[placeholder*="prompt"]',
            'textarea[placeholder*="prompt"]'
        ]
        
        print("   🔍 Checking generation page elements...")
        for selector in generation_indicators:
            try:
                print(f"   🔍 Looking for: {selector}")
                element = page.locator(selector)
                # Wait for generation elements to load
                page.wait_for_timeout(2000)
                if element.count() > 0:
                    print(f"   ✅ Generation accessible - Found: {selector}")
                    generation_access = True
                    break
            except:
                continue
        
        if not generation_access:
            print("   ❌ Generation page not accessible")
        
        return {
            "name": account["name"], 
            "authenticated": auth_status, 
            "credits": credits, 
            "generation_access": generation_access
        }
        
    except Exception as e:
        print(f"   ❌ Error testing account: {e}")
        return {"name": account["name"], "authenticated": False, "credits": None, "generation_access": False}
    
    finally:
        page.close()
        context.close()

def test_all_accounts_in_folder(cookies_folder: str):
    """Test tất cả accounts trong folder với logic giống main.py"""
    print("=" * 80)
    print("🚀 Testing ALL Accounts Authentication & Credits")
    print("=" * 80)
    
    # Load all accounts (giống cookie_handler.py)
    accounts = load_accounts(cookies_folder)
    
    if not accounts:
        print(f"❌ No accounts found in {cookies_folder}")
        return
    
    print(f"📊 Found {len(accounts)} account(s) to test\n")
    
    # Start browser
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Headless mode for faster testing
            args=[
                "--start-maximized",
                "--window-size=1920,1080",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor", 
                "--no-default-browser-check",
                "--disable-extensions",
                "--force-device-scale-factor=1.0",
            ]
        )
        
        results = []
        
        try:
            for i, account in enumerate(accounts, 1):
                print(f"\n🔄 Testing account {i}/{len(accounts)}")
                result = test_single_account(account, browser)
                results.append(result)
                
                # Longer delay between accounts để avoid rate limiting
                if i < len(accounts):
                    print(f"   ⏳ Waiting 5 seconds before next account...")
                    time.sleep(5)
            
            # Summary report (giống main.py style)
            print(f"\n{'=' * 80}")
            print("📊 COMPLETE TEST RESULTS")
            print(f"{'=' * 80}")
            
            authenticated_count = 0
            total_credits = 0
            generation_ready = 0
            
            for result in results:
                status = "✅ AUTH" if result["authenticated"] else "❌ FAIL"
                credits_text = f"{result['credits']} credits" if result["credits"] is not None else "No credits"
                gen_status = "✅ GEN" if result["generation_access"] else "❌ BLOCKED"
                
                print(f"   👤 {result['name']:<15} | {status} | 💰 {credits_text:<12} | {gen_status}")
                
                if result["authenticated"]:
                    authenticated_count += 1
                if result["credits"] is not None:
                    total_credits += result["credits"]
                if result["generation_access"]:
                    generation_ready += 1
            
            print(f"\n📈 SUMMARY:")
            print(f"   ✅ Authenticated: {authenticated_count}/{len(accounts)} accounts")
            print(f"   💰 Total Credits: {total_credits}")
            print(f"   🎨 Generation Ready: {generation_ready}/{len(accounts)} accounts")
            
            if authenticated_count > 0:
                avg_credits = total_credits / authenticated_count
                print(f"   📊 Average Credits: {avg_credits:.1f} per account")
                
                # Calculate max generations possible (giống main.py)
                credits_per_generation = 5
                max_generations = total_credits // credits_per_generation
                print(f"   🚀 Max Generations: {max_generations} total ({credits_per_generation} credits each)")
            
        except Exception as e:
            print(f"\n❌ Error during bulk test: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

def test_authentication(cookie_file: str):
    """Test authentication với single cookie file (backward compatibility)"""
    print("=" * 60)
    print("🚀 Testing Single Cookie File")
    print("=" * 60)
    
    # Load cookies
    cookies = load_cookies_from_file(cookie_file)
    if not cookies:
        print("❌ No cookies loaded, exiting")
        return
    
    # Create fake account object to reuse test_single_account function
    account = {
        "name": Path(cookie_file).stem,
        "session_id": "manual_test",
        "cookies": cookies
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Headless mode for faster testing
            args=[
                "--start-maximized",
                "--window-size=1920,1080",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--no-default-browser-check", 
                "--disable-extensions",
                "--force-device-scale-factor=1.0",
            ]
        )
        
        try:
            result = test_single_account(account, browser)
            
            print(f"\n{'=' * 60}")
            print("📊 SINGLE FILE TEST RESULT")
            print(f"{'=' * 60}")
            print(f"👤 Account: {result['name']}")
            print(f"� Authentication: {'✅ SUCCESS' if result['authenticated'] else '❌ FAILED'}")
            print(f"💰 Credits: {result['credits'] if result['credits'] is not None else 'Not found'}")
            print(f"🎨 Generation Access: {'✅ YES' if result['generation_access'] else '❌ NO'}")
            
        except Exception as e:
            print(f"\n❌ Error during single test: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

if __name__ == "__main__":
    import sys
    
    # Check arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        # If argument is a folder, test all accounts in folder
        if Path(arg).is_dir():
            test_all_accounts_in_folder(arg)
        
        # If argument is a file, test single file
        elif Path(arg).is_file():
            test_authentication(arg)
        
        else:
            print(f"❌ Path not found: {arg}")
            print("Usage:")
            print("  python test_cookie_auth.py cookies1/          # Test all in folder")
            print("  python test_cookie_auth.py cookies1/A.json    # Test single file")
            sys.exit(1)
    
    else:
        # Default: test all folders
        folders_to_test = ['cookies1', 'cookies2', 'cookies3']
        
        for folder in folders_to_test:
            if Path(folder).exists():
                print(f"\n🎯 Testing folder: {folder}")
                test_all_accounts_in_folder(folder)
                print("\n" + "="*80 + "\n")
            else:
                print(f"⚠️  Folder not found: {folder}")
        
        print("🎉 All tests completed!")
