#!/usr/bin/env python3
# PeopleFirst uploader — v5.1 (headless + GitHub-ready + hardcoded creds)

from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# ------------------🔐 HARDCODED CREDENTIALS ------------------ #
USERNAME = "2034844"
PASSWORD = "Prataprajareddy@2338"

# ------------------📄 FILE PATH ------------------ #
# Uses the docx file in the repo root (GitHub can't access your Downloads folder)
FILE_PATH = "AppealLetter.docx"

URL_LOGIN = "https://peoplefirst.myflorida.com/peoplefirst/index.html"
COMMENTS_TEXT = "People First website has some issues. It has selected all the benefits without me selecting them for the new hire benefits."

HEADLESS = True
CLICK_NEW_RETRIES = 10

# ------------------🔍 LOCATORS ------------------ #
BLOCK_LAYER = (By.ID, "sap-ui-blocklayer-popup")
BUSY_DIALOG = (By.CSS_SELECTOR, ".sapMBusyDialog")
LOGIN_USER = [(By.ID, "userid")]
LOGIN_PASS = [(By.ID, "password")]
LOGIN_BTN = [(By.XPATH, "//button[contains(., 'Log In')]")]
UPLOAD_HEADER = [(By.XPATH, "//bdi[normalize-space(.)='Upload']/ancestor::*[self::a or self::button][1]")]
NEW_BUTTON = [(By.XPATH, "//bdi[normalize-space(.)='New']/ancestor::*[self::button or self::span][1]")]
COMMENTS = [(By.TAG_NAME, "textarea")]
ADD_ATTACH = [(By.XPATH, "//*[contains(., 'Add attachments')]/ancestor::*[self::button or self::a or self::div][1]")]
FILE_INPUT = [(By.CSS_SELECTOR, "input[type='file']")]
SUBMIT = [(By.XPATH, "//bdi[normalize-space(.)='Submit']/ancestor::*[self::button or self::span][1]")]

# ------------------🧠 HELPERS ------------------ #
def log(msg): print(msg, flush=True)

def wait_clear(driver, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        blocked = False
        try: blocked |= any(e.is_displayed() for e in driver.find_elements(*BLOCK_LAYER))
        except: pass
        try: blocked |= any(e.is_displayed() for e in driver.find_elements(*BUSY_DIALOG))
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
        except: continue
    raise TimeoutException(f"No selector matched: {locator_list}")

def safe_click(driver, el):
    try: el.click(); return True
    except (ElementClickInterceptedException, StaleElementReferenceException): pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.1); el.click(); return True
    except: pass
    try: driver.execute_script("arguments[0].click();", el); return True
    except: return False

# ------------------🚀 WORKFLOW ------------------ #
def goto_login(driver):
    log("[1] Opening login page…")
    driver.get(URL_LOGIN)
    u = find_any(driver, LOGIN_USER)
    p = find_any(driver, LOGIN_PASS)
    u.clear(); u.send_keys(USERNAME)
    p.clear(); p.send_keys(PASSWORD)
    btn = find_any(driver, LOGIN_BTN, clickable=True)
    safe_click(driver, btn)

def click_upload(driver):
    log("[2] Clicking Upload…")
    wait_clear(driver)
    up = find_any(driver, UPLOAD_HEADER, clickable=True)
    safe_click(driver, up)
    time.sleep(1)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        log("[2] Switched to new tab.")

def click_new(driver):
    log("[3] Clicking New…")
    for attempt in range(1, CLICK_NEW_RETRIES + 1):
        wait_clear(driver)
        try:
            newb = find_any(driver, NEW_BUTTON, timeout=30)
        except TimeoutException:
            log(f"  Attempt {attempt}: New not found… retrying")
            time.sleep(0.5); continue
        if not safe_click(driver, newb):
            log(f"  Attempt {attempt}: Click failed")
        time.sleep(1)
        try:
            _ = find_any(driver, FILE_INPUT, timeout=3)
            log("[3] New clicked; form visible.")
            return True
        except: continue
    raise TimeoutException("Upload form didn’t appear.")

def main():
    p = Path(FILE_PATH)
    if not p.exists():
        raise FileNotFoundError(f"❌ File not found: {p}")

    log("[0] Launching Chrome headless…")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    try:
        goto_login(driver)
        click_upload(driver)
        click_new(driver)

        log("[4] Typing comment…")
        cmt = find_any(driver, COMMENTS)
        cmt.clear(); cmt.send_keys(COMMENTS_TEXT)

        log("[5] Uploading file…")
        try:
            addbtn = find_any(driver, ADD_ATTACH, timeout=6, clickable=True)
            safe_click(driver, addbtn)
            time.sleep(0.3)
        except: pass
        finput = find_any(driver, FILE_INPUT)
        finput.send_keys(str(p.resolve()))

        log("[6] Submitting…")
        sub = find_any(driver, SUBMIT, clickable=True)
        safe_click(driver, sub)

        wait_clear(driver, 20)
        log("✅ Done. File uploaded successfully!")
    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    main()
