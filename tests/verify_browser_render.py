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
OUTPUT_DIR = Path(os.environ.get("YCM_QA_OUTPUT_DIR", BASE_DIR / "output"))
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
        
        # Keep the standalone concept boundary visible before the branded site.
        concept_notice = page.locator("#concept-notice")
        assert concept_notice.is_visible(), "Standalone sample needs a visible concept notice"
        assert "not the official Yamhill County Mushrooms website" in concept_notice.inner_text()
        assert concept_notice.bounding_box()["y"] + concept_notice.bounding_box()["height"] <= page.locator("header.topbar").bounding_box()["y"], "Concept notice must sit in page flow, not over the artwork"

        # The existing handler opens mailto; the page must not promise delivery.
        inquiry_form = page.locator("#wholesaleForm")
        assert inquiry_form.locator("button[type=submit]").inner_text() == "Open Wholesale Inquiry Email Draft"
        assert "Review it and send it there" in inquiry_form.inner_text()
        assert "This website does not send your inquiry" in inquiry_form.inner_text()
        assert "Sent directly" not in inquiry_form.inner_text()

        # Verify Chef Pairings section exists and has Maitake
        pairings = page.locator("#pairings")
        assert pairings.count() > 0, "Chef pairings section (#pairings) must exist"
        pairings_text = pairings.inner_text()
        assert "Maitake" in pairings_text, "Maitake pairing must be present in chef pairings"
        assert "Executive Chef Receiving & Walk-In Storage Standards" in pairings_text, "Storage standards card missing"
        
        # Verify Order Manifest / Inquiry section & Pallet Calculator
        order_desk = page.locator("#inquiry")
        assert order_desk.count() > 0, "Inquiry section (#inquiry) must exist"
        
        # Test adding SKU and calculating net weight / pallet cube
        add_btn = page.locator(".btn-add-sku").first
        add_btn.click()
        add_btn.click()
        cases_text = page.locator("#totalCasesCount").inner_text()
        assert int(cases_text) >= 2, f"Expected at least 2 cases, got {cases_text}"
        weight_text = page.locator("#totalNetWeight").inner_text()
        assert "lbs" in weight_text and weight_text != "0 lbs", f"Weight should be calculated, got {weight_text}"
        assert page.locator("#btnExportManifest").is_visible(), "Export PO CSV button must be visible"
        manifest_shot = OUTPUT_DIR / "ycm_manifest_pallet_calc_verified.png"
        page.locator(".selected-items-panel").screenshot(path=str(manifest_shot))
        print(f"YCM Manifest & Pallet calculation screenshot saved: {manifest_shot}")
        
        # Take full desktop screenshot
        desktop_shot = OUTPUT_DIR / "ycm_desktop_render_verified.png"
        page.screenshot(path=str(desktop_shot), full_page=True)
        print(f"YCM Desktop screenshot saved: {desktop_shot}")
        
        # Capture specific Chef Pairings element screenshot
        pairing_shot = OUTPUT_DIR / "ycm_chef_pairings_verified.png"
        pairings.screenshot(path=str(pairing_shot))
        print(f"YCM Chef pairings screenshot saved: {pairing_shot}")
        
        # Careers must remain an independent, inactive concept, not a hiring portal.
        careers_url = (BASE_DIR / "careers.html").as_uri()
        page.goto(careers_url, wait_until="networkidle")
        careers_notice = page.locator("#concept-notice")
        assert careers_notice.is_visible()
        assert "not the official Yamhill County Mushrooms website" in careers_notice.inner_text()
        assert "No current job openings" in careers_notice.inner_text()
        assert careers_notice.bounding_box()["y"] + careers_notice.bounding_box()["height"] <= page.locator(".ribbon").bounding_box()["y"]
        assert "Concept" in page.title()
        careers_body = page.locator("body").inner_text()
        assert "always hiring" not in careers_body.lower()
        assert "Current Openings" not in careers_body
        assert "Send Application to Hiring Line" not in careers_body
        assert "does not send applications" in page.locator("#apply").inner_text()
        career_form = page.locator("#careerApplyForm")
        assert career_form.locator("fieldset[disabled]").count() == 1
        assert career_form.locator("input:enabled, select:enabled, textarea:enabled, button:enabled").count() == 0
        assert page.locator("#btnSubmitApp").inner_text() == "Email Draft Preview (Disabled)"
        assert page.locator("#btnSubmitApp").is_disabled()
        # Exercise the real no-data guard without entering personal details or sending.
        assert page.evaluate("""() => {
          const event = new Event('submit', {bubbles: true, cancelable: true});
          document.getElementById('careerApplyForm').dispatchEvent(event);
          return event.defaultPrevented && lastApplicationText === ''
            && !document.getElementById('applySuccessCard').classList.contains('active')
            && document.getElementById('btnSendEmailApp').getAttribute('href') === '#';
        }""")
        assert page.url == careers_url
        page.screenshot(path=str(OUTPUT_DIR / "careers_desktop_top_review.png"))
        page.locator("#apply").evaluate("section => window.scrollTo(0, window.scrollY + section.getBoundingClientRect().top - document.querySelector('header.topbar').getBoundingClientRect().height)")
        page.screenshot(path=str(OUTPUT_DIR / "careers_desktop_form_intro_review.png"))
        page.locator("#btnSubmitApp").scroll_into_view_if_needed()
        page.screenshot(path=str(OUTPUT_DIR / "careers_desktop_form_review.png"))

        # Each other directly reachable HTML entry also needs its own concept notice.
        for sample_name in ("harvest_log_sheet.html", "label_crimini_10lb.html"):
            page.goto((BASE_DIR / sample_name).as_uri(), wait_until="networkidle")
            assert page.locator("#concept-notice").is_visible(), sample_name
            assert "not an official Yamhill County Mushrooms document" in page.locator("#concept-notice").inner_text()
            page.screenshot(path=str(OUTPUT_DIR / (sample_name + ".desktop_review.png")))
            page.emulate_media(media="print")
            assert page.locator("#concept-notice").is_visible(), "Print must preserve the concept notice"
            if sample_name == "label_crimini_10lb.html":
                assert page.locator("#caseLabel #label-concept-notice").is_visible()
                assert "Not for product labeling" in page.locator("#caseLabel").inner_text()
            else:
                assert "Independent Concept Sample" in page.locator(".sheet-footer").inner_text()
            page.screenshot(path=str(OUTPUT_DIR / (sample_name + ".print_style_review.png")))
            page.emulate_media(media="screen")

        context_desktop.close()
        
        # 2. Mobile Test (iPhone 14 / 390x844)
        context_mobile = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        page_mobile = context_mobile.new_page()
        page_mobile.goto(target_url, wait_until="networkidle")
        
        assert page_mobile.locator("#concept-notice").is_visible(), "Concept notice must be visible on mobile"
        assert page_mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile page must not overflow horizontally"
        page_mobile.screenshot(path=str(OUTPUT_DIR / "ycm_mobile_top_review.png"))

        mobile_shot = OUTPUT_DIR / "ycm_mobile_render_verified.png"
        page_mobile.screenshot(path=str(mobile_shot), full_page=True)
        print(f"YCM Mobile screenshot saved: {mobile_shot}")
        page_mobile.goto((BASE_DIR / "careers.html").as_uri(), wait_until="networkidle")
        assert page_mobile.locator("#concept-notice").is_visible()
        assert page_mobile.locator("#btnSubmitApp").is_disabled()
        assert page_mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Careers mobile page must not overflow"
        page_mobile.screenshot(path=str(OUTPUT_DIR / "careers_mobile_top_review.png"))
        page_mobile.locator("#apply").evaluate("section => window.scrollTo(0, window.scrollY + section.getBoundingClientRect().top - document.querySelector('header.topbar').getBoundingClientRect().height)")
        page_mobile.screenshot(path=str(OUTPUT_DIR / "careers_mobile_form_intro_review.png"))
        page_mobile.locator("#btnSubmitApp").scroll_into_view_if_needed()
        page_mobile.screenshot(path=str(OUTPUT_DIR / "careers_mobile_form_review.png"))
        context_mobile.close()
        
        browser.close()
        
    assert len(console_errors) == 0, f"Found console errors: {console_errors}"
    print("YAMHILL COUNTY MUSHROOMS BROWSER RENDER & INTERACTION TESTS PASSED (0 console errors).")

if __name__ == "__main__":
    test_ycm_browser_render()
