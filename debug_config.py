#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Debug Configuration for Dreamina Multi-Account Generator
Bạn có thể sửa đổi các cài đặt debug ở đây
"""

# === DEBUG SETTINGS ===
DEBUG_MODE = True               # Bật/tắt chế độ debug
SHOW_BROWSER = True            # Hiển thị cửa sổ trình duyệt
SLOW_MODE = True               # Chạy chậm để dễ theo dõi
SCREENSHOT_ON_ERROR = True     # Chụp ảnh màn hình khi có lỗi
VERBOSE_LOGGING = True         # Logs chi tiết

# === BROWSER SETTINGS ===
BROWSER_ARGS = [
    "--start-maximized",       # Mở cửa sổ tối đa
    "--disable-blink-features=AutomationControlled",  # Ẩn automation
    "--no-first-run",
    "--disable-default-apps"
]

if DEBUG_MODE:
    BROWSER_ARGS.extend([
        # "--auto-open-devtools-for-tabs",  # Tắt auto mở DevTools
        "--disable-web-security",        # Tắt web security để debug
    ])

# === TIMING SETTINGS ===
if SLOW_MODE:
    CLICK_DELAY = 1000         # Delay giữa các click (ms)
    NAVIGATION_DELAY = 3000    # Delay sau navigation (ms)
    ACTION_DELAY = 500         # Delay giữa các action (ms)
else:
    CLICK_DELAY = 100
    NAVIGATION_DELAY = 1000
    ACTION_DELAY = 100

print(f"🔧 Debug Configuration Loaded:")
print(f"   • Debug Mode: {DEBUG_MODE}")
print(f"   • Show Browser: {SHOW_BROWSER}")
print(f"   • Slow Mode: {SLOW_MODE}")
print(f"   • Screenshot on Error: {SCREENSHOT_ON_ERROR}")
print(f"   • Verbose Logging: {VERBOSE_LOGGING}")
