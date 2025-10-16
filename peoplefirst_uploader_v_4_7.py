import time
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Constants
FILE_PATH = "appeal_letter.pdf"  # Change this to your file path
COMMENTS_TEXT = "Uploading appeal letter as per request."
HEADLESS = False

# Selectors (update as needed)
LOGIN_USER = [
    (By.CSS_SELECTOR, "input[placeholder='Login ID']"),
    (By.ID, "userid"),
    (By.NAME, "userid"),
    (By.XPATH, "//input[@type='text' and (contains(@aria-label,'Login') or contains(@placeholder,'Login'))]")
]

LOGIN_PASS = [
    (By.ID, "password"),
    (By.NAME, "password"),
    (By.CSS_SELECTOR, "input[type='password']"),
    (By.XPATH, "//input[@type='password']")
]

COMMENTS = [
    (By.NAME, "comments"),
    (By.ID, "comments")
]

ADD_ATTACH = [
    (By.ID, "add_attachment"),
    (By.XPATH, "//button[contains(text(),'Add Attachment')]")
]

FILE_INPUT = [
    (By.CSS_SELECTOR, "input[type='file']")
]

SUBMIT = [
    (By.ID, "submit"),
    (By.XPATH, "//button[contains(text(),'Submit')]")
]

# Logging helper
def log(msg):
    print(msg)

# Element finder helper
def find_any(driver, locators, timeout=30, clickable=False):
    wait = WebDriverWait(driver, timeout)
    for by, value in locators:
        try:
            if clickable:
                return wait.until(EC.element_to_be_clickable((by, value)))
            else:
                return wait.until(EC.presence_of_element_located((by, value)))
        except Exception:
            continue
    raise TimeoutException(f"No selector matched: {locators}")

# Safe click helper
def safe_click(driver, el):
    driver.execute_script("arguments[0].click();", el)

# Load and wait for login

def wait_for_login_page(driver, timeout=180):
    log(f"[1] Waiting for PeopleFirst login form to load... (timeout={timeout}s)")
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
    except Exception:
        Path("error_debug.html").write_text(driver.page_source)
        driver.save_screenshot("error_debug.png")
        raise TimeoutException("Login form did not appear in time.")

def goto_login(driver):
    log("[1] Opening login page...")
    driver.get("https://peoplefirst.myflorida.com/peoplefirst/index.html")
    wait_for_login_page(driver)
    log("[1] Typing credentials…")
    u = find_any(driver, LOGIN_USER)
    u.send_keys("YOUR_USERNAME")  # Replace with actual username
    p = find_any(driver, LOGIN_PASS)
    p.send_keys("YOUR_PASSWORD")  # Replace with actual password
    p.submit()

def click_upload(driver):
    pass  # TODO: Add logic for navigating to upload section

def click_new(driver):
    pass  # TODO: Add logic for clicking "New Document" or similar

def force_select_appeal_letter(driver):
    pass  # TODO: Logic to select document type as "Appeal Letter"

# Main function
def main():
    p = Path(FILE_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {p}")

    log("[0] Launching Chrome...")
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    if HEADLESS:
        opts.add_argument("--headless=new")

    with tempfile.TemporaryDirectory() as tmpdirname:
        log(f"\U0001f9ea Using temporary Chrome profile: {tmpdirname}")
        opts.add_argument(f"--user-data-dir={tmpdirname}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

        try:
            goto_login(driver)
            click_upload(driver)
            click_new(driver)

            # Select doc type
            force_select_appeal_letter(driver)
            time.sleep(0.3)

            # Comments
            log("[5] Typing comments…")
            cmt = find_any(driver, COMMENTS, timeout=25)
            try: cmt.clear()
            except: pass
            cmt.send_keys(COMMENTS_TEXT)

            # Attach file
            log("[6] Attaching file…")
            try:
                addbtn = find_any(driver, ADD_ATTACH, timeout=6, clickable=True)
                safe_click(driver, addbtn)
                time.sleep(0.3)
            except:
                pass

            finput = find_any(driver, FILE_INPUT, timeout=25)
            finput.send_keys(str(p.resolve()))

            # Submit
            log("[7] Submitting…")
            sub = find_any(driver, SUBMIT, timeout=25, clickable=True)
            safe_click(driver, sub)

            log("✅ Done.")
        finally:
            time.sleep(2)
            driver.quit()

if __name__ == "__main__":
    main()
