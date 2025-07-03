
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pandas as pd
from selenium.webdriver.support.ui import Select

USERNAME = "mwidick"
PASSWORD = "Nosethroat25!"
EXCEL_FILE = "mrn_input.xlsx"
VISIT_DIR = "visit_activity"
os.makedirs(VISIT_DIR, exist_ok=True)

def log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    entry = f"[{t}] {msg}"
    print(entry)
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def load_mrns():
    df = pd.read_excel(EXCEL_FILE)
    return df.iloc[:, 0].astype(str).tolist()

def setup_driver():
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.path.abspath(VISIT_DIR),
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=options)

def main():
    mrns = load_mrns()
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)

    try:
        driver.get("https://entaaf.ema.md/ema/Login.action")
        log("Navigated to login page.")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit" and contains(@value, "Practice Staff")]'))).click()
        log("Clicked Practice Staff.")
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(USERNAME)
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()
        log("Submitted credentials.")
        wait.until(EC.presence_of_element_located((By.ID, "patientsMenuNavTab")))
        log("Main app loaded.")

        for mrn in mrns:
            log(f"Processing MRN: {mrn}")
            driver.get("https://entaaf.ema.md/ema/web/practice/staff#/practice/staff/patient/list")
            combo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ng-select-container div.ng-input")))
            combo.click()
            time.sleep(2)
            inp = combo.find_element(By.TAG_NAME, "input")
            inp.clear()
            inp.send_keys(mrn)
            time.sleep(2)
            inp.send_keys(Keys.ENTER)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))).click()
            log("Patient selected from list.")

            # === Begin Pagination Override (merged from pagination script) ===
            try:
                time.sleep(2)
                selects = driver.find_elements(By.TAG_NAME, "select")
                for sel in selects:
                    if "pagination-select" in sel.get_attribute("class") and sel.is_displayed():
                        sel.click()
                        dropdown = Select(sel)
                        options = [opt.text.strip() for opt in dropdown.options]
                        log(f"[Pagination] Options found: {options}")
                        if '100' in options:
                            dropdown.select_by_visible_text('100')
                            log("[Pagination] Set to 100 per page.")
                            time.sleep(3)
                        else:
                            log("[Pagination] '100' not available.")
                        break
                else:
                    log("[Pagination] No matching visible pagination-select dropdown found.")
            except Exception as e:
                log(f"[Pagination ERROR] Failed to set pagination: {e}")
            # === End Pagination Override ===

            visits = driver.find_elements(By.CSS_SELECTOR, "a.po-visit-date")
            log(f"Found {len(visits)} visit tabs.")

            for i in range(len(visits)):
                visit_list = driver.find_elements(By.CSS_SELECTOR, "a.po-visit-date")
                if i >= len(visit_list):
                    log(f"[WARNING] Visit index {i} no longer valid. Skipping.")
                    continue
                visit = visit_list[i]
                visit_date = visit.text.strip().replace(" ", "-")
                safe_date = re.sub(r'[^\x00-\x7F]+', '_', visit_date)
                driver.execute_script("arguments[0].click();", visit)
                log(f"Clicked visit tab: {visit_date}")
                time.sleep(4)

                try:
                    download_button = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Download Visit Note as PDF")))
                    driver.execute_script("arguments[0].click();", download_button)
                    log(f"Triggered PDF download for visit: {visit_date}")
                    time.sleep(8)
                except Exception as e:
                    log(f"[ERROR] Download click failed for visit {visit_date}: {e}")

                driver.back()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.po-visit-date")))
                time.sleep(2)
                try:
                    dropdown_elements = driver.find_elements(By.CSS_SELECTOR, "select.pagination-select")
                    for dropdown_element in dropdown_elements:
                        if dropdown_element.is_displayed():
                            dropdown_element.click()
                            dropdown = Select(dropdown_element)
                            options = [opt.text.strip() for opt in dropdown.options]
                            if '100' in options:
                                dropdown.select_by_visible_text('100')
                                log("[Pagination] Reasserted 100 per page after return (visible dropdown only).")
                                time.sleep(2)
                                break
                except Exception as e:
                    log(f"[Pagination ERROR] Failed to reassert after return: {e}")

    except Exception as e:
        log(f"[FATAL ERROR] {e}")
    finally:
        driver.quit()
        log("Browser closed.")

