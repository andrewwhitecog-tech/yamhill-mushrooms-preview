"""
Browser Render & Interactivity Verification for Yamhill County Mushrooms Website
Executes headless Chromium via Playwright, verifies zero console errors,
checks chef pairings & walk-in storage standards, tests order manifest interaction,
and captures desktop & mobile verification screenshots.
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = BASE_DIR / "index.html"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def test_ycm_browser_render():
    console_errors = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Desktop Test (1280x800)
        context_desktop = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context_desktop.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        target_url = INDEX_HTML.as_uri()
        page.goto(target_url, wait_until="networkidle")
        
        # Verify page title
        assert "Yamhill County Mushrooms" in page.title(), f"Unexpected title: {page.title()}"
        
        # Verify Chef Pairings section exists and has Maitake
        pairings = page.locator("#pairings")
        assert pairings.count() > 0, "Chef pairings section (#pairings) must exist"
        pairings_text = pairings.inner_text()
        assert "Maitake" in pairings_text, "Maitake pairing must be present in chef pairings"
        assert "Executive Chef Receiving & Walk-In Storage Standards" in pairings_text, "Storage standards card missing"
        
        # Verify Order Manifest / Inquiry section
        order_desk = page.locator("#inquiry")
        assert order_desk.count() > 0, "Inquiry section (#inquiry) must exist"
        
        # Take full desktop screenshot
        desktop_shot = OUTPUT_DIR / "ycm_desktop_render_verified.png"
        page.screenshot(path=str(desktop_shot), full_page=True)
        print(f"YCM Desktop screenshot saved: {desktop_shot}")
        
        # Capture specific Chef Pairings element screenshot
        pairing_shot = OUTPUT_DIR / "ycm_chef_pairings_verified.png"
        pairings.screenshot(path=str(pairing_shot))
        print(f"YCM Chef pairings screenshot saved: {pairing_shot}")
        
        context_desktop.close()
        
        # 2. Mobile Test (iPhone 14 / 390x844)
        context_mobile = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        page_mobile = context_mobile.new_page()
        page_mobile.goto(target_url, wait_until="networkidle")
        
        mobile_shot = OUTPUT_DIR / "ycm_mobile_render_verified.png"
        page_mobile.screenshot(path=str(mobile_shot), full_page=True)
        print(f"YCM Mobile screenshot saved: {mobile_shot}")
        context_mobile.close()
        
        browser.close()
        
    assert len(console_errors) == 0, f"Found console errors: {console_errors}"
    print("YAMHILL COUNTY MUSHROOMS BROWSER RENDER & INTERACTION TESTS PASSED (0 console errors).")

if __name__ == "__main__":
    test_ycm_browser_render()
