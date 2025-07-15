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

def extract_audiometry_data(driver):
    table_rows = driver.find_elements(By.CSS_SELECTOR, "#ctl01_ctlPatientSummary_tblTestResults tr")
    if len(table_rows) < 2:
        return None

    header_cells = table_rows[0].find_elements(By.TAG_NAME, "th")[1:]
    data_cells = table_rows[1].find_elements(By.TAG_NAME, "td")
    if len(data_cells) < len(header_cells) + 1:
        return None

    test_date = data_cells[0].text.strip()
    air_r = [data_cells[i].text.strip() for i in range(1, len(header_cells) + 1, 2)]
    air_l = [data_cells[i].text.strip() for i in range(2, len(header_cells) + 1, 2)]
    bone_r = ["" for _ in air_r]
    bone_l = ["" for _ in air_l]
    return test_date, air_r, air_l, bone_r, bone_l

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

def main():
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
        patients = df["patient_name"].tolist()
        mrns = df["mrn"].tolist() if "mrn" in df.columns else ["UNKNOWN"] * len(patients)
        for patient_name, mrn in zip(patients, mrns):
            try:
                sb = wait.until(EC.presence_of_element_located((By.ID, "header_secureTopMenu_lookup_txtLookup")))
                sb.clear()
                sb.send_keys(str(patient_name))
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
                    fname = f"{str(patient_name).replace(' ', '_')}_{str(mrn)}.png"
                    driver.save_screenshot(os.path.join(ss_dir, fname))
                    extracted = extract_audiometry_data(driver)
                    if extracted:
                        save_to_excel(mrn, *extracted)
                except Exception as e:
                    print(f"[ERROR] patient info {patient_name}: {e}")
            except Exception as e:
                print(f"[ERROR] search {patient_name}: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()