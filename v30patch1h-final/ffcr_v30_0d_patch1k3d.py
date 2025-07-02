
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
