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
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"\n   🔄 Retry attempt {attempt + 1}/{max_retries}...")
                print("   🔄 Refreshing page...")
                page.reload(wait_until="domcontentloaded")
                time.sleep(3)  # Wait for page to fully load
            
            print(f"   📐 Processing aspect ratio: {desired_ratio}...")
            
            # Wait before interacting - slower for stability
            time.sleep(2)
            
            # Step 1: Click the first button to open aspect ratio selector
            print("   🖱️  Opening aspect ratio selector...")
            open_button_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div[2]/div[1]/button"
            open_button = page.locator(f'xpath={open_button_xpath}')
            open_button.wait_for(state="visible", timeout=15000)
            time.sleep(1)  # Wait before clicking
            open_button.click()
            print("   ✅ Opened aspect ratio selector")
            time.sleep(2)  # Wait for dropdown to fully appear
            
            # Step 2: Wait for aspect ratio container to appear
            container_xpath = "/html/body/div[4]/span/div"
            container = page.locator(f'xpath={container_xpath}')
            container.wait_for(state="visible", timeout=15000)
            print("   ✅ Aspect ratio selector appeared")
            
            # Wait for animation to complete - longer delay
            time.sleep(1.5)
            
            # Step 3: Find and click the label with the desired ratio text
            print(f"   🎯 Selecting ratio: {desired_ratio}...")
            label_selectors = [
                f'xpath=//label[contains(@class, "lv-radio")]//span[text()="{desired_ratio}"]',
                f'xpath=//label[contains(@class, "lv-radio")]//input[@value="{desired_ratio}"]/..',
                f'xpath=//input[@type="radio" and @value="{desired_ratio}"]',
            ]
            
            clicked = False
            for selector in label_selectors:
                try:
                    element = page.locator(selector)
                    if element.count() > 0:
                        time.sleep(0.5)  # Wait before clicking
                        
                        # Get the label parent if we found the span/input
                        if 'span[text()' in selector or 'input[@value' in selector:
                            # Click the parent label
                            if 'span[text()' in selector:
                                label = element.locator('xpath=ancestor::label')
                            else:
                                label = element.locator('xpath=..')
                            label.click()
                        else:
                            element.click()
                        
                        print(f"   ✅ Selected aspect ratio: {desired_ratio}")
                        clicked = True
                        time.sleep(2)  # Wait after clicking - longer delay
                        break
                except Exception as e:
                    print(f"   ⚠️  Selector {selector[:50]}... failed: {e}")
                    continue
            
            # Critical check - MUST select aspect ratio to continue
            if not clicked:
                print(f"   ❌ Could not select aspect ratio! Will retry...")
                if attempt < max_retries - 1:
                    continue  # Retry from beginning
                else:
                    print(f"   ❌ Failed after {max_retries} attempts!")
                    return False
            
            # Step 4: Input prompt into textarea
            print(f"   ✍️  Entering prompt: {prompt[:60]}...")
            textarea_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div[1]/div[2]/div/textarea"
            textarea = page.locator(f'xpath={textarea_xpath}')
            textarea.wait_for(state="visible", timeout=15000)
            time.sleep(1)  # Wait before interacting
            textarea.click()
            time.sleep(1)  # Wait after click
            textarea.fill(prompt)
            print("   ✅ Entered prompt")
            time.sleep(2)  # Wait after entering text
            
            # Step 5: Click the submit button
            print("   🚀 Clicking submit button...")
            submit_button_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div[2]/div[2]/div[2]/button"
            submit_button = page.locator(f'xpath={submit_button_xpath}')
            submit_button.wait_for(state="visible", timeout=15000)
            time.sleep(1)  # Wait before checking
            
            # Check if button is enabled
            is_disabled = submit_button.get_attribute("disabled")
            if is_disabled:
                print("   ⚠️  Submit button is disabled, waiting...")
                time.sleep(3)
                is_disabled = submit_button.get_attribute("disabled")
                if is_disabled:
                    print("   ❌ Submit button still disabled, will retry...")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return False
            
            # Click submit
            submit_button.scroll_into_view_if_needed()
            time.sleep(1)
            
            try:
                submit_button.click()
            except Exception as e:
                print(f"   ⚠️  First click failed, trying force click: {e}")
                submit_button.click(force=True)
            
            print("   ✅ Clicked submit button")
            time.sleep(2)
            
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

def generate_image_via_ui(page: Page, prompt: str, aspect_ratio: str = None, output_dir: str = "outputs") -> bool:
    """
    Complete flow to generate image via UI and download results
    
    Args:
        page: Playwright page (must be on generation page)
        prompt: Text prompt
        aspect_ratio: Aspect ratio like "16:9" (optional, uses env if not provided)
        output_dir: Directory to save downloaded images
    
    Returns:
        True if generation and download succeeded
    """
    try:
        # Get aspect ratio from env if not provided
        if aspect_ratio is None:
            aspect_ratio = os.getenv('ASPECT_RATIO', '16:9')
        
        print(f"\n🎨 Generating via UI...")
        print(f"   📝 Prompt: {prompt[:80]}...")
        print(f"   📐 Aspect Ratio: {aspect_ratio}")
        
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

