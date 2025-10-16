#!/usr/bin/env python3
# PeopleFirst uploader — v5.0 (Headless + Secrets Safe)
# - Uses environment variables for credentials (GitHub Secrets or .env)
# - Runs headless for GitHub Actions
# - Includes Chrome flags for Ubuntu CI environments
# - Clean, reliable logging and retry mechanisms

from pathlib import Path
import time, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load credentials from environment (safe for GitHub Secrets)
# -------------------------------------------------------------------
load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

URL_LOGIN = "https://peoplefirst.myflorida.com/peoplefirst/index.html"
COMMENTS_TEXT = "People First website has some issues. It has selected all the benefits without me selecting them for the new hire benefits."
FILE_PATH = r"C:\Users\prata\Downloads\AppealLetter.docx"

# Headless Chrome mode (works inside GitHub Actions)
HEADLESS = True
CLICK_NEW_RETRIES = 10

# -------------------------------------------------------------------
# Locators
# -------------------------------------------------------------------
BLOCK_LAYER = (By.ID, "sap-ui-blocklayer-popup")
BUSY_DIALOG = (By.CSS_SELECTOR, ".sapMBusyDialog")

LOGIN_USER = [
    (By.CSS_SELECTOR, "input[placeholder='Login ID']"),
    (By.ID, "userid"),
    (By.NAME, "userid"),
]
LOGIN_PASS = [
    (By.CSS_SELECTOR, "input[placeholder='Password']"),
    (By.ID, "password"),
    (By.NAME, "password"),
]
LOGIN_BTN = [
    (By.XPATH, "//button[normalize-space(.)='Log In']"),
    (By.CSS_SELECTOR, "button[type='submit']"),
    (By.XPATH, "//button[contains(., 'Log In') or contains(., 'Login')]"),
]

UPLOAD_HEADER = [
    (By.XPATH, "//bdi[normalize-space(.)='Upload']/ancestor::*[self::a or self::button][1]"),
]
NEW_BUTTON = [
    (By.XPATH, "//bdi[normalize-space(.)='New']/ancestor::*[self::button or self::span][1]"),
]
COMMENTS = [
    (By.XPATH, "//textarea[contains(@placeholder,'Add comments') or contains(@id,'comment')]"),
]
ADD_ATTACH = [(By.XPATH, "//*[contains(., 'Add attachments')]/ancestor::*[self::button or self::a or self::div][1]")]
FILE_INPUT = [(By.CSS_SELECTOR, "input[type='file']")]
SUBMIT = [
    (By.XPATH, "//bdi[normalize-space(.)='Submit']/ancestor::*[self::button or self::span][1]"),
]

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def log(msg): print(msg, flush=True)

def wait_clear(driver, timeout=60):
    """Wait for any busy overlay to disappear"""
    end = time.time() + timeout
    while time.time() < end:
        blocked = False
        try:
            if any(e.is_displayed() for e in driver.find_elements(*BLOCK_LAYER)): blocked = True
        except: pass
        try:
            if any(e.is_displayed() for e in driver.find_elements(*BUSY_DIALOG)): blocked = True
        except: pass
        if not blocked: return True
        time.sleep(0.2)
    return False

def find_any(driver, locator_list, timeout=25, clickable=False):
    for by, sel in locator_list:
        try:
            if clickable:
                WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
            else:
                WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, sel)))
            return driver.find_element(by, sel)
        except Exception:
            continue
    raise TimeoutException(f"No selector matched: {locator_list}")

def safe_click(driver, el):
    """Try several safe ways to click an element"""
    try: el.click(); return True
    except (ElementClickInterceptedException, StaleElementReferenceException): pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.1); el.click(); return True
    except Exception: pass
    try:
        driver.execute_script("arguments[0].click();", el); return True
    except Exception: return False

# -------------------------------------------------------------------
# Core steps
# -------------------------------------------------------------------
def goto_login(driver):
    log("[1] Opening login page…")
    driver.get(URL_LOGIN)
    u = find_any(driver, LOGIN_USER, timeout=30)
    p = find_any(driver, LOGIN_PASS, timeout=30)
    u.clear(); u.send_keys(USERNAME)
    p.clear(); p.send_keys(PASSWORD)
    btn = find_any(driver, LOGIN_BTN, timeout=25, clickable=True)
    log("[1] Clicking Log In…")
    safe_click(driver, btn)

def click_upload(driver):
    log("[2] Waiting for overlays to clear and clicking Upload…")
    wait_clear(driver, 60)
    up = find_any(driver, UPLOAD_HEADER, timeout=50, clickable=True)
    safe_click(driver, up)
    time.sleep(1)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        log("[2] Switched to new tab.")

def click_new(driver):
    log("[3] Clicking New (retry if overlays show)…")
    for attempt in range(1, CLICK_NEW_RETRIES + 1):
        wait_clear(driver, 30)
        try:
            newb = find_any(driver, NEW_BUTTON, timeout=30)
        except TimeoutException:
            log(f"  attempt {attempt}: New not found… retrying")
            time.sleep(0.5); continue
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", newb)
        if not safe_click(driver, newb):
            log(f"  attempt {attempt}: click failed")
        time.sleep(0.8)
        try:
            _ = find_any(driver, FILE_INPUT, timeout=3)
            log("[3] New clicked; form visible.")
            return True
        except Exception:
            log(f"  attempt {attempt}: form not visible yet.")
    raise TimeoutException("Form did not appear after clicking New.")

def main():
    p = Path(FILE_PATH)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    log("[0] Launching Chrome in headless mode…")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    try:
        goto_login(driver)
        click_upload(driver)
        click_new(driver)

        log("[4] Typing comments…")
        cmt = find_any(driver, COMMENTS, timeout=25)
        try: cmt.clear()
        except Exception: pass
        cmt.send_keys(COMMENTS_TEXT)

        log("[5] Attaching file…")
        try:
            addbtn = find_any(driver, ADD_ATTACH, timeout=6, clickable=True)
            safe_click(driver, addbtn)
            time.sleep(0.3)
        except Exception:
            pass
        finput = find_any(driver, FILE_INPUT, timeout=25)
        finput.send_keys(str(p.resolve()))

        log("[6] Submitting form…")
        sub = find_any(driver, SUBMIT, timeout=25, clickable=True)
        safe_click(driver, sub)

        wait_clear(driver, 25)
        log("✅ Upload Complete — Appeal letter submitted successfully!")
    finally:
        time.sleep(2)
        driver.quit()

# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
