import asyncio

async def check_authentication_status(page):
    """Check if user is authenticated by looking for specific indicators"""
    print("🔍 Checking authentication status...")
    
    # Primary auth indicators - user avatar and profile menu
    primary_indicators = {
        'user_avatar': [
            'img.dreamina-component-avatar',  # User avatar image
            'div.dreamina-component-avatar-container',  # Avatar container
        ],
        'user_profile': [
            'div.avatar-container-pWp6gd',  # Avatar wrapper
        ]
    }
    
    # Secondary auth indicators - credits and UI elements
    secondary_indicators = {
        'credits': [
            'span:has-text("Credits:")',
            'div:has-text("Credits")',
            'text="Credits"'
        ],
        'user_interface': [
            'button:has-text("Generate")',
            'textarea[placeholder*="prompt"]',
        ]
    }
    
    # Check for login indicators (negative auth)
    login_indicators = [
        'button:has-text("Log in")',
        'button:has-text("Đăng nhập")',
        'button:has-text("Sign in")',
        'text="Please log in"',
        'text="Login required"'
    ]
    
    print("   🔍 Checking for login indicators...")
    
    # Check login buttons first (if found, definitely not authenticated)
    for selector in login_indicators:
        try:
            login_element = page.locator(selector)
            if await login_element.count() > 0:
                print(f"   ❌ Found login indicator: {selector}")
                return False, "Login button found"
        except:
            continue
    
    print("   ✅ No login indicators found")
    print("   🔍 Checking for user profile/avatar...")
    
    # Check primary authentication indicators (avatar/profile)
    auth_found = False
    auth_details = []
    
    for category, selectors in primary_indicators.items():
        for selector in selectors:
            try:
                element = page.locator(selector)
                count = await element.count()
                if count > 0:
                    print(f"   ✅ Found {category} indicator: {selector} ({count} elements)")
                    auth_found = True
                    auth_details.append(f"{category}: {selector}")
                    
                    # Try to get avatar src for verification
                    if 'avatar' in selector.lower() and 'img' in selector:
                        try:
                            src = await element.first.get_attribute('src', timeout=2000)
                            if src:
                                print(f"      🖼️  Avatar URL: {src[:60]}...")
                        except:
                            pass
            except Exception as e:
                continue
    
    # If primary indicators found, user is authenticated
    if auth_found:
        print("   ✅ User appears to be authenticated (avatar/profile found)")
        return True, f"Auth indicators: {', '.join(auth_details)}"
    
    print("   🔍 Checking secondary indicators (credits/UI)...")
    
    # Check secondary indicators if primary not found
    for category, selectors in secondary_indicators.items():
        for selector in selectors:
            try:
                element = page.locator(selector)
                count = await element.count()
                if count > 0:
                    print(f"   ✅ Found {category} indicator: {selector} ({count} elements)")
                    auth_found = True
                    auth_details.append(f"{category}: {selector}")
                    
                    # Try to get text content for credits
                    if 'credit' in category.lower():
                        try:
                            text = await element.first.text_content(timeout=2000)
                            print(f"      📊 Content: {text}")
                        except:
                            pass
            except Exception as e:
                continue
    
    if auth_found:
        print("   ✅ User appears to be authenticated")
        return True, f"Auth indicators: {', '.join(auth_details)}"
    else:
        print("   ❓ No clear authentication indicators found")
        return False, "No authentication indicators detected"

async def wait_for_page_load(page, timeout: int = 15000):
    """Wait for page to fully load"""
    print("⏳ Waiting for page to fully load...")
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        print("   ✅ Page loaded successfully")
    except Exception as e:
        print(f"   ⚠️  Page load timeout: {e}")
        # Continue anyway, page might still be usable
