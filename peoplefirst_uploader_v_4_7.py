#!/usr/bin/env python3
# PeopleFirst uploader — v5.1
# ✅ Uses a unique Chrome temp profile every run (no session conflicts)
# ✅ Works on GitHub Actions, Replit, or locally
# ✅ Headless-safe and saves screenshot after upload

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
HEADLESS = True  # Keep True for GitHub Actions; set False for local debug
CLICK_NEW_RETRIES = 10
# ---------------------------------------- #

BLOCK_LAYER = (By.ID, "sap-ui-blocklayer-popup")
BUSY_DIALOG = (By.CSS_SELECTOR, ".sapMBusyDialog")

LOGIN_USER = [
    (By.CSS_SELECTOR, "input[placeholder='Login ID']"),
    (By.ID, "userid"),
    (By.NAME, "userid"),
    (By.XPATH, "//input[@type='text' and (contains(@aria-label,'Login') or contains(@placeholder,'Login'))]"),
]
LOGIN_PASS = [
    (By.CSS_SELECTOR, "input[placeholder='Password']"),
    (By.ID, "password"),
    (By.NAME, "password"),
    (By.XPATH, "//input[@type='password']"),
]
LOGIN_BTN = [
    (By.XPATH, "//button[normalize-space(.)='Log In']"),
    (By.CSS_SELECTOR, "button[type='submit']"),
    (By.XPATH, "//button[contains(., 'Log In') or contains(., 'Login')]"),
]
UPLOAD_HEADER = [
    (By.XPATH, "//bdi[normalize-space(.)='Upload']/ancestor::*[self::a or self::button][1]"),
    (By.LINK_TEXT, "Upload"),
    (By.XPATH, "//a[@title='Upload' or @title='Submit']"),
]
NEW_BUTTON = [
    (By.XPATH, "//bdi[normalize-space(.)='New']/ancestor::*[self::button or self::span][1]"),
    (By.XPATH, "//button[contains(@id,'newButton') or @aria-label='New']"),
]
COMMENTS = [
    (By.XPATH, "//textarea[contains(@placeholder,'Add comments') or contains(@id,'comment') or contains(@name,'comment')]"),
    (By.TAG_NAME, "textarea"),
]
FILE_INPUT = [(By.CSS_SELECTOR, "input[type='file']"), (By.XPATH, "//input[@type='file']")]
SUBMIT = [
    (By.XPATH, "//bdi[normalize-space(.)='Submit']/ancestor::*[self::button or self::span][1]"),
    (By.XPATH, "//button[.//bdi[normalize-space(.)='Submit'] or normalize-space(.)='Submit']"),
]

def log(msg): print(msg, flush=True)

def wait_clear(driver, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        blocked = False
        try:
            if any(e.is_displayed() for e in driver.find_elements(*BLOCK_LAYER)): blocked = True
        except Exception: pass
        try:
            if any(e.is_displayed() for e in driver.find_elements(*BUSY_DIALOG)): blocked = True
        except Exception: pass
        if not blocked: return True
        time.sleep(0.2)
    return False

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
    log("[1] Typing credentials…")
    u = find_any(driver, LOGIN_USER, timeout=30)
    p = find_any(driver, LOGIN_PASS, timeout=30)
    u.clear(); u.send_keys(USERNAME)
    p.clear(); p.send_keys(PASSWORD)
    btn = find_any(driver, LOGIN_BTN, timeout=25, clickable=True)
    safe_click(driver, btn)

def click_upload(driver):
    wait_clear(driver, 60)
    up = find_any(driver, UPLOAD_HEADER, timeout=50, clickable=True)
    safe_click(driver, up)
    time.sleep(1)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        log("[2] Switched to new tab.")

def click_new(driver):
    for i in range(1, CLICK_NEW_RETRIES + 1):
        wait_clear(driver, 20)
        try:
            newb = find_any(driver, NEW_BUTTON, timeout=20)
            if safe_click(driver, newb):
                _ = find_any(driver, FILE_INPUT, timeout=5)
                log("[3] Form visible.")
                return True
        except Exception:
            log(f"Retry {i}: 'New' not ready.")
            continue
    raise TimeoutException("Form never appeared after clicking New.")

def main():
    p = Path(FILE_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p}")

    log("[0] Launching Chrome…")

    # ✅ Create a unique Chrome temp profile to prevent session conflicts
    tmp_profile = tempfile.mkdtemp()
    log(f"🧪 Using temporary Chrome profile: {tmp_profile}")

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument(f"--user-data-dir={tmp_profile}")
    if HEADLESS:
        chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        goto_login(driver)
        click_upload(driver)
        click_new(driver)

        log("[5] Typing comments…")
        cmt = find_any(driver, COMMENTS, timeout=20)
        cmt.clear(); cmt.send_keys(COMMENTS_TEXT)

        log("[6] Uploading file…")
        finput = find_any(driver, FILE_INPUT, timeout=20)
        finput.send_keys(str(p.resolve()))
        time.sleep(2)

        log("[7] Submitting form…")
        sub = find_any(driver, SUBMIT, timeout=25, clickable=True)
        safe_click(driver, sub)
        wait_clear(driver, 25)
        log("🎉 ✅ Script finished successfully!")

        driver.save_screenshot("post_submit_debug.png")
        log("[📸] Screenshot saved: post_submit_debug.png")

    except Exception as e:
        log(f"❌ ERROR: {e}")
        driver.save_screenshot("error_debug.png")
        log("[📸] Saved error screenshot: error_debug.png")
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
