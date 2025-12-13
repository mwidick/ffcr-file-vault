"""
CounselEAR MRN Refresher – Core v2 GoldCore (OPENPAT v4)

Purpose:
- Open Chrome through your existing SafeCore/Selenium environment
- Wait for manual login until the blue-bar Patient Search box is visible
- For each MRN:
    1) Use Patient Search -> SearchResults
    2) OPEN the patient chart from the Telerik RadGrid SearchResults row
    3) (Best-effort) click Visits tab
    4) (Best-effort) click Save (ctl01_btnSubmit) to trigger VISIT-UPDATE webhook
    5) (Best-effort) click Back - Patient Administration (ctl01_btnCancel)

Notes:
- CounselEAR SearchResults uses Telerik RadGrid and often has NO <a> links in rows.
  Row navigation is driven by JS row events, so we use ActionChains double-click + JS fallback.
- This file is meant to be imported by wrappers (TEST/FULL). It is runnable too.

"""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COUNSELEAR_URL = "https://www.counselear.com/Login.aspx"


# ---------------------------------------------------------------------------
# CSV utilities
# ---------------------------------------------------------------------------

def read_mrns(csv_path: str) -> list[str]:
    """
    Read MRNs from the given CSV file. The file MUST have a column named 'MRN'.
    Returns a list of non-empty MRN strings.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    mrns: list[str] = []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "MRN" not in reader.fieldnames:
            raise RuntimeError(f"CSV {csv_path} must contain a column named 'MRN'")

        for row in reader:
            val = str(row.get("MRN", "")).strip()
            if val:
                mrns.append(val)

    return mrns


# ---------------------------------------------------------------------------
# WebDriver setup
# ---------------------------------------------------------------------------

def setup_driver() -> webdriver.Chrome:
    """
    Create and return a Chrome WebDriver using the same SafeCore/Selenium
    environment that already works for your Patient Activity scripts.

    IMPORTANT:
    - This relies on your SafeCore trust context and existing chromedriver wiring.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


# ---------------------------------------------------------------------------
# Page helpers – Patient Search
# ---------------------------------------------------------------------------

def wait_for_patient_search(driver: webdriver.Chrome, timeout: int = 40):
    """
    Robust locator for the blue-bar Patient Search box at the top of CounselEAR.

    Confirmed selector:
        id="header_secureTopMenu_lookup_txtLookup"
    """
    locators = [
        (By.ID, "header_secureTopMenu_lookup_txtLookup"),
        (By.NAME, "header$secureTopMenu$lookup$txtLookup"),
        (By.CSS_SELECTOR, "input#header_secureTopMenu_lookup_txtLookup"),
        (By.CSS_SELECTOR, "input.SearchDefaultState"),
    ]

    end_time = time.time() + timeout
    attempt = 0
    last_exc: Optional[Exception] = None

    while time.time() < end_time:
        attempt += 1
        print(f"[DEBUG] Patient Search probe attempt {attempt}")

        try:
            driver.switch_to.default_content()
        except Exception as e:
            print(f"[DEBUG] switch_to.default_content() failed: {e}")

        wait = WebDriverWait(driver, 4)

        for by, selector in locators:
            try:
                print(f"[DEBUG] Trying Patient Search locator: {by} '{selector}'")
                el = wait.until(EC.visibility_of_element_located((by, selector)))
                print("[DEBUG] Patient Search box FOUND.")
                return el
            except Exception as e:
                last_exc = e

        time.sleep(1)

    raise last_exc or TimeoutException("Could not locate Patient Search box")


def wait_for_patient_page(driver: webdriver.Chrome, timeout: int = 20) -> bool:
    """
    After hitting ENTER in the Patient Search box, wait for the search-results
    page to appear. Primary signal is URL containing 'SearchResults'.
    """
    try:
        WebDriverWait(driver, timeout).until(EC.url_contains("SearchResults"))
        print("[DEBUG] Patient Search results page detected (URL contains 'SearchResults').")
    except TimeoutException:
        print("[DEBUG] Timed out waiting for patient search results.")
        return False

    # RadGrid often renders as a table with tbody/tr rows.
    try:
        WebDriverWait(driver, 6).until(
            EC.presence_of_element_located(
                (By.XPATH, "//tr[starts-with(@id,'ctl01_resultsGrid_ctl00__')]")
            )
        )
        print("[DEBUG] SearchResults RadGrid row detected.")
    except Exception:
        print("[DEBUG] URL indicates SearchResults, but RadGrid row not detected yet.")
    return True


def open_first_patient_from_results(driver: webdriver.Chrome, timeout: int = 15) -> bool:
    """
    CounselEAR SearchResults uses Telerik RadGrid; rows may NOT contain <a>.
    We open the patient by double-clicking the first row, with a JS fallback.
    """
    try:
        wait = WebDriverWait(driver, timeout)

        row = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//tr[starts-with(@id,'ctl01_resultsGrid_ctl00__')]")
            )
        )

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
        time.sleep(0.2)

        try:
            ActionChains(driver).move_to_element(row).pause(0.1).double_click(row).perform()
            print("[DEBUG] SearchResults row double-clicked (RadGrid).")
        except Exception as e:
            print(f"[DEBUG] Double-click failed, trying JS click fallback: {e}")
            driver.execute_script("arguments[0].click();", row)
            time.sleep(0.1)
            driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('dblclick', {bubbles:true}));", row)
            print("[DEBUG] SearchResults row JS click/dblclick dispatched.")

        # Wait for navigation away from SearchResults (best-effort)
        try:
            WebDriverWait(driver, 10).until_not(EC.url_contains("SearchResults"))
            print("[DEBUG] Navigated away from SearchResults (patient chart opened).")
        except Exception:
            print("[DEBUG] Still on SearchResults after row interaction (may have opened in-place).")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to open patient from SearchResults (RadGrid): {e}")
        return False


