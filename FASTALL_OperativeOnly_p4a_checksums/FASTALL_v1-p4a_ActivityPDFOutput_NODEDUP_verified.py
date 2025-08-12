
import os
import time
import traceback
import requests
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== CONFIG ==========
BASE_DIR = "./Activity_PDF_Output"
SCREENSHOT_DIR = "./screenshots"
LOG_PATH = "modmed_patch4_run_log.txt"
CHROMEDRIVER_PATH = r"C:\FFCR_Project\Pair E\chromedriver-win64\chromedriver.exe"
CREDENTIAL_FILE = "counselear_credentials.xlsx"
PATIENT_FILE = "counselear_patients.xlsx"
OP_KEYWORDS = []

# ========== SETUP ==========
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

print("=== FASTALL v1-p4a NODEDUP Activity_PDF_Output ===")
print(f"OUTPUT_ROOT={BASE_DIR}")

with open(LOG_PATH, "w") as log:
    def log_msg(msg):
        print(msg)
        log.write(f"{datetime.now().isoformat()} - {msg}\n")

    log_msg("===== FFCR ModMed v1b_patch4 Start =====")

    try:
        # Load credentials and MRNs
        creds = pd.read_excel(CREDENTIAL_FILE)
        username = creds.iloc[0]["username"]
        password = creds.iloc[0]["password"]
        mrns = pd.read_excel(PATIENT_FILE).iloc[:, 0].tolist()

        log_msg(f"Loaded {len(mrns)} MRNs from Excel.")

        # Chrome setup
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

        # ========== LOGIN ==========
        def login():
            driver.get("https://entaaf.ema.md/ema/Login.action")
            wait.until(EC.element_to_be_clickable((By.XPATH, '//input[contains(@value,"Practice Staff")]'))).click()
            wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
            wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()

        # ========== LOOKUP + DOWNLOAD ==========
        def dismiss_modal():
            try:
                modal = driver.find_element(By.CSS_SELECTOR, 'modal-container[role="dialog"]')
                driver.execute_script("arguments[0].remove();", modal)
                log_msg("[~] Modal dismissed.")
            except:
                pass

        def open_patient(mrn):
            driver.get("https://entaaf.ema.md/ema/web/practice/staff#/practice/staff/patient/list")
            combo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ng-select-container div.ng-input")))
            dismiss_modal()
            combo.click()
            time.sleep(1)
            inp = combo.find_element(By.TAG_NAME, "input")
            inp.clear()
            inp.send_keys(mrn)
            time.sleep(1)
            inp.send_keys(u'\ue007')
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))).click()
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.po-visit-date")))

        def extract_pdfs_from_attachments(mrn):
            try:
                driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{mrn}_attachments_tab.png"))
                log_msg(f"[{mrn}] Clicking Attachments tab...")
                attachments_tab = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'div.nav-tab.ngx-nav-tab[data-identifier="attachments-tab"]')))
                attachments_tab.click()
                time.sleep(5)

                cookies = driver.get_cookies()
                session = requests.Session()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'])

                pdf_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/ema/secure/fileattachment/"]')
                saved = 0
                for link in pdf_links:
                    href = link.get_attribute("href")
                    filename = href.split("/")[-1].split("?")[0]
                    if href and ".pdf" in href.lower():
                        log_msg(f"[{mrn}] Downloading PDF: {filename}")
                        response = session.get(href)
                        if response.ok:
                            mrn_dir = os.path.join(BASE_DIR, mrn)
                            os.makedirs(mrn_dir, exist_ok=True)
                            from hashlib import sha256
                            # write to temp then dedupe
                            tmp_path = os.path.join(mrn_dir, "__tmp__"+filename)
                            with open(tmp_path, "wb") as f:
                                f.write(response.content)
                            # hash
                            h=sha256()
                            with open(tmp_path,"rb") as fh:
                                for chunk in iter(lambda: fh.read(8192), b""):
                                    h.update(chunk)
                            digest = h.hexdigest()
                            # ledger
                            ledger = os.path.join(mrn_dir, "_digests.txt")
                            seen = set()
                            if os.path.exists(ledger):
                                with open(ledger,"r",encoding="utf-8") as lf:
                                    seen = set(x.strip() for x in lf if x.strip())
                            if digest in seen:
                                os.remove(tmp_path)
                                log_msg(f"[{mrn}] Duplicate skipped ({digest[:8]}...)")
                            else:
                                # finalize unique filename
                                final = os.path.join(mrn_dir, filename)
                                base,ext = os.path.splitext(final)
                                i=2
                                while os.path.exists(final):
                                    final = f"{base} ({i}){ext}"
                                    i+=1
                                os.replace(tmp_path, final)
                                with open(ledger,"a",encoding="utf-8") as lf:
                                    lf.write(digest+"\n")
                                saved += 1
                        else:
                            log_msg(f"[{mrn}] Failed to download {filename} (status {response.status_code})")
                        time.sleep(1)

                if saved == 0:
                    log_msg(f"[{mrn}] No operative PDFs found.")
                else:
                    log_msg(f"[{mrn}] Saved {saved} operative PDFs.")

            except Exception as e:
                log_msg(f"[{mrn}] Error during PDF extraction: {e}")

        # Run
        login()
        for mrn in mrns:
            log_msg(f"Processing MRN: {mrn}")
            open_patient(mrn)
            extract_pdfs_from_attachments(mrn)

        driver.quit()
        log_msg("===== FFCR ModMed v1b_patch4 Finished =====")

    except Exception as e:
        log_msg(f"[FATAL ERROR] {e}")
