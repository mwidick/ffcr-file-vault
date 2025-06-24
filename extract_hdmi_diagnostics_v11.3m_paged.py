# extract_hdmi_diagnostics_v11.3a.py

import os
import time
import re
import traceback
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess

# === CONFIGURATION ===
EXCEL_PATH = "Dr. Widick - 69631-69633 without namesforchat.xlsx"
BASE_DIR = "./visit_activity"
SCREENSHOT_DIR = "./screenshots"
LOG_PATH = "v11.3a_run_log.txt"
CHROMEDRIVER_PATH = r"C:\FFCR_Project\chromedriver.exe"
KEYWORDS = ["operative", "surgery", "tympano", "op report"]

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# === START LOGGING ===
with open(LOG_PATH, "w") as log:
    def log_msg(msg):
        print(msg)
        log.write(f"{datetime.now().isoformat()} - {msg}\n")

    log_msg("===== HDMI Diagnostics v11.3a Start =====")

    try:
        # Load MRNs
        df = pd.read_excel(EXCEL_PATH, skiprows=4, usecols="B")
        mrns = df.iloc[::-1, 0].dropna().astype(str).unique().tolist()[:4]
        log_msg(f"Loaded {len(mrns)} MRNs (limited to 4).")

        # Setup browser
        options = webdriver.ChromeOptions()
        options.binary_location = r"C:\chrome-win64\chrome.exe"
        prefs = {
            "download.default_directory": os.path.abspath(BASE_DIR),
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False
        }
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--start-maximized")
        options.add_argument("--incognito")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
        wait = WebDriverWait(driver, 20)

        def login():
            driver.get("https://entaaf.ema.md/ema/Login.action")
            wait.until(EC.element_to_be_clickable((By.XPATH, '//input[contains(@value,"Practice Staff")]'))).click()
            wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("mwidick")
            wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys("Nosethroat25!")
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()

        def extract_patient_data(mrn):
            driver.get("https://entaaf.ema.md/ema/web/practice/staff#/practice/staff/patient/list")
            combo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ng-select-container div.ng-input")))
            combo.click()
            time.sleep(1)
            inp = combo.find_element(By.TAG_NAME, "input")
            inp.clear()
            inp.send_keys(mrn)
            time.sleep(1)
            inp.send_keys(u'\ue007')
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))).click()
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.po-visit-date")))

        def download_hdmi_op_reports(mrn):
            try:
                driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{mrn}_before_tab.png"))
                attachments_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-identifier="attachments-tab"]')))
                attachments_tab.click()
                time.sleep(5)
                match_found = False
                while True:
                    rows = driver.find_elements(By.CSS_SELECTOR, "tr")
                    for row in rows:
                        try:
                            text = row.text.lower()
                            if any(k in text for k in KEYWORDS):
                                date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
                                if date_match:
                                    date_obj = datetime.strptime(date_match.group(1), "%m/%d/%Y")
                                    if date_obj >= datetime(2017, 1, 1):
                                        link = row.find_element(By.TAG_NAME, "a")
                                        driver.execute_script("window.open(arguments[0]);", link.get_attribute("href"))
                                        time.sleep(2)
                                        match_found = True
                        except:
                            continue
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]:not([disabled])')
                        driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(2)
                    except:
                        break
                if not match_found:
                    log_msg(f"No qualifying attachments found for MRN {mrn}.")
            except Exception as e:
                log_msg(f"Error for MRN {mrn}: {e}")
                driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{mrn}_error.png"))

        login()
        for mrn in mrns:
            log_msg(f"Processing MRN: {mrn}")
            extract_patient_data(mrn)
            download_hdmi_op_reports(mrn)

        driver.quit()
        log_msg("Browser session closed.")

        # === Launch FFCR Parser ===
        try:
            log_msg("Launching FFCR parser...")
            subprocess.run(["python", "run_ffcr_v8.7c_hdrive.py"], check=True, cwd=os.getcwd())
            log_msg("FFCR parser complete.")
        except Exception as pe:
            log_msg(f"FFCR parser failed: {pe}")

        # === Email Snapshot ===
        try:
            log_msg("Sending FFCR snapshot email...")
            subprocess.run(["python", "send_ffcr_snapshot_email.py"], check=True)
            log_msg("Email sent successfully.")
        except Exception as ee:
            log_msg(f"Email send failed: {ee}")

    except Exception as main_e:
        log_msg(f"Fatal error: {main_e}")
    finally:
        log_msg("===== HDMI Diagnostics v11.3a End =====")


def extract_all_pages(driver, item_selector, next_button_selector, process_fn):
    """Navigates through paginated data and applies a processing function on each page.

    Args:
        driver (WebDriver): The Selenium browser instance.
        item_selector (str): CSS/XPath selector for the rows or items to extract.
        next_button_selector (str): CSS/XPath selector for the 'Next' page button.
        process_fn (Callable): Function to run on each item.

    Returns:
        List[Any]: Aggregated data from all pages.
    """
    results = []
    while True:
        try:
            items = driver.find_elements(By.CSS_SELECTOR, item_selector)
            for item in items:
                try:
                    results.append(process_fn(item))
                except Exception as item_error:
                    print(f"[!] Error processing item: {item_error}")
            next_btn = driver.find_element(By.CSS_SELECTOR, next_button_selector)
            if "disabled" in next_btn.get_attribute("class") or not next_btn.is_displayed():
                break
            next_btn.click()
            time.sleep(2)  # Wait for the page transition
        except Exception as pagination_error:
            print(f"[!] Pagination error or last page reached: {pagination_error}")
            break
    return results
