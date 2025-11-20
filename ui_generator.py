"""
UI-based image generation using Playwright
Clicks through the UI to generate images instead of using API
"""
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
import time
import os

def click_generate_button(page: Page) -> bool:
    """Click the generate button to open prompt input"""
    try:
        print("   🖱️  Clicking generate button...")
        button_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div[2]/div[1]/button"
        
        button = page.locator(f'xpath={button_xpath}')
        button.wait_for(state="visible", timeout=10000)
        button.click()
        
        print("   ✅ Clicked generate button")
        time.sleep(1)
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to click generate button: {e}")
        return False

def select_aspect_ratio_and_submit(page: Page, desired_ratio: str, prompt: str, max_retries: int = 3) -> bool:
    """
    Complete flow: Open aspect ratio selector, choose ratio, input prompt, and submit
    With retry logic - will refresh page and retry if aspect ratio selection fails
    
    Args:
        page: Playwright page (must be on generation page)
        desired_ratio: Aspect ratio like "16:9", "1:1", etc.
        prompt: Text prompt for generation
        max_retries: Maximum number of retry attempts
    """
    
    # Workaround: If desired_ratio contains comma-separated values, take the first one
    if ',' in desired_ratio:
        original_ratio = desired_ratio
        desired_ratio = desired_ratio.split(',')[0].strip()
        print(f"   🔧 Workaround: Split '{original_ratio}' -> using first item '{desired_ratio}'")
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"\n   🔄 Retry attempt {attempt + 1}/{max_retries}...")
                print("   🔄 Refreshing page...")
                page.reload(wait_until="domcontentloaded")
                time.sleep(3)  # Wait for page to fully load
            
            print(f"   📐 Processing aspect ratio: {desired_ratio}...")
            
            # Close any existing popups/modals before starting
            print("   🚪 Closing any existing popups/modals...")
            close_modal(page)
            
            # Set localStorage to prevent app download modal
            try:
                print("   🔧 Setting localStorage to prevent app download modal...")
                page.evaluate("() => { localStorage.setItem('app_download_modal_first_screen_shown', 'true'); }")
            except Exception as e:
                print(f"   ⚠️  Failed to set localStorage: {e}")
            
            # Step 1: Click directly on "High (2K)" or "Cao (2K)" text to open aspect ratio dropdown
            print("   🖱️  Looking for 'High (2K)' or 'Cao (2K)' text to click...")
            
            # Simple approach - click directly on the text (support both English and Vietnamese)
            high_2k_selectors = [
                ':text("High (2K)")',           # Direct text selector (English)
                ':text("Cao (2K)")',            # Direct text selector (Vietnamese)
                'text=High (2K)',               # Playwright text selector (English)
                'text=Cao (2K)',                # Playwright text selector (Vietnamese)
                ':text-is("High (2K)")',        # Exact text match (English)
                ':text-is("Cao (2K)")',         # Exact text match (Vietnamese)
                '*:has-text("High (2K)")',      # Any element containing text (English)
                '*:has-text("Cao (2K)")',       # Any element containing text (Vietnamese)
                'button:has-text("High (2K)")', # Button containing text (English)
                'button:has-text("Cao (2K)")',  # Button containing text (Vietnamese)
                'span:has-text("High (2K)")',   # Span containing text (English)
                'span:has-text("Cao (2K)")',    # Span containing text (Vietnamese)
                'div:has-text("High (2K)")',    # Div containing text (English)
                'div:has-text("Cao (2K)")',     # Div containing text (Vietnamese)
            ]
            
            clicked_high_2k = False
            
            for selector in high_2k_selectors:
                try:
                    print(f"   🔍 Trying to click: {selector}")
                    element = page.locator(selector).first
                    
                    # Wait for element to be visible
                    element.wait_for(state="visible", timeout=5000)
                    
                    if element.count() > 0:
                        print(f"   ✅ Found 'High (2K)' or 'Cao (2K)' element, clicking...")
                        element.click()
                        print("   ✅ Clicked 'High (2K)' or 'Cao (2K)' to open dropdown")
                        clicked_high_2k = True
                        time.sleep(1)  # Wait for dropdown animation
                        break
                        
                except Exception as e:
                    print(f"   ⏳ Selector failed: {str(e)[:50]}...")
                    continue
            
            if not clicked_high_2k:
                print("   ❌ Could not find or click 'High (2K)' or 'Cao (2K)' text!")
                if attempt < max_retries - 1:
                    continue
                else:
                    return False
            
            # Step 2: After clicking "High (2K)" or "Cao (2K)", look for aspect ratio options
            print(f"   🔍 Looking for aspect ratio options in dropdown...")
            time.sleep(0.8)  # Brief wait for dropdown animation
            
            # Step 3: Click directly on the desired ratio text
            print(f"   🎯 Looking for aspect ratio: {desired_ratio}...")
            
            # Simple approach - click directly on the ratio text
            ratio_text_selectors = [
                f':text("{desired_ratio}")',           # Direct text selector
                f'text={desired_ratio}',               # Playwright text selector  
                f':text-is("{desired_ratio}")',        # Exact text match
                f'*:has-text("{desired_ratio}")',      # Any element containing ratio text
                f'label:has-text("{desired_ratio}")',  # Label containing ratio text
                f'span:has-text("{desired_ratio}")',   # Span containing ratio text
                f'div:has-text("{desired_ratio}")',    # Div containing ratio text
                f'button:has-text("{desired_ratio}")', # Button containing ratio text
            ]
            
            clicked_ratio = False
            
            for selector in ratio_text_selectors:
                try:
                    print(f"   🔍 Trying to click ratio: {selector}")
                    element = page.locator(selector).first
                    
                    # Wait for element to be visible
                    element.wait_for(state="visible", timeout=3000)
                    
                    if element.count() > 0:
                        print(f"   ✅ Found '{desired_ratio}' text, preparing to click...")
                        
                        # Scroll element into view
                        element.scroll_into_view_if_needed()
                        
                        # Hover over element
                        print(f"   🎯 Hovering and clicking '{desired_ratio}'...")
                        element.hover()
                        time.sleep(0.3)  # Brief hover delay
                        
                        # Click with left mouse button explicitly
                        element.click(button="left")
                        
                        print(f"   ✅ Clicked aspect ratio: {desired_ratio}")
                        clicked_ratio = True
                        time.sleep(1)  # Wait for selection to register
                        break
                        
                except Exception as e:
                    print(f"   ⏳ Selector failed: {str(e)[:50]}...")
                    continue
            
            # Critical check - MUST select aspect ratio to continue
            if not clicked_ratio:
                print(f"   ❌ Could not select aspect ratio! Will retry...")
                if attempt < max_retries - 1:
                    continue  # Retry from beginning
                else:
                    print(f"   ❌ Failed after {max_retries} attempts!")
                    return False
            
            # Step 4: Input prompt into textarea
            print(f"   ✍️  Entering prompt: {prompt[:60]}...")
            
            # Find textarea by multiple simple selectors
            textarea_selectors = [
                'textarea[placeholder*="prompt"]',     # Textarea with prompt in placeholder
                'textarea[placeholder*="Prompt"]',     # Textarea with Prompt in placeholder
                'textarea[placeholder*="描述"]',        # Chinese placeholder
                'textarea',                            # Any textarea
            ]
            
            textarea_found = False
            
            for selector in textarea_selectors:
                try:
                    print(f"   🔍 Looking for textarea with: {selector}")
                    textarea = page.locator(selector).first
                    
                    if textarea.count() > 0:
                        print(f"   ✅ Found textarea")
                        textarea.click()
                        time.sleep(0.5)  # Wait for focus
                        textarea.fill(prompt)
                        print("   ✅ Entered prompt")
                        textarea_found = True
                        time.sleep(1)  # Wait for text to register
                        break
                        
                except Exception as e:
                    print(f"   ⏳ Textarea selector failed: {str(e)[:50]}...")
                    continue
            
            if not textarea_found:
                print("   ❌ Could not find textarea!")
                if attempt < max_retries - 1:
                    continue
                else:
                    return False
            
            # Step 5: Click the submit button
            print("   🚀 Looking for submit button...")
            
            # Try the specific XPath first
            submit_clicked = False
            specific_submit_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div[2]/div[2]/div[2]/button"
            
            try:
                print(f"   🔍 Trying specific XPath: {specific_submit_xpath}")
                submit_button = page.locator(f'xpath={specific_submit_xpath}')
                
                if submit_button.count() > 0:
                    print(f"   ✅ Found submit button via specific XPath")
                    time.sleep(0.5)  # Brief wait before checking
                    
                    # Check if button is enabled
                    is_disabled = submit_button.get_attribute("disabled")
                    if is_disabled:
                        print("   ⚠️  Submit button is disabled, waiting...")
                        time.sleep(2)  # Wait for button to enable
                        is_disabled = submit_button.get_attribute("disabled")
                        if not is_disabled:
                            print("   ✅ Submit button is now enabled")
                        else:
                            print("   ⚠️  Submit button still disabled, will try other selectors...")
                            raise Exception("Button still disabled")
                    
                    # Click submit
                    print("   🖱️  Clicking submit button...")
                    submit_button.scroll_into_view_if_needed()
                    time.sleep(0.5)  # Brief scroll delay
                    
                    try:
                        submit_button.click()
                    except Exception as e:
                        print(f"   ⚠️  First click failed, trying force click: {e}")
                        submit_button.click(force=True)
                    
                    print("   ✅ Clicked submit button (XPath)")
                    submit_clicked = True
                    
            except Exception as e:
                print(f"   ⚠️  Specific XPath failed: {str(e)[:50]}...")
            
            # If specific XPath didn't work, try other selectors
            if not submit_clicked:
                print("   🔄 Trying alternative submit selectors...")
                
                # Find submit button by text or type
                submit_selectors = [
                    'button[class*="submit-button"]',
                    'button:has-text("Generate")',         # Generate button
                    'button:has-text("Submit")',           # Submit button
                    'button:has-text("Tạo")',              # Vietnamese Generate
                    'button[type="submit"]',               # Submit type button
                    'button:has-text("生成")',              # Chinese Generate
                    'input[type="submit"]',                # Submit input
                    'button[class*="submit"]',             # Button with submit in class
                    'button[class*="generate"]',           # Button with generate in class
                ]
                
                for selector in submit_selectors:
                    try:
                        print(f"   🔍 Looking for submit with: {selector}")
                        submit_button = page.locator(selector).first
                        submit_button.wait_for(state="visible", timeout=5000)
                        
                        if submit_button.count() > 0:
                            print(f"   ✅ Found submit button")
                            time.sleep(0.5)  # Brief wait before checking
                            
                            # Check if button is enabled
                            is_disabled = submit_button.get_attribute("disabled")
                            if is_disabled:
                                print("   ⚠️  Submit button is disabled, waiting...")
                                time.sleep(2)  # Wait for enable
                                is_disabled = submit_button.get_attribute("disabled")
                                if is_disabled:
                                    print("   ❌ Submit button still disabled, trying next selector...")
                                    continue
                            
                            # Click submit
                            print("   🖱️  Clicking submit button...")
                            submit_button.scroll_into_view_if_needed()
                            time.sleep(0.5)  # Brief scroll delay
                            
                            try:
                                submit_button.click()
                            except Exception as e:
                                print(f"   ⚠️  First click failed, trying force click: {e}")
                                submit_button.click(force=True)
                            
                            print("   ✅ Clicked submit button")
                            submit_clicked = True
                            break
                            
                    except Exception as e:
                        print(f"   ⏳ Submit selector failed: {str(e)[:50]}...")
                        continue
            
            if not submit_clicked:
                print("   ❌ Could not find or click submit button!")
                if attempt < max_retries - 1:
                    continue
                else:
                    return False
            
            # Success!
            return True
            
        except Exception as e:
            print(f"   ❌ Error in attempt {attempt + 1}: {e}")
            import traceback
            traceback.print_exc()
            
            if attempt < max_retries - 1:
                print(f"   🔄 Will refresh and retry...")
                continue
            else:
                print(f"   ❌ Failed after {max_retries} attempts!")
                return False
    
    return False

