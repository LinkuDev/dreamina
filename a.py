#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Dreamina Multi-Account 2-Phase Generator
# ---------------------------------------------------------------------------
# • Generates images through CapCut Dreamina via REST
# • Then scrapes the hi-res previews through Playwright
# • Browser now runs headlessly; all logs stay visible in console
# ---------------------------------------------------------------------------

import os
import requests
import uuid
import json
import time
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from playwright.sync_api import (
    sync_playwright, Page, expect, Browser,
    TimeoutError as PlaywrightTimeoutError,
)
import csv
import random

# Import debug configuration
try:
    from debug_config import *
    print("✅ Debug configuration loaded")
except ImportError:
    print("⚠️  Debug config not found, using default settings")
    DEBUG_MODE = False
    SHOW_BROWSER = False
    SLOW_MODE = False
    SCREENSHOT_ON_ERROR = False
    VERBOSE_LOGGING = False
    BROWSER_ARGS = []
    CLICK_DELAY = 100
    NAVIGATION_DELAY = 1000
    ACTION_DELAY = 100

# --- Configuration ---------------------------------------------------------
API_BASE_URL           = "http://localhost:8000/v1"
DREAMINA_ROOT_URL      = "https://dreamina.capcut.com"
DREAMINA_HOME_URL      = "https://dreamina.capcut.com/ai-tool/home"
DREAMINA_CREATIONS_URL = "https://dreamina.capcut.com/ai-tool/asset"
MODEL_NAME             = "jimeng-3.0"
WATERMARK_DIR          = "generated_watermarked"
PREVIEW_DIR            = "generated_no_watermark"
CREDITS_PER_GENERATION = 5
COOKIE_FOLDER          = "cookies"          # Folder containing account files

# --- Advanced Configuration -------------------------------------------------
DEFAULT_NUM_IMAGES      = 4
DEFAULT_SAMPLE_STRENGTH = 0.5
MAX_CONCURRENT_JOBS     = 3
HEADLESS_MODE           = False             # ← show browser window for debugging
PROMPT_CHUNK_SIZE       = 6
GALLERY_UPDATE_DELAY    = 10                # Seconds

ASPECT_RATIOS = {
    "21:9 (Landscape)" : (2016,  864),
    "16:9 (Widescreen)": (1664,  936),
    "3:2 (Landscape)"   : (1584, 1056),
    "4:3 (Standard)"    : (1472, 1104),
    "8:7 (Tui tote Landscape)"   : (1344, 1176),
    "1:1 (Square)"      : (1328, 1328),
    "7:8 (Tui tote Portrait)"    : (1176, 1344),
    "3:4 (Portrait)"    : (1104, 1472),
    "2:3 (Portrait)"    : (1056, 1584),
    "9:16 (Tall)"       : ( 936, 1664),
}

# ---------------------------------------------------------------------------
# (Functions below are updated for new features)
# ---------------------------------------------------------------------------

def safe_navigate(page: Page, target_url: str, max_attempts: int = 5):
    """Robust navigation with retries and gateway-timeout detection."""
    for attempt in range(max_attempts):
        try:
            if VERBOSE_LOGGING:
                print(f"--- Navigation Attempt {attempt + 1}/{max_attempts} → {target_url}")
            if attempt:
                if VERBOSE_LOGGING:
                    print("    • Retry: first hop to root, then back to target")
                page.goto(DREAMINA_ROOT_URL, wait_until="networkidle", timeout=60_000)
                if SLOW_MODE:
                    time.sleep(NAVIGATION_DELAY / 1000)
                else:
                    time.sleep(5)

            page.goto(target_url, wait_until="networkidle", timeout=45_000)
            
            if SLOW_MODE:
                time.sleep(NAVIGATION_DELAY / 1000)

            if "gateway timeout" in page.content().lower():
                raise PlaywrightTimeoutError("'Gateway timeout' in HTML")

            if VERBOSE_LOGGING:
                print("    • Page loaded successfully")
            return
        except PlaywrightTimeoutError as e:
            if VERBOSE_LOGGING:
                print(f"    ⚠️  Attempt {attempt + 1} failed: {e}")
            if SCREENSHOT_ON_ERROR:
                screenshot_path = f"error_navigation_{attempt}_{int(time.time())}.png"
                try:
                    page.screenshot(path=screenshot_path)
                    print(f"    📸 Screenshot saved: {screenshot_path}")
                except:
                    pass
            if attempt == max_attempts - 1:
                print("    ❌ All navigation attempts exhausted.")
                raise
            if VERBOSE_LOGGING:
                print("    …retrying")

