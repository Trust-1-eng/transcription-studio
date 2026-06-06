"""
UI Smoke Test — Assembly Transcription Studio
Uses Playwright to verify all UI interactions work.
"""
import sys
import time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0

def ok(name, detail=""):
    global PASS
    PASS += 1
    print(f"\033[32m✓ {name:<50} {detail}\033[0m")

def fail(name, detail=""):
    global FAIL
    FAIL += 1
    print(f"\033[31m✗ {name:<50} {detail}\033[0m")

def check(name, condition, detail=""):
    if condition:
        ok(name, detail)
    else:
        fail(name, detail)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ─── 1. PAGE LOAD ───
        print("\n─── Page Load ───")
        page.goto(BASE)
        check("Page loads", page.title() == "Transcription Studio", f"title='{page.title()}'")

        # Fonts loaded via CSS @import
        check("CSS loads", page.locator("link[href*='style.css']").count() == 1)
        check("JS loads", page.locator("script[src*='app.js']").count() == 1)

        # ─── 2. HEADER ───
        print("\n─── Header ───")
        check("Logo visible", page.locator(".logo").is_visible())
        check("API status dot exists", page.locator(".dot").count() >= 1)
        check("History button exists", page.locator("#btnHistory").is_visible())

        # Wait for API health check
        page.wait_for_timeout(2000)
        api_label = page.locator("#apiLabel").text_content()
        check("API connected", "Connected" in api_label, api_label)

        # ─── 3. STEP INDICATOR ───
        print("\n─── Step Indicator ───")
        dots = page.locator(".step-dot")
        check("4 step dots", dots.count() == 4)
        check("Step 1 is active", dots.nth(0).get_attribute("class") and "active" in dots.nth(0).get_attribute("class"))

        # ─── 4. SOURCE STEP — TABS ───
        print("\n─── Source Step: Tabs ───")
        check("Upload tab visible", page.locator(".tab").nth(0).is_visible())
        check("URL tab visible", page.locator(".tab").nth(1).is_visible())

        # Switch to URL tab
        page.locator(".tab").nth(1).click()
        page.wait_for_timeout(300)
        check("URL pane visible after click", page.locator("#pane-url").is_visible())
        check("File pane hidden", not page.locator("#pane-file").is_visible())

        # Switch back to File tab
        page.locator(".tab").nth(0).click()
        page.wait_for_timeout(300)
        check("File pane visible again", page.locator("#pane-file").is_visible())

        # ─── 5. SOURCE STEP — DROPZONE ───
        print("\n─── Source Step: Dropzone ───")
        check("Dropzone visible", page.locator("#dropzone").is_visible())
        check("Browse button exists", page.locator("#btnBrowse").is_visible())
        check("Configure btn disabled", page.locator("#btnToOptions").is_disabled())

        # ─── 6. FILE UPLOAD ───
        print("\n─── File Upload ───")
        # Create a tiny WAV in memory via ffmpeg
        import subprocess, tempfile, os
        test_audio = os.path.join(tempfile.gettempdir(), "ui_test.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", test_audio],
            capture_output=True, timeout=10
        )

        # Upload via file input
        page.locator("#fileInput").set_input_files(test_audio)
        page.wait_for_timeout(2000)

        # Status card should appear
        status_visible = page.locator("#sourceStatus").is_visible()
        check("Status card appears after upload", status_visible)

        btn_enabled = not page.locator("#btnToOptions").is_disabled()
        check("Configure btn enabled after upload", btn_enabled)

        # ─── 7. NAVIGATE TO OPTIONS ───
        print("\n─── Options Step ───")
        page.locator("#btnToOptions").click()
        page.wait_for_timeout(500)

        options_visible = page.locator("#step-options").is_visible()
        check("Options step visible", options_visible)

        source_hidden = not page.locator("#step-source").is_visible()
        check("Source step hidden", source_hidden)

        # Step indicator updated
        step2_class = page.locator(".step-dot").nth(1).get_attribute("class") or ""
        check("Step 2 dot active", "active" in step2_class)

        # ─── 8. OPTIONS — LANGUAGE MODES ───
        print("\n─── Options: Language ───")
        check("AUTO button exists", page.locator("#btnAuto").is_visible())
        check("SELECT button exists", page.locator("#btnManual").is_visible())

        # Switch to manual
        page.locator("#btnManual").click()
        page.wait_for_timeout(300)
        check("Manual pane visible", page.locator("#manualPane").is_visible())
        check("Auto pane hidden", not page.locator("#autoPane").is_visible())

        # Switch back to auto
        page.locator("#btnAuto").click()
        page.wait_for_timeout(300)
        check("Auto pane visible again", page.locator("#autoPane").is_visible())

        # ─── 9. OPTIONS — TOGGLES ───
        print("\n─── Options: Toggles ───")
        toggles = [
            ("speakerLabels", "Speaker Labels"),
            ("punctuate", "Punctuate"),
            ("formatText", "Format Text"),
            ("disfluencies", "Disfluencies"),
            ("entityDetection", "Entity Detection"),
            ("sentimentAnalysis", "Sentiment Analysis"),
            ("contentSafety", "Content Safety"),
            ("iabCategories", "IAB Categories"),
            ("autoHighlights", "Auto Highlights"),
            ("piiEnabled", "PII Redaction"),
        ]
        for tid, name in toggles:
            el = page.locator(f"#{tid}")
            exists = el.count() > 0
            check(f"Toggle: {name}", exists)

        # Toggle speaker labels ON via JS (checkbox hidden in toggle)
        page.evaluate("document.getElementById('speakerLabels').click()")
        page.wait_for_timeout(300)
        spk_body = page.locator("#speakerBody")
        has_disabled = "disabled" in (spk_body.get_attribute("class") or "")
        check("Speaker body enabled when toggled", not has_disabled)

        # Toggle OFF
        page.evaluate("document.getElementById('speakerLabels').click()")
        page.wait_for_timeout(300)
        has_disabled = "disabled" in (spk_body.get_attribute("class") or "")
        check("Speaker body disabled when untoggled", has_disabled)

        # ─── 10. OPTIONS — ADVANCED ───
        print("\n─── Options: Advanced ───")
        adv_body = page.locator("#advBody")
        check("Advanced body hidden by default", not adv_body.is_visible())

        page.locator("#advHead").click()
        page.wait_for_timeout(300)
        check("Advanced body visible after click", adv_body.is_visible())

        check("Key terms input exists", page.locator("#keyInput").is_visible())
        check("Speech threshold exists", page.locator("#speechThresh").is_visible())
        check("Trim From exists", page.locator("#trimFrom").is_visible())
        check("Trim To exists", page.locator("#trimTo").is_visible())

        # ─── 11. OPTIONS — TRANSLATION ───
        print("\n─── Options: Translation ───")
        check("Translation search exists", page.locator("#transSearch").is_visible())
        check("Translation list exists", page.locator("#transList").is_visible())
        trans_opts = page.locator("#transOpts")
        check("Translation opts hidden by default", not trans_opts.is_visible())

        # ─── 12. OPTIONS — CONTENT SAFETY CONF ───
        print("\n─── Options: Content Safety ───")
        page.evaluate("document.getElementById('contentSafety').click()")
        page.wait_for_timeout(300)
        check("Safety conf wrap visible", page.locator("#safetyConfWrap").is_visible())
        page.evaluate("document.getElementById('contentSafety').click()")

        # ─── 13. BACK BUTTON ───
        print("\n─── Navigation ───")
        page.locator("#btnBackSource").click()
        page.wait_for_timeout(500)
        check("Back to source works", page.locator("#step-source").is_visible())

        # Go to options again
        page.locator("#btnToOptions").click()
        page.wait_for_timeout(500)

        # ─── 14. HISTORY DRAWER ───
        print("\n─── History Drawer ───")
        page.locator("#btnHistory").click()
        page.wait_for_timeout(300)
        check("History drawer visible", page.locator("#historyDrawer").is_visible())

        check("Resume input exists", page.locator("#resumeInput").is_visible())
        check("Resume btn exists", page.locator("#btnResume").is_visible())

        page.locator("#btnCloseHistory").click()
        page.wait_for_timeout(300)
        check("History drawer closed", not page.locator("#historyDrawer").is_visible())

        # ─── 15. TOAST ───
        print("\n─── Toast ───")
        # Trigger toast via JS
        page.evaluate("toast('Test message', 'success')")
        page.wait_for_timeout(300)
        toast = page.locator("#toast")
        check("Toast visible", toast.is_visible())
        check("Toast has success class", "toast-ok" in (toast.get_attribute("class") or ""))

        # ─── 16. NO CONSOLE ERRORS ───
        print("\n─── Console Errors ───")
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.reload()
        page.wait_for_timeout(2000)
        # Filter out known non-issues (favicon etc)
        real_errors = [e for e in errors if "favicon" not in e.lower()]
        check("No JS console errors", len(real_errors) == 0, f"{len(real_errors)} errors" if real_errors else "clean")

        # ─── 17. SCREENSHOT ───
        print("\n─── Screenshot ───")
        page.goto(BASE)
        page.wait_for_timeout(1500)
        screenshot_path = "/tmp/transcription_studio_ui.png"
        page.screenshot(path=screenshot_path, full_page=True)
        check("Screenshot saved", True, screenshot_path)

        browser.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"  UI Tests:  \033[32m{PASS} passed\033[0m  \033[31m{FAIL} failed\033[0m")
    print(f"{'='*60}\n")

    return FAIL == 0

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
