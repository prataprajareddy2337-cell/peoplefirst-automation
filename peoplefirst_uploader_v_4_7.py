#!/usr/bin/env python3
# PeopleFirst uploader — v5.3 (Final)
# ✅ Works with https://peoplefirst.myflorida.com/peoplefirst/index.html
# ✅ Waits for redirect/login form
# ✅ Fixed login field detection
# ✅ Avoids Chrome profile reuse errors
# ✅ Saves screenshots for debugging

from pathlib import Path
import time, tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# ---------------- CONFIG ---------------- #
URL_LOGIN = "https://peoplefirst.myflorida.com/peoplefirst/index.html"
USERNAME = "2034844"
PASSWORD = "Prataprajareddy@2338"
COMMENTS_TEXT = "People First website has some issues. It has selected all the benefits without me selecting them for the new hire benefits."
FILE_PATH = r"AppealLetter.docx"
HEADLESS = True  # Set False to watch browser open
CLICK_NEW_RETRIES = 10
# ---------------------------------------- #

# Locators (based on actual site)
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

UPLOAD_HEADER = [
    (By.XPATH, "//bdi[normalize-space(.)='Upload']/ancestor::*[self::a or self::button][1]"),
    (By.LINK_TEXT, "Upload"),
    (By.XPATH, "//a[@title='Upload' or @title='Submit']")
]
NEW_BUTTON = [
    (By.XPATH, "//bdi[normalize-space(.)='New']/ancestor::*[self::button or self::span][1]"),
    (By.XPATH, "//button[contains(@id,'newButton') or @aria-label='New']")
]
COMMENTS = [
    (By.XPATH, "//textarea[contains(@placeholder,'Add comments') or contains(@id,'comment')]"),
    (By.TAG_NAME, "textarea")
]
FILE_INPUT = [(By.CSS_SELECTOR, "input[type='file']"), (By.XPATH, "//input[@type='file']")]
SUBMIT = [
    (By.XPATH, "//bdi[normalize-space(.)='Submit']/ancestor::*[self::button or self::span][1]"),
    (By.XPATH, "//button[normalize-space(.)='Submit']")
]

def log(msg):
    print(msg, flush=True)

def wait_for_login_page(driver, timeout=60):
    """Wait until the login fields appear (after redirect)."""
    log("[1] Waiting for PeopleFirst login form to load…")
    end = time.time() + timeout
    while time.time() < end:
        try:
            if driver.find_elements(By.XPATH, "//input[@placeholder='Login ID']"):
                log("[1] ✅ Login form detected.")
                return True
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutException("Login form did not appear in time.")

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

def goto_login(driver):
    log("[1] Opening login page…")
    driver.get(URL_LOGIN)
    wait_for_login_page(driver)
    u = find_any(driver, LOGIN_USER, timeout=30)
    p = find_any(driver, LOGIN_PASS, timeout=20)
    log("[1] Typing credentials…")
    u.clear(); u.send_keys(USERNAME)
    p.clear(); p.send_keys(PASSWORD)
    btn = find_any(driver, LOGIN_BTN, timeout=20, clickable=True)
    safe_click(driver, btn)
    log("[1] Login button clicked.")

def wait_clear(driver, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        try:
            block = driver.find_elements(By.ID, "sap-ui-blocklayer-popup")
            busy = driver.find_elements(By.CSS_SELECTOR, ".sapMBusyDialog")
            if not any(e.is_displayed() for e in block + busy):
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False

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
    chrome_options.add_argument(f"--user-data-dir={tmp_profile}")
    chrome_options.add_argument("--start-maximized")
    if HEADLESS:
        chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        goto_login(driver)
        log("✅ Logged in successfully (if credentials are correct).")
        time.sleep(2)
        log("🎉 You can now add the upload flow after this step.")
        driver.save_screenshot("login_success.png")
        log("[📸] Screenshot saved: login_success.png")
    except Exception as e:
        log(f"❌ ERROR: {e}")
        driver.save_screenshot("error_debug.png")
        log("[📸] Saved error screenshot: error_debug.png")
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
