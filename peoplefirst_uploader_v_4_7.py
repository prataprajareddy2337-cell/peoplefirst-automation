#!/usr/bin/env python3
# PeopleFirst uploader — v5.0 (Headless + Hardcoded Credentials)
# - Uses headless Chrome for GitHub Actions
# - Credentials are hardcoded
# - Works with cron + workflow_dispatch

from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# 🧾 Hardcoded credentials (your choice!)
USERNAME = "2034844"
PASSWORD = "Prataprajareddy@2338"

URL_LOGIN = "https://peoplefirst.myflorida.com/peoplefirst/index.html"
COMMENTS_TEXT = "People First website has some issues. It has selected all the benefits without me selecting them for the new hire benefits."
FILE_PATH = r"C:\Users\prata\Downloads\AppealLetter.docx"

HEADLESS = True
CLICK_NEW_RETRIES = 10

# Locators
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

def log(msg): print(msg, flush=True)

def wait_clear(driver, timeout=60):
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
    try: el.click(); return True
    except (ElementClickInterceptedException, StaleElementReferenceException): pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.1); el.click(); return True
    except Exception: pass
    try:
        driver.execute_script("arguments[0].click();", el); return True
    except Exception: return False

def goto_login(driver):
    log("[1] Logging in…")
    driver.get(URL_LOGIN)
    u = find_any(driver, LOGIN_USER)
    p = find_any(driver, LOGIN_PASS)
    u.clear(); u.send_keys(USERNAME)
    p.clear(); p.send_keys(PASSWORD)
    btn = find_any(driver, LOGIN_BTN, clickable=T
