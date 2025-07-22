
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import openpyxl
from datetime import datetime

def extract_audiometry_data(driver):
    """Extracts all audiometric thresholds from the Test Results table."""
    results = []
    try:
        print("[DEBUG] Locating 'Test Results' anchor...")
        anchor = driver.find_element(By.XPATH, "//strong[contains(text(), 'Test Results')]")
        print("[DEBUG] Anchor found ✓")

        table = anchor.find_element(By.XPATH, "following-sibling::table[contains(@class, 'formTable')]")
        rows = table.find_elements(By.TAG_NAME, "tr")
        print(f"[DEBUG] Table rows found: {len(rows)}")
        if len(rows) < 2:
            print("[DEBUG] Table has no data rows.")
            return []

        for row_index, row in enumerate(rows[1:], start=1):
            data_cells = row.find_elements(By.TAG_NAME, "td")
            if len(data_cells) < 11:
                print(f"[DEBUG] Row {row_index} skipped due to insufficient data.")
                continue

            test_date = data_cells[0].text.strip()
            values = []
            for i, cell in enumerate(data_cells[1:11]):
                text = cell.text.replace("\n", "").strip()
                if not text:
                    spans = cell.find_elements(By.TAG_NAME, "span")
                    text = " / ".join([s.text.strip() for s in spans if s.text.strip()])
                print(f"[DEBUG] Row {row_index}, Cell {i+1}: '{text}'")
                if "/" in text:
                    parts = [p.strip() for p in text.split("/")[:2]]
                    values.extend(parts if len(parts) == 2 else parts + [""])
                elif text:
                    values.append(text)
                    values.append("")
                else:
                    values.extend(["", ""])
            if len(values) < 20:
                values += [""] * (20 - len(values))
            ac_r = values[0::2]
            ac_l = values[1::2]
            bc_r = ["" for _ in ac_r]
            bc_l = ["" for _ in ac_l]
            results.append((test_date, ac_r, ac_l, bc_r, bc_l))
        return results
    except Exception as e:
        print(f"[EXTRACT ERROR - MULTIROW] {e}")
        return []

def save_to_excel(mrn, test_date, air_r, air_l, bone_r, bone_l):
    hz_list = [250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000]
    cols = ["MRN", "Test Date"] + [f"AC R {hz}" for hz in hz_list] + [f"AC L {hz}" for hz in hz_list] + [f"BC R {hz}" for hz in hz_list] + [f"BC L {hz}" for hz in hz_list]
    data = [[mrn, test_date] + air_r + air_l + bone_r + bone_l]
    df = pd.DataFrame(data, columns=cols)
    out_path = os.path.join("CounselEar Downloads", "audiometry_data.xlsx")
    os.makedirs("CounselEar Downloads", exist_ok=True)
    if os.path.exists(out_path):
        existing = pd.read_excel(out_path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(out_path, index=False)

def log_message(logfile, message):
    print(message)
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def main():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "log_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt")

    creds = pd.read_excel("counselear_credentials.xlsx")
    username, password = creds.loc[0, "username"], creds.loc[0, "password"]
    chrome_options = Options()
    chrome_options.binary_location = "C:/FFCR_Project/Pair E/chrome-win64/chrome.exe"
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.abspath("visit_activity"),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })
    driver = webdriver.Chrome(service=Service("C:/FFCR_Project/Pair E/chromedriver-win64/chromedriver.exe"), options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://counselear.com")
        wait.until(EC.element_to_be_clickable((By.ID, "lnkLogin"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "txtEmailAddress"))).send_keys(username)
        driver.find_element(By.ID, "btnStep1").click()
        wait.until(EC.presence_of_element_located((By.ID, "txtPassword"))).send_keys(password)
        driver.find_element(By.ID, "btnStep2").click()
        wait.until(EC.presence_of_element_located((By.ID, "header_secureTopMenu_lookup_txtLookup")))

        df = pd.read_excel("counselear_patients.xlsx")
        patients = df["patient_name"].dropna().drop_duplicates().tolist()

        for patient in patients:
            try:
                sb = wait.until(EC.presence_of_element_located((By.ID, "header_secureTopMenu_lookup_txtLookup")))
                sb.clear()
                sb.send_keys(str(patient))
                sb.send_keys(Keys.RETURN)
                time.sleep(3)
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".rgRow, .rgAltRow"))).click()
                time.sleep(3)
                try:
                    info_btn = wait.until(EC.element_to_be_clickable((By.ID, "ctl01_ctlPatientSummary_imgPatientInfo")))
                    info_btn.click()
                    time.sleep(3)
                    ss_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CounselEar Downloads")
                    os.makedirs(ss_dir, exist_ok=True)
                    fname = f"{str(patient).replace(' ', '_')}_UNKNOWN.png"
                    driver.save_screenshot(os.path.join(ss_dir, fname))
                    results = extract_audiometry_data(driver)
                    if results:
                        for r in results:
                            save_to_excel(patient, *r)
                        log_message(log_path, f"[✓] Saved {len(results)} audiograms for: {patient}")
                    else:
                        log_message(log_path, f"[!] No audiometry data found for {patient}")
                except Exception as e:
                    log_message(log_path, f"[✘] Info panel failure for {patient}: {e}")
            except Exception as e:
                log_message(log_path, f"[✘] Search failure for {patient}: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