def wait_and_download_images(page: Page, prompt: str, aspect_ratio: str, output_dir: str = "outputs", expected_images: int = 4, timeout: int = 180) -> bool:
    """
    Wait for generation to complete and download all generated images
    
    Args:
        page: Playwright page
        prompt: The prompt text used for generation (to find the correct div)
        aspect_ratio: Aspect ratio like "16:9" to determine target resolution
        output_dir: Directory to save downloaded images
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
        print(f"\n   ⏳ Waiting for generation to complete...")
        print(f"   🔍 Looking for prompt: {prompt[:60]}...")
        
        # Create output directory if needed
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        item_div = None
        
        # Step 1: Find the LAST (newest) div containing our prompt text
        # Retry with delays because div takes time to appear after submit
        print("   🔄 Waiting for new item div to appear (with retries)...")
        
        retry_count = 0
        max_find_retries = 20  # Try for up to 40 seconds to find the div
        
        while time.time() - start_time < timeout and retry_count < max_find_retries:
            try:
                retry_count += 1
                print(f"   🔍 Search attempt {retry_count}/{max_find_retries}...")
                
                # Search for all divs containing the prompt text
                prompt_elements = page.locator(f'xpath=//span[contains(@class, "prompt-value-container")]')
                count = prompt_elements.count()
                
                print(f"   📊 Found {count} total prompt elements on page")
                
                # Look through all elements and find matches
                matching_indices = []
                for i in range(count):
                    try:
                        element = prompt_elements.nth(i)
                        text = element.inner_text()
                        
                        # Check if this is our prompt (compare first 50 chars or full text)
                        if prompt[:50] in text or text[:50] in prompt:
                            matching_indices.append(i)
                    except:
                        continue
                
                if matching_indices:
                    # Get the LAST matching element (newest one, from top to bottom)
                    last_index = matching_indices[-1]
                    print(f"   ✅ Found {len(matching_indices)} matching prompt(s), using the last one (index {last_index})")
                    
                    last_element = prompt_elements.nth(last_index)
                    # Get the parent item div
                    item_div = last_element.locator('xpath=ancestor::div[contains(@class, "item-")]').first
                    print(f"   ✅ Found item div for our newest prompt")
                    break
                else:
                    print(f"   ⚠️  No matching prompt found yet, waiting...")
                    time.sleep(2)
                
            except Exception as e:
                print(f"   ⚠️  Error searching for prompt: {e}")
                time.sleep(2)
        
        if not item_div:
            print("   ❌ Could not find item div with our prompt after all retries")
            return False
        
        # Step 2: Wait for processing to complete
        print("   ⏳ Waiting for 'Đang xử lý gợi ý của bạn...' to disappear...")
        processing_check_start = time.time()
        
        while time.time() - processing_check_start < timeout:
            try:
                # Check if processing text still exists in this div
                processing_text = item_div.locator('text="Đang xử lý gợi ý của bạn..."')
                
                if processing_text.count() == 0:
                    print("   ✅ Processing completed")
                    break
                    
                time.sleep(3)
                
            except:
                # If we can't find the text, assume it's done
                break
        
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
                print(f"   🔍 Finding full resolution image in modal...")
                
                # There are 2 images in modal: 720:720 (full-res) and 360:360 (low-res)
                # Find all img elements and filter by URL containing "720:720"
                modal_img_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[4]/div/div/div[2]/div[1]/div[1]/div/div[1]/div/div/div/div[1]/div/img"
                all_modal_imgs = page.locator(f'xpath={modal_img_xpath}')
                
                # Wait for images to be in DOM
                all_modal_imgs.first.wait_for(state="attached", timeout=10000)
                time.sleep(1)
                
                # Find the image with 720:720 in its src
                full_res_src = None
                img_count = all_modal_imgs.count()
                print(f"   📊 Found {img_count} images in modal, looking for 720:720...")
                
                for j in range(img_count):
                    try:
                        img_element = all_modal_imgs.nth(j)
                        src = img_element.get_attribute('src')
                        if src and '720:720' in src:
                            full_res_src = src
                            print(f"   ✅ Found 720:720 image at index {j}")
                            break
                    except:
                        continue
                
                # Fallback: if no 720:720 found, try to find the larger resolution
                if not full_res_src:
                    print(f"   ⚠️  No 720:720 found, checking for any high-res image...")
                    for j in range(img_count):
                        try:
                            img_element = all_modal_imgs.nth(j)
                            src = img_element.get_attribute('src')
                            if src:
                                # Check if it's NOT the 360:360 version
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
                
                print(f"   🔗 Full-res URL {i+1}: {full_res_src[:80]}...")
                
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
    
    # Default to 720x720 if we can't determine
    if width is None or height is None:
        target_res = "720:720"
    else:
        # Use 720 as base and calculate other dimension
        if width >= height:
            # Landscape or square
            base = 720
            target_width = base
            target_height = int(base * height / width)
        else:
            # Portrait
            base = 720
            target_height = base
            target_width = int(base * width / height)
        
        target_res = f"{target_width}:{target_height}"
    
    # Replace the resize parameter
    # Pattern: aigc_resize:360:360 or similar
    pattern = r'aigc_resize:\d+:\d+'
    replacement = f'aigc_resize:{target_res}'
    
    new_url = re.sub(pattern, replacement, url)
    
    return new_url

def close_modal(page: Page) -> bool:
    """
    Close the image detail modal by clicking the X button
    
    Args:
        page: Playwright page
    
    Returns:
        True if modal closed successfully
    """
    try:
        close_button_xpath = "/html/body/div[1]/div[1]/div/div/div[2]/div[4]/div/div/div[2]/div[1]/div[2]/button[1]"
        close_button = page.locator(f'xpath={close_button_xpath}')
        
        close_button.wait_for(state="visible", timeout=5000)
        time.sleep(0.5)
        close_button.click()
        time.sleep(0.5)
        
        print("   ✅ Closed modal")
        return True
        
    except Exception as e:
        print(f"   ⚠️  Failed to close modal: {e}")
        # Try pressing Escape as fallback
        try:
            page.keyboard.press("Escape")
            time.sleep(0.5)
            print("   ✅ Closed modal with Escape key")
            return True
        except:
            return False