def input_prompt_and_generate(page: Page, prompt: str) -> bool:
    """
    Input prompt and click generate button
    
    Args:
        page: Playwright page
        prompt: Text prompt for generation
    """
    try:
        print(f"   ✍️  Entering prompt: {prompt[:60]}...")
        
        # Wait before starting
        time.sleep(1)
        
        # Find and fill textarea
        textarea_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div[1]/div[2]/div/textarea"
        textarea = page.locator(f'xpath={textarea_xpath}')
        textarea.wait_for(state="visible", timeout=10000)
        
        # Click to focus first
        textarea.click()
        time.sleep(0.5)
        
        # Clear existing text and input new prompt
        textarea.fill(prompt)
        print("   ✅ Entered prompt")
        time.sleep(1)  # Wait after entering text
        
        # Click submit button
        print("   🚀 Preparing to click submit button...")
        submit_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div[2]/div[2]/div[2]/button"
        submit_button = page.locator(f'xpath={submit_xpath}')
        
        # Wait for button to be ready
        submit_button.wait_for(state="visible", timeout=10000)
        time.sleep(0.5)
        
        # Check if button is enabled
        is_disabled = submit_button.get_attribute("disabled")
        if is_disabled:
            print("   ⚠️  Submit button is disabled, waiting...")
            # Wait a bit and check again
            time.sleep(2)
            is_disabled = submit_button.get_attribute("disabled")
            if is_disabled:
                print("   ❌ Submit button still disabled")
                return False
        
        # Scroll button into view if needed
        submit_button.scroll_into_view_if_needed()
        time.sleep(0.5)
        
        # Click with retry
        print("   🖱️  Clicking submit button...")
        try:
            submit_button.click()
        except Exception as e:
            print(f"   ⚠️  First click failed, trying force click: {e}")
            submit_button.click(force=True)
        
        print("   ✅ Clicked submit button")
        time.sleep(2)  # Wait after clicking submit
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to input prompt and generate: {e}")
        import traceback
        traceback.print_exc()
        return False

