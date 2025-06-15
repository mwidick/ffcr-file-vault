
import os
import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

USERNAME = "mwidick"
PASSWORD = "Nosethroat25!"
MRN = "1595525"
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_DIR = os.path.join(f"output_{timestamp}_MRN{MRN}")
os.makedirs(OUTPUT_DIR, exist_ok=True)
LOGFILE = os.path.join(OUTPUT_DIR, f"log_{timestamp}_MRN{MRN}.txt")
VISIT_DIR = "visit_activity"
os.makedirs(VISIT_DIR, exist_ok=True)

def log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    entry = f"[{t}] {msg}"
    print(entry)
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": os.path.abspath(VISIT_DIR),
    "plugins.always_open_pdf_externally": True
}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)
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
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ng-select-container div.ng-input")))
    log("Main app loaded.")

    driver.get("https://entaaf.ema.md/ema/web/practice/staff#/practice/staff/patient/list")
    combo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ng-select-container div.ng-input")))
    combo.click()
    time.sleep(2)
    inp = combo.find_element(By.TAG_NAME, "input")
    inp.clear()
    inp.send_keys(MRN)
    time.sleep(2)
    inp.send_keys(Keys.ENTER)
    log(f"MRN search for {MRN} triggered.")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))).click()
    log("Patient selected from list.")

    visits = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.po-visit-date")))
    log(f"Found {len(visits)} visit tabs.")

    for i, visit in enumerate(visits[:4]):
        visits = driver.find_elements(By.CSS_SELECTOR, "a.po-visit-date")
        visit = visits[i]
        visit_date = visit.text.strip().replace(" ", "-")
        safe_date = re.sub(r'[^\x00-\x7F]+', '_', visit_date)
        driver.execute_script("arguments[0].click();", visit)
        log(f"Clicked visit tab: {visit_date}")
        time.sleep(4)

        try:
            wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Download Visit Note as PDF")))
            pdf_link = driver.find_element(By.LINK_TEXT, "Download Visit Note as PDF")
            href = pdf_link.get_attribute("href")
            full_url = href
            log(f"Download link found: {full_url}")
            r = requests.get(full_url)
            filepath = os.path.join(VISIT_DIR, f"{MRN}_{safe_date}.pdf")
            with open(filepath, "wb") as f:
                f.write(r.content)
            log(f"PDF downloaded: {filepath}")
        except Exception as e:
            log(f"[ERROR] Download failed for visit {visit_date}: {e}")

        time.sleep(20)
        driver.back()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.po-visit-date")))
        time.sleep(2)

except Exception as e:
    log(f"[FATAL ERROR] {e}")
finally:
    driver.quit()
    log("Browser closed.")