def create_retry_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(total=3,
                           status_forcelist=[429, 500, 502, 503, 504],
                           backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def clean_cookies(cookies: list[dict]) -> list[dict]:
    """Ensure each cookie has a valid sameSite value so Playwright likes them."""
    valid = {"Strict", "Lax", "None"}
    for ck in cookies:
        if ck.get("sameSite") not in valid:
            ck["sameSite"] = "Lax"
    return cookies

def sanitize_filename(text: str) -> str:
    s = re.sub(r"[^\w\s\._-]", "", text).strip()
    s = re.sub(r"\s+", "_", s)
    return s[:80] or "unnamed_creation"

# ---------------- Account helpers ------------------------------------------

def load_accounts(folder: str) -> list[dict]:
    print(f"🔑 Loading account cookies from “{folder}”…")
    accounts = []
    folder_path = Path(folder)
    if not folder_path.is_dir():
        print(f"❌ Folder not found: {folder}")
        return []

    for fp in sorted(folder_path.glob("*.json")):
        try:
            with fp.open(encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) < 2:
                print(f"  ⚠️  {fp.name}: not enough lines, skipping")
                continue
            session_id = lines[0].strip()
            cookies = json.loads("".join(lines[1:]))
            accounts.append({
                "name": fp.stem,
                "session_id": session_id,
                "cookies": cookies,
                "filepath": fp,
            })
            print(f"  • Loaded {fp.name}")
        except (json.JSONDecodeError, IndexError) as exc:
            print(f"  ⚠️  {fp.name}: bad format ({exc})")

    if not accounts:
        print("❌ No usable accounts found.")
    else:
        print(f"✅ {len(accounts)} account(s) ready\n")
    return accounts

def get_single_account_credits(account: dict, browser: Browser) -> int | None:
    print(f"🔎 Checking credits for {account['name']}…")
    context = None
    try:
        context = browser.new_context()
        context.add_cookies(clean_cookies(account["cookies"]))
        page = context.new_page()
        safe_navigate(page, DREAMINA_HOME_URL)

        # ### THIS IS THE ONLY MODIFIED LINE ###
        # Updated the CSS selector to match the new website structure.
        credit_span = page.locator("div.credit-amount-text-tuyBBF")
        expect(credit_span).to_be_visible(timeout=20_000)

        credits = int(credit_span.inner_text())
        print(f"  • Credits: {credits}")
        return credits
    except Exception as exc:
        print(f"  ❌ Couldn’t fetch credits: {exc}")
        return None
    finally:
        if context:
            context.close()

# ------------- Generation via REST API -------------------------------------

def generate_with_api(prompt_details: dict,
                      output_dir: Path,
                      session_id: str,
                      save_watermarked: bool,
                      prompt_no: int,
                      csv_name: str,
                      ratio_string: str) -> int:
    """Call /images/generations and optionally download the watermarked JPGs."""
    prompt = prompt_details["prompt"]
    try:
        endpoint = f"{API_BASE_URL}/images/generations"
        headers = {"Authorization": f"Bearer {session_id}",
                   "Content-Type": "application/json"}
        payload = {"model": MODEL_NAME,
                   **{k: v for k, v in prompt_details.items() if k != "prompt"},
                   "prompt": prompt}
        session = create_retry_session()
        resp = session.post(endpoint,
                            headers=headers,
                            data=json.dumps(payload),
                            timeout=300)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("data"):
            print(f"  ⚠️  No images for: {prompt[:60]}…")
            return 0

        urls = [d["url"] for d in data["data"]]
        if save_watermarked:
            output_dir.mkdir(parents=True, exist_ok=True)
            for i, url in enumerate(urls):
                try:
                    letter = chr(ord("A") + i)
                    base = f"{prompt_no}{letter}_{sanitize_filename(csv_name)}_{ratio_string}"
                    fp = output_dir / f"{base}.jpeg"

                    img = session.get(url, stream=True, timeout=60)
                    img.raise_for_status()
                    
                    with fp.open("wb") as f_out:
                        for chunk in img.iter_content(8192):
                            f_out.write(chunk)
                except Exception as exc:
                    print(f"    ⚠️  Couldn’t download {url}: {exc}")
        return len(urls)
    except Exception as exc:
        print(f"  ❌ API error for “{prompt[:60]}…”: {exc}")
        return 0

# ---------------- PHASE 1: submit jobs -------------------------------------

def run_generation_phase_for_account(prompt_jobs: list[dict],
                                     account: dict,
                                     shared_settings: dict,
                                     base_filename_info: dict,
                                     watermark_dir: Path,
                                     save_watermarked: bool) -> int:
    """
    Args:
        prompt_jobs (list[dict]): List of dicts, each with 'prompt' and 'prompt_no'.
        base_filename_info (dict): Dict with 'csv_name' and 'ratio_string'.
    """
    print(f"\n— PHASE 1 — {account['name']} generating {len(prompt_jobs)} prompt(s)")
    if save_watermarked:
        watermark_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    with ThreadPoolExecutor(MAX_CONCURRENT_JOBS) as pool:
        fut_to_prompt = {}
        for i, job in enumerate(prompt_jobs, 1):
            print(f"  • Queue job {i}/{len(prompt_jobs)}")
            prompt_details = {"prompt": job['prompt'], **shared_settings}
            fut = pool.submit(generate_with_api,
                              prompt_details,
                              watermark_dir,
                              account["session_id"],
                              save_watermarked,
                              job['prompt_no'],
                              base_filename_info['csv_name'],
                              base_filename_info['ratio_string'])
            fut_to_prompt[fut] = job['prompt']
            if i < len(prompt_jobs):
                delay = random.uniform(4, 8)
                time.sleep(delay)

        for done_i, fut in enumerate(as_completed(fut_to_prompt), 1):
            try:
                n = fut.result()
                total += n
                print(f"    ✓ Job finished ({done_i}/{len(prompt_jobs)})")
            except Exception as exc:
                print(f"    ❌ Job crashed: {exc}")

    print(f"— PHASE 1 complete for {account['name']} — generated {total} image(s)")
    return total

# ---------------- PHASE 2: scrape previews ---------------------------------

def run_scraping_phase(num_images: int,
                       account: dict,
                       prompt_chunk: list[str],
                       shared_settings: dict,
                       global_prompt_counter: int,
                       preview_dir: Path,
                       browser: Browser,
                       csv_name: str,
                       ratio_string: str):
    print(f"\n— PHASE 2 — download {num_images} preview(s) to {preview_dir}")
    if num_images == 0:
        print("  (Nothing to download)")
        return

    preview_dir.mkdir(parents=True, exist_ok=True)
    context = None
    try:
        context = browser.new_context()
        context.add_cookies(clean_cookies(account["cookies"]))
        page = context.new_page()

        safe_navigate(page, DREAMINA_HOME_URL)

        print("  • Checking for and closing any initial pop-up modals...")
        try:
            modal_locator = page.locator('div[class*="lv-modal-wrapper"]')
            modal_locator.wait_for(state="visible", timeout=5000)
            print("    - Modal detected. Pressing 'Escape' to close.")
            page.keyboard.press("Escape")
            expect(modal_locator).to_be_hidden(timeout=5000)
            print("    - Modal closed successfully.")
            time.sleep(1)
        except PlaywrightTimeoutError:
            print("    - No modal detected, proceeding as normal.")

        expect(page.locator("#Asset")).to_be_visible(timeout=30_000)
        page.locator("#Asset").click()
        page.wait_for_url(f"**/{DREAMINA_CREATIONS_URL.split('/')[-1]}",
                          timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=30_000)

        card_sel = '[class*="history-image-card"]'
        expect(page.locator(card_sel).first).to_be_visible(timeout=30_000)

        n_per_prompt = shared_settings.get("n", DEFAULT_NUM_IMAGES)
        n_prompts = len(prompt_chunk)
        max_to_scrape = min(num_images, n_per_prompt * n_prompts)

        for i in range(max_to_scrape):
            try:
                print(f"\n  ⮞ Image {i + 1}/{max_to_scrape}")
                cards = page.locator(card_sel)
                if cards.count() <= i:
                    print("    • No more thumbnails, aborting loop")
                    break

                cards.nth(i).click()

                med_sel = 'img[data-apm-action="ai-generated-image-detail-card"]'
                med_img = page.locator(med_sel)
                expect(med_img).to_be_visible(timeout=20_000)
                med_img.click()

                zoom_dialog_locator = page.locator('div[role="dialog"]').last
                final_img = zoom_dialog_locator.locator("img")
                expect(final_img).to_be_visible(timeout=20_000)
                expect(final_img).to_have_attribute(
                    "src", re.compile(r"^https?"), timeout=8_000
                )
                image_url = final_img.get_attribute("src")

                if not image_url:
                    raise ValueError("No src attribute found")

                resp = page.request.get(image_url)
                img_bytes = resp.body()

                prompt_idx = (n_prompts - 1) - (i // n_per_prompt)
                sub_idx = i % n_per_prompt
                if not (0 <= prompt_idx < n_prompts):
                    base = f"error_index_{i}_preview_{account['name']}_{uuid.uuid4().hex[:4]}"
                else:
                    prompt_no  = global_prompt_counter + prompt_idx
                    letter     = chr(ord("A") + (n_per_prompt - 1 - sub_idx))
                    base = f"{prompt_no}{letter}_{sanitize_filename(csv_name)}_{ratio_string}"

                fp = preview_dir / f"{base}.webp"
                fp.write_bytes(img_bytes)
                print(f"    ✓ Saved {fp.name}")

            except Exception as exc:
                print(f"    ❌ Couldn’t download image {i + 1}: {exc}")
            finally:
                while page.locator('div[role="dialog"]').count():
                    page.keyboard.press("Escape")
                    time.sleep(1)

    except Exception as exc:
        print(f"❌ PHASE 2 error: {exc}")
    finally:
        if context:
            context.close()

# ---------------- Helper: user I/O -----------------------------------------

def select_from_menu(prompt_text: str, options: list, default_index: int = 0) -> int:
    while True:
        print(prompt_text)
        for i, opt in enumerate(options, 1):
            print(f"  {i}: {opt}")
        choice = input(f"Enter 1-{len(options)} "
                       f"(default {default_index + 1}): ").strip()
        if not choice:
            return default_index
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice) - 1
        print("❌ Invalid selection.")

def get_generation_settings_from_user() -> dict:
    cfg = {}
    keys = list(ASPECT_RATIOS.keys())
    idx  = select_from_menu("\n📏 Aspect ratio:", keys, 1)
    cfg["width"], cfg["height"] = ASPECT_RATIOS[keys[idx]]
    print(f"  → {keys[idx]} ({cfg['width']}×{cfg['height']})")

    while True:
        n = input(f"🔢 Images per prompt (1-4, default {DEFAULT_NUM_IMAGES}): ").strip()
        cfg["n"] = int(n) if n else DEFAULT_NUM_IMAGES
        if 1 <= cfg["n"] <= 4:
            break
        print("❌ Enter 1–4.")

    cfg["negative_prompt"] = input("🚫 Negative prompt (optional): ").strip()

    while True:
        ss = input(f"🎨 Sample strength 0.0-1.0 (default {DEFAULT_SAMPLE_STRENGTH}): ").strip()
        cfg["sample_strength"] = float(ss) if ss else DEFAULT_SAMPLE_STRENGTH
        if 0.0 <= cfg["sample_strength"] <= 1.0:
            break
        print("❌ Enter 0.0–1.0.")
    return cfg

def get_save_mode_from_user() -> int:
    """Asks user to select a save mode and returns an integer (1, 2, or 3)."""
    prompt = "\n💾 Select save mode:"
    options = [
        "Save ONLY watermarked images (Default)",
        "Save ONLY non-watermarked previews",
        "Save BOTH watermarked and non-watermarked"
    ]
    # select_from_menu returns a 0-based index, so we add 1.
    # The new default is option 1, which has index 0.
    return select_from_menu(prompt, options, default_index=0) + 1

def load_prompts_from_file(path: str) -> list[str]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    ext = p.suffix.lower()
    if ext in {".csv", ".tsv"}:
        print(f"  • Reading CSV {p.name}")
        prompts = []
        with p.open(encoding="utf-8-sig", newline="") as f:
            try:
                dialect = csv.Sniffer().sniff(f.read(2048), delimiters=",\t")
                f.seek(0)
            except csv.Error:
                f.seek(0)
                dialect = csv.get_dialect("excel")
            reader = csv.reader(f, dialect)
            first = next(reader, [])
            if first and first[0].lower().strip() == "prompt":
                pass
            else:
                if first and first[0].strip():
                    prompts.append(first[0].strip())
            for row in reader:
                if row and row[0].strip():
                    prompts.append(row[0].strip())
        return prompts
    elif ext == ".txt":
        print(f"  • Reading TXT {p.name}")
        return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    else:
        raise ValueError("Unsupported file type: " + ext)

# ---------------- Main driver ----------------------------------------------

def main():
    print("=== Dreamina Multi-Account Generator ===")
    accounts = load_accounts(COOKIE_FOLDER)
    if not accounts:
        return

    folder = input("\n📁 Folder with prompt files (.txt/.csv): ").strip("'\"")
    prompt_dir = Path(folder)
    if not prompt_dir.is_dir():
        print(f"❌ Not a folder: {folder}")
        return

    files = sorted(prompt_dir.glob("*.csv")) + sorted(prompt_dir.glob("*.txt"))
    if not files:
        print("❌ No .csv or .txt files found.")
        return
    print(f"✅ {len(files)} prompt file(s) discovered")

    print("\n— Global generation settings —")
    shared = get_generation_settings_from_user()

    ratio_key_str = "unknown"
    for key, (w, h) in ASPECT_RATIOS.items():
        if shared.get('width') == w and shared.get('height') == h:
            ratio_key_str = key
            break
    ratio_for_name = ratio_key_str.split(" ")[0].replace(":", "-")

    save_mode = get_save_mode_from_user()

    loops = 1
    while True:
        lp = input("\n🔁 Repeat each prompt how many times? (default 1): ").strip()
        if not lp:
            break
        if lp.isdigit() and int(lp) > 0:
            loops = int(lp)
            break
        print("❌ Positive integer, please")

    mpa_raw = input("⏳ Max prompts per account (Enter = no limit): ").strip()
    max_per_acc = int(mpa_raw) if mpa_raw.isdigit() and int(mpa_raw) > 0 else None

    with sync_playwright() as p:
        # Cấu hình browser với debug settings
        launch_options = {
            "headless": not SHOW_BROWSER,  # Sử dụng cấu hình debug
            "slow_mo": CLICK_DELAY if SLOW_MODE else 0,
            "args": BROWSER_ARGS
        }
        
        if DEBUG_MODE:
            print(f"🚀 Launching browser with debug settings:")
            print(f"   • Headless: {not SHOW_BROWSER}")
            print(f"   • Slow motion: {CLICK_DELAY}ms")
            print(f"   • Browser args: {BROWSER_ARGS}")
        
        browser = p.chromium.launch(**launch_options)
        for file_path in files:
            print("\n" + "=" * 80)
            print(f"🚀 FILE: {file_path.name}")
            print("=" * 80)

            try:
                prompts = load_prompts_from_file(file_path)
            except Exception as exc:
                print(f"❌ {exc}")
                continue

            if not prompts:
                print("No prompts, skipping")
                continue

            if loops > 1:
                prompts = [p for p in prompts for _ in range(loops)]
                print(f"  • Repetition: each prompt ×{loops}")
            print(f"Total generation jobs: {len(prompts)}")

            remain = prompts[:]
            acc_idx = 0
            g_counter = 1

            sub = f"{sanitize_filename(file_path.stem)}_{ratio_for_name}"
            wm_dir  = Path(WATERMARK_DIR) / sub
            pre_dir = Path(PREVIEW_DIR) / sub

            while remain:
                if acc_idx >= len(accounts):
                    print("⚠️  Out of accounts")
                    break

                acc = accounts[acc_idx]
                credits = get_single_account_credits(acc, browser)
                if credits is None or credits < CREDITS_PER_GENERATION:
                    print(f"  • Skipping {acc['name']} (no/low credits)")
                    acc_idx += 1
                    continue

                if max_per_acc:
                    to_take = min(max_per_acc, len(remain))
                else:
                    to_take = min(credits // CREDITS_PER_GENERATION, len(remain))

                if to_take == 0:
                    acc_idx += 1
                    continue

                chunk_prompts = remain[:to_take]
                print(f"\n== {acc['name']} will handle {to_take} prompt(s) ==")

                processed = 0
                while processed < to_take:
                    start = processed
                    end   = processed + PROMPT_CHUNK_SIZE
                    chunk = chunk_prompts[start:end]
                    if not chunk:
                        break
                    ck_no = start // PROMPT_CHUNK_SIZE + 1
                    ck_tot= (to_take + PROMPT_CHUNK_SIZE - 1) // PROMPT_CHUNK_SIZE
                    print(f"\n--- Chunk {ck_no}/{ck_tot} ({len(chunk)} prompts) ---")

                    # Prepare job info with global prompt numbers for consistent naming.
                    prompt_jobs_with_indices = [
                        {'prompt': p, 'prompt_no': g_counter + i}
                        for i, p in enumerate(chunk)
                    ]
                    base_filename_info = {
                        'csv_name': file_path.stem,
                        'ratio_string': ratio_for_name
                    }
                    
                    # Phase 1 always runs to generate images on the server.
                    # We just decide whether to *save* the watermarked files locally.
                    img_gen = run_generation_phase_for_account(
                        prompt_jobs_with_indices, acc, shared, base_filename_info, wm_dir,
                        save_watermarked=(save_mode in [1, 3]) # True if mode 1 or 3
                    )

                    # Phase 2 (scraping) only runs if requested.
                    if img_gen and save_mode in [2, 3]:
                        print(f"  • Wait {GALLERY_UPDATE_DELAY}s for gallery refresh…")
                        time.sleep(GALLERY_UPDATE_DELAY)
                        run_scraping_phase(img_gen, acc, chunk,
                                           shared, g_counter, pre_dir, browser,
                                           file_path.stem, ratio_for_name)
                    elif save_mode == 1:
                        print("  • Skipping Phase 2 (watermark-only mode).")
                    else:
                        print("  • No images generated, skipping scrape.")


                    processed += len(chunk)
                    g_counter += len(chunk)

                remain = remain[to_take:]
                acc_idx += 1

            print(f"\n✨ Finished {file_path.name}")
            if save_mode in [2, 3]:
                print(f"   Previews → {pre_dir.resolve()}")
            if save_mode in [1, 3]:
                print(f"   Watermarks → {wm_dir.resolve()}")
            if remain:
                print(f"⚠️  {len(remain)} prompt(s) unprocessed")

    print("\n🎉 ALL FILES DONE 🎉")

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()