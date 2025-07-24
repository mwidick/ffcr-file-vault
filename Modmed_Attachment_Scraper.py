
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import re
from datetime import datetime

def download_relevant_attachments(driver, download_dir, keywords, image_keywords):
    wait = WebDriverWait(driver, 10)
    seen_links = set()

    while True:
        rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) > 3:
                    title = cells[0].text.strip().lower()
                    category = cells[1].text.strip().lower()
                    link_el = cells[2].find_element(By.TAG_NAME, 'a')
                    href = link_el.get_attribute('href')
                    added_on = cells[3].text.strip()

                    if not href or href in seen_links:
                        continue

                    seen_links.add(href)

                    # Determine if this is an operative report or an ear-related image
                    file_ext = os.path.splitext(href)[-1].lower()
                    is_pdf_or_doc = file_ext in ['.pdf', '.doc', '.docx']
                    is_image = file_ext in ['.jpg', '.jpeg', '.png']

                    if any(k in title for k in keywords) and is_pdf_or_doc:
                        print(f"[+] Downloading operative report: {title}")
                        driver.execute_script("window.open(arguments[0]);", href)
                        time.sleep(2)
                    elif any(k in title for k in image_keywords) and is_image:
                        print(f"[+] Downloading ear image: {title}")
                        driver.execute_script("window.open(arguments[0]);", href)
                        time.sleep(2)
            except Exception as e:
                print(f"[!] Error processing row: {e}")

        # Try to click next page if it exists
        try:
            next_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'i.fa-angle-right')))
            parent_a = next_button.find_element(By.XPATH, './ancestor::a[1]')
            if 'disabled' in parent_a.get_attribute('class'):
                print("[-] No more pages.")
                break
            print("[>] Moving to next page of attachments...")
            driver.execute_script("arguments[0].click();", parent_a)
            time.sleep(3)
        except Exception:
            print("[-] No pagination or cannot move forward.")
            break
