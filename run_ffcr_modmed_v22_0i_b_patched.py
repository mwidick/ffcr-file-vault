
import os
import time
import pandas as pd
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Constants
EXCEL_FILE = 'mrn_input.xlsx'
CHROMEDRIVER_EXE = r"C:\FFCR_Project\chromedriver.exe"
CHROMEDRIVER_DIR = os.path.dirname(CHROMEDRIVER_EXE)
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')

# Create downloads folder if not exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Chrome version enforcement
# Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = r"C:\\FFCR_Project\\chrome135\\chrome.exe"
chrome_options = webdriver.ChromeOptions()
prefs = {'download.default_directory': DOWNLOAD_DIR}
chrome_options.add_experimental_option('prefs', prefs)

# Read MRNs from Excel with defensive handling
df = pd.read_excel(EXCEL_FILE)
if 'MRN' not in df.columns:
    print("\nERROR: Excel file is missing the required 'MRN' column.")
    print("Please verify that the spreadsheet includes a column labeled 'MRN'.")
    exit(1)
mrns = df['MRN'].astype(str).tolist()

# Launch browser
driver = webdriver.Chrome(service=ChromeService(CHROMEDRIVER_EXE), options=chrome_options)
driver.get("https://login.modmed.com")

# Login sequence
WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username"))).send_keys("USERNAME")
driver.find_element(By.ID, "password").send_keys("PASSWORD")
driver.find_element(By.ID, "loginButton").click()

# Process each MRN
for mrn in mrns:
    print(f"Processing MRN: {mrn}")
    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "patientsMenuNavTab"))).click()
        search_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "patientSearchInput")))
        search_input.clear()
        search_input.send_keys(mrn)

        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "tr.patientRow"))).click()

        # --- ATTACHMENTS TAB EXTRACTION ---
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "attachmentsTab"))).click()
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "attachmentTable")))
        attachment_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
        for link in attachment_links:
            link.click()
            time.sleep(2)

        # --- PATIENT ACTIVITY TAB EXTRACTION ---
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "patientActivityTab"))).click()
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "activityTable")))
        activity_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
        for link in activity_links:
            link.click()
            time.sleep(2)

    except TimeoutException as e:
        print(f"Timeout for MRN {mrn}: {e}")
    except Exception as e:
        print(f"Error with MRN {mrn}: {e}")

# Finalization
time.sleep(10)
driver.quit()
print("All MRNs processed.")
