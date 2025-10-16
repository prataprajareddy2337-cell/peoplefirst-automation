#!/usr/bin/env python3
# PeopleFirst uploader — v4.7 (extra logging)
# - Hard-coded credentials (as requested)
# - Safe “Upload → New” clicks with overlay waits
# - Forces Document Type to “APPEAL LETTER” using native <select> OR SAP UI5 API (no dropdown popups needed)
# - Clear step-by-step prints so you see where it is

from pathlib import Path
import time, sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

URL_LOGIN = "https://peoplefirst.myflorida.com/peoplefirst/index.html"
USERNAME = "2034844"
PASSWORD = "Prataprajareddy@2338"

COMMENTS_TEXT = "People First website has some issues. It has selected all the benefits without me selecting them for the new hire benefits."
FILE_PATH = r"AppealLetter.docx"

HEADLESS = False
CLICK_NEW_RETRIES = 10

# Locators
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
ADD_ATTACH = [(By.XPATH, "//*[contains(., 'Add attachments')]/ancestor::*[self::button or self::a or self::div][1]")]
FILE_INPUT = [(By.CSS_SELECTOR, "input[type='file']"), (By.XPATH, "//input[@type='file']")]
SUBMIT = [
    (By.XPATH, "//bdi[normalize-space(.)='Submit']/ancestor::*[self::button or self::span][1]"),
    (By.XPATH, "//button[.//bdi[normalize-space(.)='Submit'] or normalize-space(.)='Submit']"),
]

def log(msg):
    print(msg, flush=True)

def wait_clear(driver, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        blocked = False
        try:
            if any(e.is_displayed() for e in driver.find_elements(*BLOCK_LAYER)):
                blocked = True
        except Exception:
            pass
        try:
            if any(e.is_displayed() for e in driver.find_elements(*BUSY_DIALOG)):
                blocked = True
        except Exception:
            pass
        if not blocked:
            return True
        time.sleep(0.2)
    return False

def find_any(driver, locator_list, timeout=25, clickable=False):
    last_err = None
    for by, sel in locator_list:
        try:
            if clickable:
                WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
            else:
                WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, sel)))
            return driver.find_element(by, sel)
        except Exception as e:
            last_err = e
            continue
    raise TimeoutException(f"No selector matched: {locator_list}") from last_err

def safe_click(driver, el):
    try:
        el.click(); return True
    except (ElementClickInterceptedException, StaleElementReferenceException):
        pass
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
        time.sleep(0.1); el.click(); return True
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].click();", el); return True
    except Exception:
        return False

def goto_login(driver):
    log("[1] Opening login page…")
    driver.get(URL_LOGIN)
    log("[1] Finding username & password fields…")
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
    log("[3] Clicking New (with retries while overlays appear/disappear)…")
    for attempt in range(1, CLICK_NEW_RETRIES + 1):
        wait_clear(driver, 30)
        try:
            newb = find_any(driver, NEW_BUTTON, timeout=30)
        except TimeoutException:
            log(f"    attempt {attempt}: New not found, retrying…"); time.sleep(0.5); continue
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", newb)
        time.sleep(0.05)
        if not safe_click(driver, newb):
            log(f"    attempt {attempt}: click failed, retrying…")
        time.sleep(0.8)
        # Form hint: file input present?
        try:
            _ = find_any(driver, FILE_INPUT, timeout=3)
            log("[3] New clicked; form visible.")
            return True
        except Exception:
            log(f"    attempt {attempt}: form not visible yet.")
            continue
    raise TimeoutException("Form did not appear after clicking New.")

