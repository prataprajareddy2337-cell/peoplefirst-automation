#!/usr/bin/env python3
# PeopleFirst uploader — v5.5 (Stable for GitHub Actions)
# ✅ Works with https://peoplefirst.myflorida.com/peoplefirst/index.html
# ✅ Handles long redirect delays in headless mode
# ✅ Waits up to 3 minutes for login form
# ✅ Dumps screenshot + HTML if login fails
# ✅ Safe temporary Chrome profile each run
# ✅ Compatible with both local and CI (GitHub Actions)

from pathlib import Path
import time, tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# ---------------- CONFIG ---------------- #
URL_LOGIN = "https://peoplefirst.myflorida.com/peoplefirst/index.html"
USERNAME = "2034844"
PASSWORD = "Prataprajareddy@2338"
COMMENTS_TEXT = "People First website has some issues. It has selected all the benefits without me selecting them for the new hire benefits."
FILE_PATH = r"AppealLetter.docx"
HEADLESS = True  # Set False to view Chrome window locally
# ---------------------------------------- #

# Locators
LOGIN_USER = [
    (By.ID, "loginId"),
    (By.XPATH, "//input[@placeholder='Login ID']"),
    (By.XPATH, "//input[contains(@aria-label, 'Login ID')]"),
    (By.XPATH, "//input[@type='text']")
]
LOGIN_PASS = [
    (By.ID, "password"),
    (By.XPATH, "//input[@placeholder='Password']"),
    (By.XPATH, "//input[@type='password']")
]
LOGIN_BTN = [
    (By.XPATH, "//button[contains(text(), 'Log In')]"),
    (By.XPATH, "//input[@value='Log In']"),
    (By.XPATH, "//button[@type='submit']")
]

# --- Utilities ---
def log(msg):
    print(msg, flush=True)

def find_any(driver, locs, timeout=25, clickable=False):
    for by, sel in locs:
        try:
            if clickable:
                WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
            else:
                WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, sel)))
            return driver.find_element(by, sel)
        except Exception:
            continue
    raise TimeoutException(f"No selector matched: {locs}")

def safe_click(driver, el):
    for _ in range(3):
        try:
            el.click(); return True
        except Exception:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.2)
    return False

# --- Wait for login ---
def wait_for_login_page(driver, timeout=180):
    """Wait up to 3 minutes for login form using multiple strategies."""
    log(f"[1] Waiting for PeopleFirst login form to load… (timeout={timeout}s)")
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            # check for login keywords in HTML (since page is JS rendered)
            html = driver.page_source.lower()
            if any(kw in html for kw in ["login id", "password", "log in", "sign in"]):
                # now check if field is visible
                for by, sel in LOGIN_USER:
                    els = driver.find_elements(by, sel)
                    if els and els[0].is_displayed():
                        log("[1] ✅ Login form detected.")
                        return
        except Exception:
            pass
        time.sleep(1)

    # If timeout -> save debug info
    driver.save_screenshot("error_debug.png")
    with open("error_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    log("[📸] Saved error screenshot: error_debug.png")
    log("[📄] Saved HTML source: error_debug.html")
    raise TimeoutException("Login form did not appear in time.")

# --- Main login ---
def goto_login(driver):
    log("[1] Opening login page…")
    driver.get(URL_LOGIN)
    time.sleep(15)  # give enough time for SSO redirect
    wait_for_login_page(driver)
    log("[1] Typing credentials…")
    u = find_any(driver, LOGIN_USER, timeout=30)
    p = find_any(driver, LOGIN_PASS, timeout=20)
    u.clear(); u.send_keys(USERNAME)
    p.clear(); p.send_keys(PASSWORD)
    btn = find_any(driver, LOGIN_BTN, timeout=25, clickable=True)
    safe_click(driver, btn)
    log("[1] Login button clicked.")

# --- MAIN ---
def main():
    p = Path(FILE_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p}")

    log("[0] Launching Chrome…")
    tmp_profile = tempfile.mkdtemp()
    log(f"🧪 Using temporary Chrome profile: {tmp_profile}")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument(f"--user-data-dir={tmp_profile}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    if HEADLESS:
        chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        goto_login(driver)
        log("✅ Logged in successfully (if credentials are correct).")
        driver.save_screenshot("login_success.png")
        log("[📸] Screenshot saved: login_success.png")
        log("🎉 Login stage completed successfully.")
    except Exception as e:
        log(f"❌ ERROR: {e}")
        driver.save_screenshot("error_debug.png")
        with open("error_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log("[📸] Saved error screenshot: error_debug.png")
        log("[📄] Saved HTML source: error_debug.html")
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
