import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EXCEL_FILE = "mrn_input.xlsx"
def load_mrns_from_excel(file_path):
    df = pd.read_excel(file_path, header=None)
    return [str(mrn).strip() for mrn in df[0].tolist() if str(mrn).strip()]
MRN_LIST = load_mrns_from_excel(EXCEL_FILE)

chrome_binary = r"C:\\FFCR_Project\\Pair E\\chrome-win64\\chrome.exe"
driver_path = r"C:\\FFCR_Project\\Pair E\\chromedriver-win64\\chromedriver.exe"

options = Options()
options.binary_location = chrome_binary
options.add_experimental_option("prefs", {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "profile.default_content_setting_values.automatic_downloads": 1
})
options.add_argument("--remote-debugging-port=9222")

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

driver.get("https://entaaf.ema.md/ema/Login.action")
wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit" and contains(@value, "Practice Staff")]'))).click()
wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("mwidick")
wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys("Nosethroat25!")
wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()
wait.until(EC.presence_of_element_located((By.ID, "patientsMenuNavTab")))

print("✅ Login successful. MRNs loaded:", MRN_LIST)
