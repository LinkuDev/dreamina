from playwright.sync_api import Browser, Page, expect, TimeoutError as PlaywrightTimeoutError
from cookie_handler import clean_cookies
from config import DREAMINA_HOME_URL, DREAMINA_CREATIONS_URL, DREAMINA_ROOT_URL, CREDITS_PER_GENERATION, MAX_RETRIES
import time

def safe_navigate_sync(page: Page, target_url: str, max_attempts: int = None):
    """Robust navigation with retries and gateway-timeout detection (sync version)"""
    if max_attempts is None:
        max_attempts = MAX_RETRIES
    
    for attempt in range(max_attempts):
        try:
            if attempt:
                print(f"   🔄 Retry attempt {attempt + 1}/{max_attempts}")
                # First hop to root, then back to target
                page.goto(DREAMINA_ROOT_URL, wait_until="networkidle", timeout=60000)
                time.sleep(3)
            
            # Use networkidle for better page load detection
            page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # Extended wait for page to stabilize
            time.sleep(3)
            
            # Check for gateway timeout in content
            if "gateway timeout" in page.content().lower():
                raise PlaywrightTimeoutError("Gateway timeout detected in HTML")
            
            return
            
        except PlaywrightTimeoutError as e:
            print(f"   ⚠️  Navigation attempt {attempt + 1} failed: {e}")
            if attempt == max_attempts - 1:
                print(f"   ❌ All navigation attempts exhausted")
                raise
            time.sleep(3)

def handle_modal_sync(page: Page):
    """Handle modal pop-ups (sync version)"""
    try:
        modal_locator = page.locator('div[class*="lv-modal-wrapper"]')
        modal_locator.wait_for(state="visible", timeout=5000)
        print("   📱 Modal detected, closing...")
        page.keyboard.press("Escape")
        expect(modal_locator).to_be_hidden(timeout=5000)
        print("   ✅ Modal closed")
        time.sleep(1)
    except PlaywrightTimeoutError:
        # No modal, that's fine
        pass

