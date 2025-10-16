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

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        opts.add_argument(f"--user-data-dir={tmpdirname}")
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