if __name__ == "__main__":
    main()

# === Begin Attachments Module ===

import os
import time
import traceback
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================== SETUP & INITIALIZATION ====================

BASE_DIR = "./visit_activity"
SCREENSHOT_DIR = "./screenshots"
LOG_PATH = "v13_0i_run_log.txt"
CHROMEDRIVER_PATH = r"C:\FFCR_Project\Pair E\chromedriver-win64\chromedriver.exe"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

with open(LOG_PATH, "w") as log:
    def log_msg(msg):
        print(msg)
        log.write(f"{datetime.now().isoformat()} - {msg}\n")

    log_msg("===== HDMI Diagnostics v11.3f Start =====")
    log_msg("Refer to FFCR_HDMI_Video_Metadata.txt for HDMI session metadata.")

    try:
        mrns = ["MM0000333560"]
        log_msg(f"Loaded {len(mrns)} MRNs (hardcoded).")

        options = webdriver.ChromeOptions()
        options.binary_location = r"C:\FFCR_Project\Pair E\chrome-win64\chrome.exe"
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

        browser_version = driver.capabilities.get("browserVersion", "")
        if not browser_version.startswith("135"):
            print(f"[WARN] Chrome version is {browser_version}, not 135.x. Proceeding anyway...")

        # ==================== LOGIN LOGIC ====================
        def login():
            driver.get("https://entaaf.ema.md/ema/Login.action")
            wait.until(EC.element_to_be_clickable((By.XPATH, '//input[contains(@value,"Practice Staff")]'))).click()
            wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("mwidick")
            wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys("Nosethroat25!")
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()

        # ==================== PATIENT LOOKUP ====================
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

        # ==================== ATTACHMENTS EXTRACTION ====================
        def download_fax_attachments(mrn):
            try:
                driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{mrn}_attachments_tab.png"))
                log_msg("Clicking Attachments tab...")
                attachments_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.nav-tab.ngx-nav-tab[data-identifier="attachments-tab"]')))
                attachments_tab.click()
                log_msg("Attachments tab clicked.")
                time.sleep(5)

                cookies = driver.get_cookies()
                session = requests.Session()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'])

                found = False
                links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ema/secure/fileattachment/"]')
                for link in links:
                    text = link.text.strip().lower()
                    if "fax" in text:
                        href = link.get_attribute("href")
                        filename = href.split("/")[-1].split("?")[0]
                        log_msg(f"Downloading via requests: {filename}")
                        response = session.get(href)
                        if response.ok:
                            filepath = os.path.join(BASE_DIR, filename)
                            with open(filepath, "wb") as f:
                                f.write(response.content)
                        else:
                            log_msg(f"[ERROR] Failed to download {filename}, status: {response.status_code}")
                        time.sleep(1)
                        found = True

                if not found:
                    log_msg(f"[INFO] No 'fax' attachments found for MRN {mrn}.")
            except Exception as e:
                log_msg(f"[ERROR] Attachment scan failed for MRN {mrn}: {e}")

        # ==================== PATIENT ACTIVITY ADD-ON (Toggleable) ====================
        ENABLE_PATIENT_ACTIVITY = True

        def extract_patient_activity(driver):
            print("[ADD-ON] Beginning Patient Activity extraction...")
            page = 1
            while True:
                print(f"[Page {page}] Scanning for visit PDFs...")
                pdf_links = []
                if not pdf_links:
                    print("[Info] No PDFs found on this page.")
                else:
                    for i, link in enumerate(pdf_links):
                        print(f"[Download] Visit PDF {i+1} on page {page}")
                has_next_page = False
                if has_next_page:
                    print("[Action] Moving to next page...")
                    page += 1
                else:
                    print("[Complete] No more pages in Patient Activity.")
                    break

        # ==================== EXECUTION ====================
        login()
        for mrn in mrns:
            log_msg(f"Processing MRN: {mrn}")
            extract_patient_data(mrn)
            download_fax_attachments(mrn)
            if ENABLE_PATIENT_ACTIVITY:
                extract_patient_activity(driver)

        driver.quit()
        log_msg("Browser session closed.")

    except Exception as main_e:
        log_msg(f"Fatal error: {main_e}")
    finally:
        log_msg("===== HDMI Diagnostics v11.3f End =====")
# === End Attachments Module ===