def check_account_credits(account: dict, browser: Browser = None, existing_context=None) -> int | None:
    """
    Check credits for a specific account with robust navigation and modal handling
    
    Args:
        account: Account dict with 'name', 'cookies', etc.
        browser: Playwright browser instance (required if existing_context not provided)
        existing_context: Existing browser context to reuse (optional)
    
    Returns:
        Number of credits, or None if check failed
    """
    print(f"💰 Checking credits for {account['name']}...")
    context = None
    page = None
    should_close_context = False
    
    try:
        # Use existing context or create new one
        if existing_context:
            context = existing_context
            should_close_context = False  # Don't close existing context
        else:
            if browser is None:
                print(f"   ❌ Browser instance required when not using existing context")
                return None
            
            # Create fresh context with isolated cookies
            context = browser.new_context(
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Clean and add cookies
            cleaned_cookies = clean_cookies(account["cookies"])
            context.add_cookies(cleaned_cookies)
            
            should_close_context = True  # We created it, we close it
        
        page = context.new_page()
        
        # Navigate to home page with retries
        print(f"   🌐 Navigating to home page...")
        safe_navigate_sync(page, DREAMINA_HOME_URL)
        
        # Extended wait for page to settle and UI to load
        print(f"   ⏳ Waiting for page UI to fully load...")
        time.sleep(3)
        
        # Check and close any modal
        handle_modal_sync(page)
        
        # Additional wait after modal handling
        time.sleep(2)
        
        # First, check if there's a Sign in / Login button (means not authenticated)
        print(f"   🔍 Verifying authentication...")
        
        # Check for login/sign-in buttons
        login_button_selectors = [
            'button:has-text("Sign in")',
            'button:has-text("sign in")',
            'button:has-text("Đăng nhập")',
            'button:has-text("đăng nhập")',
            'a:has-text("Sign in")',
            'a:has-text("sign in")',
            'a:has-text("Đăng nhập")',
            'a:has-text("đăng nhập")',
        ]
        
        for selector in login_button_selectors:
            try:
                print(f"   🔍 Checking for login indicator: {selector}")
                element = page.locator(selector)
                # Wait for potential login buttons to appear
                page.wait_for_timeout(1500)
                if element.count() > 0:
                    print(f"   ❌ Not authenticated - found login button: {selector}")
                    return None
            except:
                continue
        
        # Then verify authentication by checking for user avatar/profile
        auth_indicators = [
            'img.dreamina-component-avatar',
            'div.dreamina-component-avatar-container',
        ]
        
        auth_found = False
        for selector in auth_indicators:
            try:
                print(f"   🔍 Looking for auth indicator: {selector}")
                element = page.locator(selector)
                # Wait for authentication elements to load
                page.wait_for_timeout(2000)
                if element.count() > 0:
                    print(f"   ✅ Authenticated (found: {selector})")
                    auth_found = True
                    break
            except:
                continue
        
        if not auth_found:
            print(f"   ❌ Not authenticated - cookies may be invalid")
            return None
        
        # Try to find credits on current page first (home page may have it)
        print(f"   🔍 Looking for credit display on home page...")
        credit_selectors = [
            "div.credit-amount-text-VHUjL3",  # From credit.html
            "div[class*='credit-amount-text']",  # Class pattern match
            "#SiderMenuCredit div[class*='credit-amount']",  # By menu ID
            "div.credit-container-mJtuXc div[class*='credit-amount']",  # Within credit container
        ]
        
        credits = None
        for selector in credit_selectors:
            try:
                print(f"   🔍 Checking credit selector: {selector}")
                credit_element = page.locator(selector).first
                # Extended wait for credit elements
                credit_element.wait_for(state="visible", timeout=8000)
                
                # Try to extract number from text
                text = credit_element.inner_text()
                print(f"   📝 Found text with {selector}: {text}")
                
                # Extract number from text
                import re
                numbers = re.findall(r'\d+', text)
                if numbers:
                    credits = int(numbers[0])
                    print(f"   ✅ Credits: {credits}")
                    break
            except Exception as e:
                print(f"   ⏳ Selector {selector} not found, trying next...")
                continue
        
        # If not found on home, try creations page
        if credits is None:
            print(f"   🌐 Navigating to creations page...")
            safe_navigate_sync(page, DREAMINA_CREATIONS_URL)
            
            # Extended wait for creations page
            print(f"   ⏳ Waiting for creations page to load...")
            time.sleep(3)
            
            # Check and close any modal again
            handle_modal_sync(page)
            
            # Additional wait after modal
            time.sleep(2)
            
            for selector in credit_selectors:
                try:
                    print(f"   🔍 Checking credit on creations: {selector}")
                    credit_element = page.locator(selector).first
                    # Extended wait for credit elements on creations page
                    credit_element.wait_for(state="visible", timeout=10000)
                    
                    text = credit_element.inner_text()
                    print(f"   📝 Found text with {selector}: {text}")
                    
                    import re
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        credits = int(numbers[0])
                        print(f"   ✅ Credits: {credits}")
                        break
                except Exception as e:
                    print(f"   ⏳ Selector {selector} not found on creations...")
                    continue
        
        if credits is None:
            print(f"   ❌ Could not find credit display")
            return None
        
        return credits
        
    except Exception as exc:
        print(f"   ❌ Failed to check credits: {exc}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Ensure clean closure
        if page:
            try:
                page.close()
            except:
                pass
        
        # Only close context if we created it
        if context and should_close_context:
            try:
                context.close()
            except:
                pass
            # Small delay to ensure complete cleanup
            time.sleep(0.5)

def has_enough_credits(account: dict, browser: Browser, required: int = None) -> bool:
    """
    Check if account has enough credits for generation
    
    Args:
        account: Account dict
        browser: Playwright browser instance
        required: Required credits (default: CREDITS_PER_GENERATION)
    
    Returns:
        True if has enough credits
    """
    if required is None:
        required = CREDITS_PER_GENERATION
    
    credits = check_account_credits(account, browser)
    
    if credits is None:
        return False
    
    return credits >= required

def get_max_generations(account: dict, browser: Browser) -> int:
    """
    Calculate how many generations can be done with current credits
    
    Args:
        account: Account dict
        browser: Playwright browser instance
    
    Returns:
        Number of generations possible
    """
    credits = check_account_credits(account, browser)
    
    if credits is None:
        return 0
    
    return credits // CREDITS_PER_GENERATION
