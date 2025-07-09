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

def main():
    creds = pd.read_excel("counselear_credentials.xlsx")
    username = creds.loc[0, "username"]
    password = creds.loc[0, "password"]

    chrome_options = Options()
    chrome_options.binary_location = "C:/FFCR_Project/Pair E/chrome-win64/chrome.exe"
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.abspath("visit_activity"),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })

    service = Service("C:/FFCR_Project/Pair E/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
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
        patients = df["PatientName"].tolist()

        for patient_name in patients:
            try:
                search_box = wait.until(EC.presence_of_element_located((By.ID, "header_secureTopMenu_lookup_txtLookup")))
                search_box.clear()
                search_box.send_keys(patient_name)
                search_box.send_keys(Keys.RETURN)
                print(f"[SEARCHING] {patient_name}")
                time.sleep(3)

                # Wait for and click first result row
                result_row = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".rgRow, .rgAltRow")))
                result_row.click()
                print(f"[CLICKED] First result row for {patient_name}")
                time.sleep(3)

            except Exception as e:
                print(f"[ERROR] Search/click failed for {patient_name}: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