def wait_for_generation_complete(page: Page, timeout: int = 120) -> bool:
    """
    Wait for image generation to complete
    
    Args:
        page: Playwright page
        timeout: Maximum time to wait in seconds
    """
    try:
        print("   ⏳ Waiting for generation to complete...")
        
        # Look for completion indicators
        # This might be a "Download" button, generated images, or status message
        completion_selectors = [
            'button:has-text("Download")',
            'div[class*="generated"]',
            'img[class*="result"]',
            'div:has-text("Generation complete")',
        ]
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            for selector in completion_selectors:
                try:
                    element = page.locator(selector)
                    if element.count() > 0:
                        print("   ✅ Generation appears to be complete")
                        return True
                except:
                    pass
            
            # Check if there's an error message
            error_selectors = [
                'div:has-text("Error")',
                'div:has-text("Failed")',
                'div[class*="error"]',
            ]
            
            for selector in error_selectors:
                try:
                    element = page.locator(selector)
                    if element.count() > 0:
                        print("   ❌ Generation failed with error")
                        return False
                except:
                    pass
            
            time.sleep(2)
        
        print("   ⏰ Timeout waiting for generation")
        return False
        
    except Exception as e:
        print(f"   ❌ Error waiting for generation: {e}")
        return False

def generate_image_via_ui(page: Page, prompt: str, aspect_ratio: str = None, output_dir: str = None) -> bool:
    """
    Complete flow to generate image via UI and download results
    
    Args:
        page: Playwright page (must be on generation page)
        prompt: Text prompt
        aspect_ratio: Aspect ratio like "16:9" (optional, uses env if not provided)
        output_dir: Directory to save downloaded images (optional, uses OUTPUT_DIR env if not provided)
    
    Returns:
        True if generation and download succeeded
    """
    try:
        # Get aspect ratio from env if not provided
        if aspect_ratio is None:
            aspect_ratio = os.getenv('ASPECT_RATIO', '16:9')
        
        # Get output dir from env if not provided
        if output_dir is None:
            output_dir = os.getenv('OUTPUT_DIR', 'outputs')
        
        print(f"\n🎨 Generating via UI...")
        print(f"   📝 Prompt: {prompt[:80]}...")
        print(f"   📐 Aspect Ratio: {aspect_ratio}")
        print(f"   📁 Output Dir: {output_dir}")
        
        # Step 1: Select aspect ratio and submit
        if not select_aspect_ratio_and_submit(page, aspect_ratio, prompt):
            print("   ❌ Failed to select aspect ratio and submit!")
            return False
        
        # Step 2: Wait for generation and download images
        if not wait_and_download_images(page, prompt, aspect_ratio, output_dir):
            print("   ❌ Failed to download images!")
            return False
        
        print("   ✅ Generation and download completed successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        return False

def wait_and_download_images(page: Page, prompt: str, aspect_ratio: str, output_dir: str = None, expected_images: int = 4, timeout: int = 180) -> bool:
    """
    Wait for generation to complete and download all generated images
    
    Args:
        page: Playwright page
        prompt: The prompt text used for generation (to find the correct div)
        aspect_ratio: Aspect ratio like "16:9" to determine target resolution
        output_dir: Directory to save downloaded images (uses OUTPUT_DIR env if not provided)
        expected_images: Number of images to wait for (default 4)
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if all images downloaded successfully
    """
    import os
    import re
    import urllib.parse
    from pathlib import Path
    
    try:
        # Get output dir from env if not provided
        if output_dir is None:
            output_dir = os.getenv('OUTPUT_DIR', 'outputs')
            
        print(f"\n   ⏳ Waiting for generation to complete...")
        print(f"   🔍 Looking for prompt: {prompt[:60]}...")
        print(f"   📁 Download target: {output_dir}")
        
        # Create output directory if needed
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        item_div = None
        max_main_retries = 3  # Max number of full retries (F5 + resubmit)
        main_retry = 0
        
        while main_retry < max_main_retries:
            print(f"\n   🔄 Main attempt {main_retry + 1}/{max_main_retries}")
            
            # Step 1: Find the correct div containing our prompt text
            retry_count = 0
            max_find_retries = 2  # Try only 2 times (2 * 5s = 10s) to find the div
            found_valid_item = False
            
            while retry_count < max_find_retries and not found_valid_item:
                try:
                    retry_count += 1
                    print(f"   🔍 Search attempt {retry_count}/{max_find_retries}...")
                    
                    # Search for all divs containing the prompt text
                    prompt_elements = page.locator(f'xpath=//span[contains(@class, "prompt-value-container")]')
                    count = prompt_elements.count()
                    
                    print(f"   📊 Found {count} total prompt elements on page")
                    
                    # Look through all elements and find matches with our exact prompt
                    matching_items = []
                    for i in range(count):
                        try:
                            element = prompt_elements.nth(i)
                            text = element.inner_text().strip()
                            
                            # Check if this matches our prompt (exact match or close match)
                            if prompt.strip() == text or prompt[:50] in text or text[:50] in prompt:
                                # Get the parent item div
                                item_candidate = element.locator('xpath=ancestor::div[contains(@class, "item-")]').first
                                
                                # Check status of this item (processing, completed, or failed)
                                processing_text = item_candidate.locator('text="Đang xử lý gợi ý của bạn..."')
                                has_processing = processing_text.count() > 0
                                
                                # Check if it has images (completed)
                                img_elements = item_candidate.locator('img')
                                has_images = img_elements.count() > 0
                                
                                matching_items.append({
                                    'index': i,
                                    'element': item_candidate,
                                    'text': text,
                                    'has_processing': has_processing,
                                    'has_images': has_images
                                })
                                
                                print(f"   📝 Match {len(matching_items)}: index {i}, processing={has_processing}, images={has_images}")
                        except:
                            continue
                    
                    if matching_items:
                        # Get the LAST matching element (newest one)
                        last_item = matching_items[-1]
                        print(f"   ✅ Found {len(matching_items)} matching item(s), checking the last one")
                        
                        # Accept item if it's either processing OR has completed images
                        if last_item['has_processing'] or last_item['has_images']:
                            if last_item['has_processing']:
                                print(f"   ✅ Found item with 'Đang xử lý gợi ý của bạn...' - generation in progress!")
                            elif last_item['has_images']:
                                print(f"   ✅ Found item with completed images - generation done!")
                            item_div = last_item['element']
                            found_valid_item = True
                            break
                        else:
                            print(f"   ⚠️  Last item has no processing text or images, waiting...")
                    else:
                        print(f"   ⚠️  No matching prompt found yet, waiting...")
                    
                    # Wait 5 seconds before next check
                    if not found_valid_item:
                        time.sleep(5)
                        
                except Exception as e:
                    print(f"   ⚠️  Error searching for prompt: {e}")
                    time.sleep(5)
            
            # If we found a valid item, break out of main retry loop
            if found_valid_item:
                break
            
            # If we didn't find valid item after all retries, try F5 refresh
            main_retry += 1
            if main_retry < max_main_retries:
                print(f"   ❌ Could not find valid item after {max_find_retries} attempts")
                print(f"   🔄 Refreshing page (F5) and checking again...")
                
                page.reload(wait_until="domcontentloaded")
                time.sleep(3)
                
                # Wait a bit more and check again
                time.sleep(5)
                
                # Quick check after F5 - look for our prompt with processing text OR completed images
                try:
                    prompt_elements = page.locator(f'xpath=//span[contains(@class, "prompt-value-container")]')
                    count = prompt_elements.count()
                    found_after_refresh = False
                    
                    for i in range(count):
                        try:
                            element = prompt_elements.nth(i)
                            text = element.inner_text().strip()
                            
                            if prompt.strip() == text or prompt[:50] in text:
                                item_candidate = element.locator('xpath=ancestor::div[contains(@class, "item-")]').first
                                processing_text = item_candidate.locator('text="Đang xử lý gợi ý của bạn..."')
                                img_elements = item_candidate.locator('img')
                                
                                # Accept if processing OR has images
                                if processing_text.count() > 0 or img_elements.count() > 0:
                                    status = "processing" if processing_text.count() > 0 else "completed"
                                    print(f"   ✅ Found valid item after F5 refresh! Status: {status}")
                                    item_div = item_candidate
                                    found_valid_item = True
                                    found_after_refresh = True
                                    break
                        except:
                            continue
                    
                    if found_after_refresh:
                        break
                    else:
                        print(f"   ⚠️  Still no valid item after F5, will restart generation...")
                        
                        # Only restart if we truly can't find any trace of our prompt
                        print(f"   🔄 Restarting generation: selecting aspect ratio and submitting prompt...")
                        if not select_aspect_ratio_and_submit(page, aspect_ratio, prompt):
                            print(f"   ❌ Failed to restart generation!")
                            continue  # Try main retry again
                        
                        print(f"   ✅ Restarted generation, will search for item again...")
                        time.sleep(5)  # Wait for new submission to process
                        
                except Exception as e:
                    print(f"   ⚠️  Error during F5 check: {e}")
                    time.sleep(3)
        
        if not found_valid_item or not item_div:
            print(f"   ❌ Could not find valid item after {max_main_retries} main attempts")
            return False
        
        # Step 2: Wait for processing to complete (only if still processing)
        print(f"   ⏳ Checking if generation is still in progress...")
        
        # First check current status
        try:
            processing_text = item_div.locator('text="Đang xử lý gợi ý của bạn..."')
            img_elements = item_div.locator('img')
            
            if processing_text.count() > 0:
                print(f"   ⏳ Generation still in progress, waiting for completion...")
                processing_check_start = time.time()
                
                while time.time() - processing_check_start < timeout:
                    try:
                        # Check if processing text still exists in this div
                        processing_text = item_div.locator('text="Đang xử lý gợi ý của bạn..."')
                        
                        if processing_text.count() == 0:
                            print("   ✅ Processing completed")
                            break
                        else:
                            print(f"   ⏳ Still processing... ({int(time.time() - processing_check_start)}s)")
                            
                        time.sleep(3)
                        
                    except:
                        # If we can't find the text, assume it's done
                        break
                        
            elif img_elements.count() > 0:
                print(f"   ✅ Generation already completed, found {img_elements.count()} images")
            else:
                print(f"   ⚠️  Item found but no processing text or images, will wait briefly...")
                time.sleep(5)
                
        except Exception as e:
            print(f"   ⚠️  Error checking status: {e}")
        
        time.sleep(2)  # Wait a bit more for images to load
        
        # Step 3: Wait for all images to appear
        print(f"   🖼️  Waiting for {expected_images} images to load...")
        images_check_start = time.time()
        
        while time.time() - images_check_start < timeout:
            try:
                # Find all img tags within this item div
                img_elements = item_div.locator('img')
                img_count = img_elements.count()
                
                print(f"   📊 Found {img_count}/{expected_images} images...")
                
                if img_count >= expected_images:
                    print(f"   ✅ All {expected_images} images loaded")
                    break
                    
                time.sleep(3)
                
            except Exception as e:
                print(f"   ⚠️  Error counting images: {e}")
                time.sleep(3)
        
        # Step 4: Click each image to get full resolution URL and download
        print(f"   📥 Downloading images by clicking each one...")
        
        img_elements = item_div.locator('img')
        img_count = img_elements.count()
        
        if img_count < expected_images:
            print(f"   ⚠️  Only found {img_count} images, expected {expected_images}")
        
        downloaded_count = 0
        
        for i in range(min(img_count, expected_images)):
            try:
                print(f"\n   🖼️  Processing image {i+1}/{expected_images}...")
                
                # Get fresh reference to images (in case DOM changed)
                img_elements = item_div.locator('img')
                img = img_elements.nth(i)
                
                # Step 4.1: Hover over thumbnail first, then click to open modal
                print(f"   🖱️  Hovering over thumbnail {i+1}...")
                img.scroll_into_view_if_needed()
                time.sleep(0.5)
                
                # Hover to trigger any hover effects
                img.hover()
                time.sleep(0.5)
                
                # Try multiple click strategies to open modal
                print(f"   🖱️  Left-clicking thumbnail {i+1}...")
                modal_opened = False
                
                # Strategy 1: Click the img directly
                try:
                    img.click(button="left")
                    time.sleep(2)
                    
                    # Check if modal opened
                    modal_img_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[4]/div/div/div[2]/div[1]/div[1]/div/div[1]/div/div/div/div[1]/div/img"
                    modal_check = page.locator(f'xpath={modal_img_xpath}')
                    if modal_check.count() > 0:
                        print(f"   ✅ Modal opened (direct img click)")
                        modal_opened = True
                except Exception as e:
                    print(f"   ⚠️  Direct img click failed: {e}")
                
                # Strategy 2: Click the parent div if img click didn't work
                if not modal_opened:
                    try:
                        print(f"   🔄 Trying parent div click...")
                        parent_div = img.locator('xpath=ancestor::div[1]')
                        parent_div.hover()
                        time.sleep(0.3)
                        parent_div.click(button="left")
                        time.sleep(2)
                        
                        modal_check = page.locator(f'xpath={modal_img_xpath}')
                        if modal_check.count() > 0:
                            print(f"   ✅ Modal opened (parent div click)")
                            modal_opened = True
                    except Exception as e:
                        print(f"   ⚠️  Parent div click failed: {e}")
                
                # Strategy 3: Try clicking with force if still not opened
                if not modal_opened:
                    try:
                        print(f"   🔄 Trying force click...")
                        img.click(button="left", force=True)
                        time.sleep(2)
                        
                        modal_check = page.locator(f'xpath={modal_img_xpath}')
                        if modal_check.count() > 0:
                            print(f"   ✅ Modal opened (force click)")
                            modal_opened = True
                    except Exception as e:
                        print(f"   ⚠️  Force click failed: {e}")
                
                if not modal_opened:
                    print(f"   ❌ Could not open modal for image {i+1}, skipping...")
                    continue
                
                # Step 4.2: Find the full resolution image in modal
                print(f"   🔍 Finding highest resolution image in modal...")
                
                # Look for images with different resolutions in order of preference (highest to lowest)
                # Common resolutions: 1440, 1280, 1080, 960, 720, 600, 512, 360
                modal_img_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[4]/div/div/div[2]/div[1]/div[1]/div/div[1]/div/div/div/div[1]/div/img"
                all_modal_imgs = page.locator(f'xpath={modal_img_xpath}')
                
                # Wait for images to be in DOM
                all_modal_imgs.first.wait_for(state="attached", timeout=10000)
                time.sleep(1)
                
                # Find the highest resolution image available
                full_res_src = None
                highest_resolution = 0
                found_resolution = None
                img_count = all_modal_imgs.count()
                print(f"   📊 Found {img_count} images in modal, searching for highest resolution...")
                
                # List of possible resolutions to check (from highest to lowest priority)
                # Including ultra-high resolutions: 4K, 2K, QHD, FHD, HD, and lower
                possible_resolutions = [
                    "3840:3840", "2880:2880", "2560:2560", "2048:2048",  # 4K and ultra-high
                    "1920:1920", "1800:1800", "1440:1440", "1280:1280",  # 2K and QHD range
                    "1080:1080", "960:960", "720:720", "600:600",        # Standard HD range
                    "512:512", "480:480"                                 # Lower resolutions
                ]
                
                for j in range(img_count):
                    try:
                        img_element = all_modal_imgs.nth(j)
                        src = img_element.get_attribute('src')
                        if src:
                            # Check each resolution from highest to lowest
                            for resolution in possible_resolutions:
                                if resolution in src:
                                    res_value = int(resolution.split(':')[0])
                                    if res_value > highest_resolution:
                                        highest_resolution = res_value
                                        full_res_src = src
                                        found_resolution = resolution
                                        print(f"   ✅ Found {resolution} resolution image at index {j}")
                                    break
                    except:
                        continue
                
                # Fallback: if no specific resolution found, try to find any non-360 image
                if not full_res_src:
                    print(f"   ⚠️  No standard resolution found, checking for any high-quality image...")
                    for j in range(img_count):
                        try:
                            img_element = all_modal_imgs.nth(j)
                            src = img_element.get_attribute('src')
                            if src:
                                # Check if it's NOT the low-res 360:360 version
                                if '360:360' not in src:
                                    full_res_src = src
                                    print(f"   ✅ Found non-360 image at index {j}")
                                    break
                        except:
                            continue
                
                if not full_res_src:
                    print(f"   ⚠️  Modal image {i+1} has no valid src")
                    # Close modal and continue
                    close_modal(page)
                    continue
                
                # Show what resolution we found
                if found_resolution:
                    print(f"   🎯 Using {found_resolution} resolution image")
                else:
                    print(f"   🎯 Using best available resolution")
                
                print(f"   🔗 Image URL {i+1}: {full_res_src[:80]}...")
                
                # Step 4.3: Download the image
                filename = f"prompt_{hash(prompt) & 0xFFFFFFFF}_{i+1}.webp"
                filepath = os.path.join(output_dir, filename)
                
                print(f"   📥 Downloading to {filename}...")
                response = page.context.request.get(full_res_src)
                
                if response.ok:
                    with open(filepath, 'wb') as f:
                        f.write(response.body())
                    print(f"   ✅ Downloaded image {i+1}: {filename}")
                    downloaded_count += 1
                else:
                    print(f"   ❌ Failed to download image {i+1}: HTTP {response.status}")
                
                # Step 4.4: Close modal by clicking X button
                print(f"   ❌ Closing modal...")
                close_modal(page)
                time.sleep(1)  # Wait for modal to close
                
            except Exception as e:
                print(f"   ❌ Error processing image {i+1}: {e}")
                import traceback
                traceback.print_exc()
                # Try to close modal if still open
                try:
                    close_modal(page)
                except:
                    pass
        
        print(f"\n   ✅ Downloaded {downloaded_count}/{expected_images} images")
        return downloaded_count >= expected_images
        
    except Exception as e:
        print(f"   ❌ Error in wait_and_download_images: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_to_high_res(url: str, aspect_ratio: str) -> str:
    """
    Convert low-res image URL to high-res by changing the resize parameter
    
    Args:
        url: Original URL like ...aigc_resize:360:360.webp...
        aspect_ratio: Aspect ratio like "16:9", "1:1", etc.
    
    Returns:
        Modified URL with high-res dimensions
    """
    import re
    from config import get_aspect_ratio_dimensions
    
    # Get target dimensions based on aspect ratio
    width, height = get_aspect_ratio_dimensions(aspect_ratio)
    
    # Try to get the highest resolution available, with fallback chain
    if width is None or height is None:
        # Try different resolutions from highest to lowest
        preferred_resolutions = ["3840:3840", "2560:2560", "1920:1920", "1440:1440", "1080:1080", "720:720"]
        target_res = preferred_resolutions[0]  # Default to highest (4K)
    else:
        # Calculate dimensions for different base resolutions
        # Try ultra-high resolutions first: 2560 (2K), 1920 (FHD), 1440 (QHD), 1080, 720
        base_resolutions = [2560, 1920, 1440, 1080, 720]
        
        for base in base_resolutions:
            if width >= height:
                # Landscape or square
                target_width = base
                target_height = int(base * height / width)
            else:
                # Portrait
                target_height = base
                target_width = int(base * width / height)
            
            target_res = f"{target_width}:{target_height}"
            break  # Use the first (highest) resolution
    
    # Replace the resize parameter
    # Pattern: aigc_resize:360:360 or similar
    pattern = r'aigc_resize:\d+:\d+'
    replacement = f'aigc_resize:{target_res}'
    
    new_url = re.sub(pattern, replacement, url)
    
    return new_url

def close_modal(page: Page) -> bool:
    """
    Close the image detail modal by clicking the X button
    Also handles additional popups that might appear
    
    Args:
        page: Playwright page
    
    Returns:
        True if modal closed successfully
    """
    try:
        # First, try to close the main image modal
        close_button_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[4]/div/div/div[2]/div[1]/div[2]/button[1]"
        close_button = page.locator(f'xpath={close_button_xpath}')
        
        close_button.wait_for(state="visible", timeout=5000)
        time.sleep(0.5)
        close_button.click()
        time.sleep(0.5)
        
        print("   ✅ Closed main modal")
        
    except Exception as e:
        print(f"   ⚠️  Failed to close main modal: {e}")
    
    # Check for and close additional popup at /html/body/div[5]/div[2]
    try:
        additional_popup_xpath = "/html/body/div[5]/div[2]"
        additional_popup = page.locator(f'xpath={additional_popup_xpath}')
        
        # Wait briefly to see if popup exists
        additional_popup.wait_for(state="visible", timeout=2000)
        
        if additional_popup.count() > 0:
            print("   📱 Found additional popup at div[5], closing...")
            
            # Try to find and click exit/close button within the popup
            exit_button_selectors = [
                f'xpath={additional_popup_xpath}//button[contains(@class, "close-button")]',  # Button with close-button class
                f'xpath={additional_popup_xpath}//div[contains(@class, "close-button")]',    # Div with close-button class
                f'xpath={additional_popup_xpath}//span[contains(@class, "close-button")]',   # Span with close-button class
                f'xpath={additional_popup_xpath}//button[contains(@class, "close")]',
                f'xpath={additional_popup_xpath}//button[contains(@class, "exit")]',
                f'xpath={additional_popup_xpath}//button[contains(text(), "✕")]',
                f'xpath={additional_popup_xpath}//button[contains(text(), "×")]',
                f'xpath={additional_popup_xpath}//button[contains(text(), "Close")]',
                f'xpath={additional_popup_xpath}//button[contains(text(), "Exit")]',
                f'xpath={additional_popup_xpath}//span[contains(@class, "close")]',
                f'xpath={additional_popup_xpath}//div[contains(@class, "close")]',
            ]
            
            popup_closed = False
            
            for selector in exit_button_selectors:
                try:
                    exit_button = page.locator(selector)
                    if exit_button.count() > 0:
                        element_type = "close-button class" if "close-button" in selector else "fallback"
                        print(f"   🖱️  Clicking {element_type} exit button in popup...")
                        exit_button.first.click()
                        popup_closed = True
                        print(f"   ✅ Closed popup with {element_type} button")
                        time.sleep(0.5)
                        break
                except Exception as e:
                    continue
            
            # If no exit button found, try pressing Escape
            if not popup_closed:
                print("   ⌨️  No exit button found, pressing Escape...")
                page.keyboard.press("Escape")
                popup_closed = True
                print("   ✅ Closed popup with Escape key")
                time.sleep(0.5)
            
    except Exception as e:
        # Popup doesn't exist or already closed
        pass

    # Check for and close popup at /html/body/div[6]/div[2]/div
    try:
        popup_div6_xpath = "/html/body/div[6]/div[2]/div"
        popup_div6 = page.locator(f'xpath={popup_div6_xpath}')
        
        # Wait briefly to see if popup exists
        popup_div6.wait_for(state="visible", timeout=2000)
        
        if popup_div6.count() > 0:
            print("   📱 Found popup at div[6], closing...")
            
            # First try to click the specific close button
            close_button_xpath = "/html/body/div[6]/div[2]/div/div[2]/div[2]/div/div"
            close_button = page.locator(f'xpath={close_button_xpath}')
            
            popup_closed = False
            
            try:
                close_button.wait_for(state="visible", timeout=3000)
                if close_button.count() > 0:
                    print(f"   🖱️  Clicking close button in div[6] popup...")
                    close_button.first.click()
                    popup_closed = True
                    print("   ✅ Closed div[6] popup with specific close button")
                    time.sleep(0.5)
            except Exception as e:
                print(f"   ⚠️  Specific close button failed: {e}")
            
            # If specific button doesn't work, try other selectors
            if not popup_closed:
                exit_button_selectors = [
                    f'xpath={popup_div6_xpath}//button[contains(@class, "close-button")]',  # Button with close-button class
                    f'xpath={popup_div6_xpath}//div[contains(@class, "close-button")]',    # Div with close-button class
                    f'xpath={popup_div6_xpath}//span[contains(@class, "close-button")]',   # Span with close-button class
                    f'xpath={popup_div6_xpath}//button[contains(@class, "close")]',
                    f'xpath={popup_div6_xpath}//button[contains(@class, "exit")]',
                    f'xpath={popup_div6_xpath}//button[contains(text(), "✕")]',
                    f'xpath={popup_div6_xpath}//button[contains(text(), "×")]',
                    f'xpath={popup_div6_xpath}//button[contains(text(), "Close")]',
                    f'xpath={popup_div6_xpath}//button[contains(text(), "Exit")]',
                    f'xpath={popup_div6_xpath}//span[contains(@class, "close")]',
                    f'xpath={popup_div6_xpath}//div[contains(@class, "close")]',
                ]
                
                for selector in exit_button_selectors:
                    try:
                        exit_button = page.locator(selector)
                        if exit_button.count() > 0:
                            element_type = "close-button class" if "close-button" in selector else "fallback"
                            print(f"   🖱️  Clicking {element_type} exit button in div[6] popup...")
                            exit_button.first.click()
                            popup_closed = True
                            print(f"   ✅ Closed div[6] popup with {element_type} button")
                            time.sleep(0.5)
                            break
                    except Exception as e:
                        continue
            
            # Final fallback for div[6] popup - try pressing Escape
            if not popup_closed:
                print("   ⌨️  No exit button found for div[6], pressing Escape...")
                page.keyboard.press("Escape")
                popup_closed = True
                print("   ✅ Closed div[6] popup with Escape key")
                time.sleep(0.5)
            
    except Exception as e:
        # Popup doesn't exist or already closed
        pass
    
    # Final fallback - press Escape to close any remaining modals
    try:
        print("   ⌨️  Final Escape key press to ensure all modals are closed...")
        page.keyboard.press("Escape")
        time.sleep(0.5)
        print("   ✅ Final modal cleanup completed")
        return True
    except Exception as e:
        print(f"   ⚠️  Final modal cleanup failed: {e}")
        return False

def detect_available_resolutions(page: Page) -> list:
    """
    Detect what resolutions are available on the current page
    Returns list of available resolutions in format ["1440:1440", "720:720", etc.]
    """
    try:
        # Find all images on page and extract resolution patterns
        all_imgs = page.locator('img')
        count = all_imgs.count()
        
        resolutions = set()
        resolution_pattern = r'(\d+):(\d+)'
        
        for i in range(min(count, 20)):  # Check first 20 images max
            try:
                img = all_imgs.nth(i)
                src = img.get_attribute('src')
                if src:
                    import re
                    matches = re.findall(resolution_pattern, src)
                    for match in matches:
                        width, height = match
                        if int(width) >= 360 and int(height) >= 360:  # Only valid resolutions
                            # Also check for ultra-high resolutions
                            if int(width) <= 4096 and int(height) <= 4096:  # Up to 4K max
                                resolutions.add(f"{width}:{height}")
            except:
                continue
        
        # Sort by resolution (highest first)
        sorted_resolutions = sorted(list(resolutions), 
                                  key=lambda x: int(x.split(':')[0]), 
                                  reverse=True)
        
        return sorted_resolutions
    
    except Exception as e:
        print(f"   ⚠️  Could not detect resolutions: {e}")
        return ["720:720", "360:360"]  # Default fallback