def force_select_appeal_letter(driver):
    """
    Select 'APPEAL LETTER' via:
      1) native <select> by text or 2nd index
      2) SAP UI5 control API by text or 2nd item
    """
    log("[4] Forcing Document Type = 'APPEAL LETTER' (native/UI5)…")
    js = r"""
    (function () {
      const WANT = "APPEAL LETTER";

      // (1) Native <select>
      try {
        const selects = document.querySelectorAll("select");
        for (const s of selects) {
          for (let i = 0; i < s.options.length; i++) {
            const txt = (s.options[i].text || "").trim().toUpperCase();
            if (txt === WANT) {
              s.selectedIndex = i;
              s.dispatchEvent(new Event("change", { bubbles: true }));
              return "native-select-by-text";
            }
          }
          if (s.options && s.options.length >= 2) {
            s.selectedIndex = 1;
            s.dispatchEvent(new Event("change", { bubbles: true }));
            return "native-select-by-index";
          }
        }
      } catch (e) {}

      // (2) SAP UI5 control API
      try {
        if (window.sap && sap.ui && sap.ui.getCore) {
          let input = document.querySelector("input[id$='doctypeCombo-inner'], input[aria-label='Document Type']");
          if (!input) {
            const label = Array.from(document.querySelectorAll("label"))
              .find(l => (l.textContent || "").trim().toLowerCase() === "document type");
            if (label) {
              input = label.parentElement && label.parentElement.querySelector("input[role='combobox'], input.sapMComboBoxBaseInput");
            }
          }
          if (input) {
            let baseId = input.id ? input.id.replace(/-inner$/, "").replace(/-input$/, "") : null;
            let ctrl = baseId ? sap.ui.getCore().byId(baseId) : null;
            if (!ctrl) {
              const cont = input.closest("[data-sap-ui], [id]");
              if (cont && cont.id) ctrl = sap.ui.getCore().byId(cont.id);
            }
            if (ctrl && (ctrl.getItems || ctrl.getItemAt)) {
              const items = ctrl.getItems ? ctrl.getItems() : [];
              for (let i = 0; i < items.length; i++) {
                const it = items[i];
                const t = (it.getText ? it.getText() : (it.mProperties && it.mProperties.text) || "").trim().toUpperCase();
                if (t === WANT) {
                  if (ctrl.setSelectedItem) ctrl.setSelectedItem(it);
                  if (ctrl.setSelectedKey && it.getKey) ctrl.setSelectedKey(it.getKey());
                  if (ctrl.fireChange) ctrl.fireChange({ selectedItem: it });
                  if (ctrl.fireSelectionChange) ctrl.fireSelectionChange({ selectedItem: it });
                  if (ctrl.rerender) ctrl.rerender();
                  return "ui5-combobox-by-text";
                }
              }
              if (items.length >= 2) {
                const it = items[1];
                if (ctrl.setSelectedItem) ctrl.setSelectedItem(it);
                if (ctrl.setSelectedKey && it.getKey) ctrl.setSelectedKey(it.getKey());
                if (ctrl.fireChange) ctrl.fireChange({ selectedItem: it });
                if (ctrl.fireSelectionChange) ctrl.fireSelectionChange({ selectedItem: it });
                if (ctrl.rerender) ctrl.rerender();
                return "ui5-combobox-by-index";
              }
            }
          }
        }
      } catch (e) {}

      return "not-found";
    })();
    """
    result = driver.execute_script(js)
    log(f"[4] Doc-Type mode: {result}")
    if result == "not-found":
      raise TimeoutException("Could not set Document Type via native/select or UI5 control.")
    return result

def main():
    # quick preflight on file path
    p = Path(FILE_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {p}")

    log("[0] Launching Chrome…")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    if HEADLESS:
        opts.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    try:
        goto_login(driver)
        click_upload(driver)
        click_new(driver)

        # Document Type
        force_select_appeal_letter(driver)
        time.sleep(0.3)

        # Comments
        log("[5] Typing comments…")
        cmt = find_any(driver, COMMENTS, timeout=25)
        try:
            cmt.clear()
        except Exception:
            pass
        cmt.send_keys(COMMENTS_TEXT)

        # Attachment
        log("[6] Attaching file…")
        try:
            addbtn = find_any(driver, ADD_ATTACH, timeout=6, clickable=True)
            safe_click(driver, addbtn)
            time.sleep(0.3)
        except Exception:
            pass
        finput = find_any(driver, FILE_INPUT, timeout=25)
        finput.send_keys(str(p.resolve()))

        # Submit
        log("[7] Submitting…")
        sub = find_any(driver, SUBMIT, timeout=25, clickable=True)
        safe_click(driver, sub)

        wait_clear(driver, 25)
        log("✅ Done.")
    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    main()