# ---------------------------------------------------------------------------
# Page helpers – Visits / Save / Back (best-effort)
# ---------------------------------------------------------------------------

def click_visits_tab(driver: webdriver.Chrome, timeout: int = 8) -> bool:
    """
    Click the Visits tab/label.
    Confirmed HTML example:
        <span class="ceLocaleKeyElement" data-celocalekey="Visits">Visits</span>
    """
    locators = [
        (By.XPATH, "//span[@data-celocalekey='Visits' and normalize-space()='Visits']"),
        (By.XPATH, "//span[@data-celocalekey='Visits']"),
        (By.XPATH, "//td[normalize-space()='Visits']"),
    ]

    wait = WebDriverWait(driver, timeout)
    for by, selector in locators:
        try:
            el = wait.until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.1)
            el.click()
            print("[DEBUG] Visits tab clicked.")
            time.sleep(1)
            return True
        except Exception:
            continue

    print("[DEBUG] Visits tab not found/clicked (may not be available on this page).")
    return False


def click_save_button(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """
    Click Save on a visit page (preferred) or any visible Save button.
    Confirmed selector:
        id="ctl01_btnSubmit"
        xpath: //input[@type='submit' and @value='Save']
    """
    locators = [
        (By.ID, "ctl01_btnSubmit"),
        (By.XPATH, "//input[@type='submit' and @value='Save']"),
        # legacy / fallback:
        (By.ID, "ctl00_cphUserMenu_btnSave"),
        (By.XPATH, "//button[contains(normalize-space(.), 'Save')]"),
    ]

    wait = WebDriverWait(driver, timeout)

    for by, selector in locators:
        try:
            print(f"[DEBUG] Trying Save locator: {by} '{selector}'")
            btn = wait.until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.1)
            btn.click()
            print("[DEBUG] Save button clicked.")
            time.sleep(1.5)
            return True
        except Exception as e:
            # keep logging minimal to avoid drowning
            last = str(e).splitlines()[0] if str(e) else "unknown"
            print(f"[DEBUG] Save locator failed: {by} '{selector}' – {last}")

    print("[DEBUG] No Save button found/clicked on this page.")
    return False


def click_back_patient_admin(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """
    Click Back - Patient Administration.
    Confirmed selector:
        id="ctl01_btnCancel"
    """
    locators = [
        (By.ID, "ctl01_btnCancel"),
        (By.XPATH, "//input[@type='button' and contains(@value, 'Back - Patient Administration')]"),
        (By.XPATH, "//input[contains(@value,'Back') and contains(@value,'Patient')]"),
    ]

    wait = WebDriverWait(driver, timeout)

    for by, selector in locators:
        try:
            print(f"[DEBUG] Trying Back locator: {by} '{selector}'")
            btn = wait.until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.1)
            btn.click()
            print("[DEBUG] Back button clicked.")
            time.sleep(1.0)
            return True
        except Exception:
            continue

    print("[DEBUG] Back button not found/clicked on this page.")
    return False


# ---------------------------------------------------------------------------
# Main entry point used by TEST/FULL wrappers
# ---------------------------------------------------------------------------

def run_mrn_refresh(csv_path: str, mode_label: str = "TEST") -> None:
    """
    High-level driver called by the TEST/FULL wrapper scripts.
    """
    print(f"=== CounselEAR MRN Refresh – {mode_label} (OPENPAT v4) ===")
    print(f"CSV: {csv_path}")

    mrns = read_mrns(csv_path)
    print(f"Loaded {len(mrns)} MRNs from {csv_path}")

    driver = setup_driver()
    driver.get(COUNSELEAR_URL)

    print("\nPlease log in to CounselEAR in the browser window,")
    print("including Google Authenticator if needed, until you see your normal dashboard.")
    print("This script will automatically continue once it can see the blue Patient Search box.\n")

    # Wait for Patient Search on the dashboard
    wait_for_patient_search(driver)

    for idx, mrn in enumerate(mrns, start=1):
        print(f"\n=== [{idx}/{len(mrns)}] MRN {mrn} ===")

        # Find the search box each time
        try:
            search_box = wait_for_patient_search(driver)
            search_box.clear()
            search_box.send_keys(mrn + Keys.ENTER)
        except Exception as e:
            print(f"[ERROR] Could not type MRN {mrn}: {e}")
            continue

        if not wait_for_patient_page(driver):
            print(f"[ERROR] Patient search page did not load correctly for MRN {mrn}")
            continue

        if not open_first_patient_from_results(driver):
            print(f"[ERROR] Could not open patient chart from SearchResults for MRN {mrn}")
            continue

        # Best-effort: click Visits (if present), then Save, then Back
        click_visits_tab(driver)
        click_save_button(driver)
        click_back_patient_admin(driver)

        time.sleep(1.0)

    print("\n=== MRN refresh complete – you can close the browser when ready. ===")


# Optional: allow direct execution
if __name__ == "__main__":
    # Default to a safe, obvious message rather than running accidentally.
    print("This is a core module. Run via your wrapper (e.g., counselear_visit_refresher_TEST_v1d.py).")
