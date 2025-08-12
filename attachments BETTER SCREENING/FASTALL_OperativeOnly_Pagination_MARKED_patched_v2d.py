# ======= FFCR FILE: FASTALL_OperativeOnly_Pagination_MARKED_patched.py =======
# Purpose: Keep GoldCore frozen; patch modular pagination to be robust (scroll, visibility waits, retries).
# Logs frozen/modular section SHA256 for forensics.

import os, time, re, hashlib, requests, pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException, StaleElementReferenceException, ElementNotInteractableException

# ========= CONFIG (unchanged from baseline) =========
BASE_DIR = "./Activity_PDF_Output"
SCREENSHOT_DIR = "./screenshots"
LOG_PATH = "modmed_patch4_run_log.txt"
CHROMEDRIVER_PATH = r"C:\\FFCR_Project\\Pair E\\chromedriver-win64\\chromedriver.exe"
CREDENTIAL_FILE = "counselear_credentials.xlsx"
PATIENT_FILE = "counselear_patients.xlsx"

# ========= SETUP =========
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

print("=== FASTALL OperativeOnly + Pagination (Patched) ===")
print(f"OUTPUT_ROOT={BASE_DIR}")

def log_msg(f, msg):
    print(msg)
    f.write(f"{datetime.now().isoformat()} - {msg}\n")

with open(LOG_PATH, "a", encoding="utf-8") as log:
    log_msg(log, "===== FFCR ModMed OperativeOnly+Pagination (Patched) Start =====")

    try:
        # Load credentials and MRNs (unchanged)
        creds = pd.read_excel(CREDENTIAL_FILE)
        username = creds.iloc[0]["username"]
        password = creds.iloc[0]["password"]
        mrns = pd.read_excel(PATIENT_FILE).iloc[:, 0].astype(str).tolist()
        log_msg(log, f"Loaded {len(mrns)} MRNs from Excel.")

        # Chrome setup (unchanged except prefs)
        options = webdriver.ChromeOptions()
        options.binary_location = r"C:\\FFCR_Project\\Pair E\\chrome-win64\\chrome.exe"
        prefs = {
            "download.default_directory": os.path.abspath(BASE_DIR),
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False,
        }
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--start-maximized")
        options.add_argument("--incognito")
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
        wait = WebDriverWait(driver, 20)

        # ======= FFCR_FROZEN_SECTION_START (DO NOT EDIT) =======
        # ========= FROZEN START =========
        def login():
            driver.get("https://entaaf.ema.md/ema/Login.action")
            # Practice Staff landing
            wait.until(EC.element_to_be_clickable((By.XPATH, '//input[contains(@value,"Practice Staff")]'))).click()
            # Credentials
            wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
            wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Login")]'))).click()

        def dismiss_modal():
            try:
                modal = driver.find_element(By.CSS_SELECTOR, 'modal-container[role="dialog"]')
                driver.execute_script("arguments[0].remove();", modal)
                log_msg(log, "[~] Modal dismissed.")
            except Exception:
                pass

        def open_patient(mrn):
            driver.get("https://entaaf.ema.md/ema/web/practice/staff#/practice/staff/patient/list")
            combo = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ng-select-container div.ng-input")))
            dismiss_modal()
            combo.click(); time.sleep(1)
            inp = combo.find_element(By.TAG_NAME, "input")
            inp.clear(); inp.send_keys(mrn); time.sleep(1); inp.send_keys(u'\ue007')
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))).click()
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.po-visit-date")))
        # ========= FROZEN END =========
        # ======= FFCR_FROZEN_SECTION_END (DO NOT EDIT) =======

        # ======= FFCR_MODULAR_SECTION_START =======
        # ========= MODULAR START =========
        # Hardened pagination + operative-only extraction
        OPERATIVE_KEYWORDS = [
            "operative report","op report","op. report","operation report",
            "surgical report","opnote","op note","op-note","op rpt","op rpt.",
            "op_report","op-report","opreport","op_report_scan",
            "tympanoplasty","mastoidectomy","stapedectomy","tympanomastoidectomy",
            "post-op operative","operation note","procedure report",
        ]
        def is_operative(s: str) -> bool:
            t = (s or "").lower()
            return any(k in t for k in OPERATIVE_KEYWORDS)

        def safe_join(a,b):
            base, ext = os.path.splitext(b)
            i = 2
            out = os.path.join(a, b)
            while os.path.exists(out):
                out = os.path.join(a, f"{base} ({i}){ext}")
                i += 1
            return out

        def kill_backdrops():
            try:
                driver.execute_script("""
                    for (const sel of ['bs-modal-backdrop','.modal-backdrop','modal-container[role="dialog"]']) {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    }
                """)
            except Exception:
                pass

        def table_signature():
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                if not rows: return ("", "", 0)
                return (rows[0].text.strip(), rows[-1].text.strip(), len(rows))
            except StaleElementReferenceException:
                return ("", "", -1)

        def wait_for_table_change(timeout=12, before=None):
            end = time.time() + timeout
            while time.time() < end:
                sig = table_signature()
                if before is None:
                    if sig[2] > 0:
                        time.sleep(0.3)
                        if table_signature() == sig:
                            return sig
                else:
                    if sig != before and sig[2] >= 0:
                        time.sleep(0.3)
                        if table_signature() == sig:
                            return sig
                time.sleep(0.2)
            return table_signature()

        def open_attachments_tab():
            log_msg(log, "Opening Attachments tab...")
            tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.nav-tab.ngx-nav-tab[data-identifier="attachments-tab"]')))
            try: tab.click()
            except Exception: driver.execute_script("arguments[0].click();", tab)
            # Wait for at least one row (table rendered)
            wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "table tbody tr")) >= 1)

        def _locate_page_size_select():
            # Multiple selectors as seen in patient activity script
            selectors = [
                (By.ID, "pageSizeSelect"),
                (By.CSS_SELECTOR, "select#pageSizeSelect"),
                (By.CSS_SELECTOR, "select[data-identifier^='pagination-view-records-by']"),
            ]
            for by, sel in selectors:
                try:
                    el = driver.find_element(by, sel)
                    return el
                except Exception:
                    continue
            raise TimeoutException("page size <select> not found")

        def set_per_page_to_100(max_attempts=3):
            attempts = 0
            last_err = ""
            while attempts < max_attempts:
                attempts += 1
                try:
                    kill_backdrops()
                    select_el = _locate_page_size_select()
                    # scroll into middle to avoid sticky footer/header overlay
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_el)
                    # wait for visibility & enabled state
                    wait.until(EC.visibility_of(select_el))
                    wait.until(lambda d: select_el.is_enabled())
                    sel = Select(select_el)
                    before = table_signature()
                    tried = []
                    for val in ["number:100", "100"]:
                        try:
                            sel.select_by_value(val); tried.append(f"value:{val}"); break
                        except Exception as e:
                            last_err = str(e)
                    else:
                        try:
                            sel.select_by_visible_text("100"); tried.append("visible_text:100")
                        except Exception as e:
                            last_err = str(e)
                            # final fallback: last option
                            opts = sel.options
                            sel.select_by_index(len(opts)-1); tried.append(f"index:{len(opts)-1}")
                    sig = wait_for_table_change(timeout=12, before=before)
                    which = sel.first_selected_option.text.strip()
                    log_msg(log, f"[PERPAGE] Selected '{which}' via {tried}; sig={sig}")
                    return which
                except Exception as e:
                    last_err = str(e)
                    log_msg(log, f"[PERPAGE WARN] attempt {attempts}/{max_attempts} failed: {last_err}")
                    # small nudge: reopen tab and try again
                    try:
                        open_attachments_tab()
                    except Exception:
                        pass
            # out of attempts
            raise TimeoutException(f"Could not set per-page to 100 after {max_attempts} attempts: {last_err}")

        def collect_attachment_rows():
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            out = []
            for r in rows:
                try:
                    tds = r.find_elements(By.CSS_SELECTOR, "td")
                    title = (tds[0].text if tds else r.text).strip()
                    href = ""
                    for css in ["a[href*='/ema/secure/fileattachment/']","a[href*='fileattachment']","a[href$='.pdf']","a[href]"]:
                        try:
                            a = r.find_element(By.CSS_SELECTOR, css)
                            h = a.get_attribute("href")
                            if h: href = h; break
                        except Exception: pass
                    if href:
                        out.append((title, href))
                except Exception:
                    continue
            return out

        def click_next_page():
            before = table_signature()
            try:
                nxt = driver.find_element(By.CSS_SELECTOR, "a[data-identifier='pagination-next']")
            except Exception:
                return False
            cls = (nxt.get_attribute("class") or "").lower()
            if "disabled" in cls:
                return False
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", nxt)
                driver.execute_script("arguments[0].click();", nxt)
            except Exception:
                return False
            sig = wait_for_table_change(timeout=10, before=before)
            return sig != before and sig[2] >= 0

        def extract_operatives_all_pages(mrn):
            # Seed requests session with Selenium cookies
            cookies = driver.get_cookies()
            session = requests.Session()
            for c in cookies:
                try: session.cookies.set(c['name'], c['value'], domain=c.get('domain'), path=c.get('path','/'))
                except Exception: session.cookies.set(c['name'], c['value'])
            mrn_dir = os.path.join(BASE_DIR, mrn); os.makedirs(mrn_dir, exist_ok=True)
            saved = 0

            # Open tab + set per-page
            open_attachments_tab()
            try:
                _ = set_per_page_to_100()
            except Exception as e:
                log_msg(log, f"[WARN] set_per_page_to_100 ultimately failed: {e} (continuing at 25 per page)")

            page = 1
            while True:
                rows = collect_attachment_rows()
                log_msg(log, f"[{mrn}] PAGE {page} rows={len(rows)}")
                for title, href in rows:
                    if not (is_operative(title) or is_operative(href)):
                        continue
                    if ".pdf" not in href.lower():
                        continue
                    filename = href.split("/")[-1].split("?")[0]
                    try:
                        r = session.get(href, timeout=60)
                        if r.ok:
                            final = safe_join(mrn_dir, filename)
                            with open(final, "wb") as f: f.write(r.content)
                            saved += 1
                        else:
                            log_msg(log, f"[{mrn}] Failed {filename} ({r.status_code})")
                    except Exception as e:
                        log_msg(log, f"[{mrn}] ERROR {filename}: {e}")
                if not click_next_page():
                    break
                page += 1
            return saved
        

        # v2d hardening: robust try/except, window-handle guardian, steady logging, continue-on-error
        def _handles_guard(expected_min=1, max_close=5):
            try:
                hs = driver.window_handles[:]
                if len(hs) >= expected_min:
                    return hs
                return hs
            except Exception:
                return []

        def _close_excess_handles(keep_first=True, limit=10):
            try:
                hs = driver.window_handles[:]
                base = hs[0] if (hs and keep_first) else None
                closed = 0
                # close everything except base
                for h in hs[1:] if base else hs:
                    try:
                        driver.switch_to.window(h)
                        driver.close()
                        closed += 1
                        if closed >= limit:
                            break
                    except Exception:
                        pass
                if base:
                    driver.switch_to.window(base)
                return closed
            except Exception:
                return 0

        def _safe_wait_rows(timeout=20):
            t0 = time.time()
            last = 0
            while time.time() - t0 < timeout:
                try:
                    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    if len(rows) != last:
                        last = len(rows)
                        time.sleep(0.2)
                        rows2 = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                        if len(rows2) == last and last > 0:
                            return rows2
                except StaleElementReferenceException:
                    pass
                except Exception:
                    pass
                time.sleep(0.2)
            return driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        def collect_attachment_rows_hardened():
            rows = _safe_wait_rows()
            out = []
            for r in rows:
                try:
                    tds = r.find_elements(By.CSS_SELECTOR, "td")
                    title = (tds[0].text if tds else r.text).strip()
                    href = ""
                    click_xpath = ""
                    for css in ["a[href*='/ema/secure/fileattachment/']",
                                "a[href*='fileattachment']",
                                "a[href$='.pdf']",
                                "a[href]"]:
                        try:
                            a = r.find_element(By.CSS_SELECTOR, css)
                            h = a.get_attribute("href")
                            if h:
                                href = h
                                break
                        except Exception:
                            pass
                    if not href:
                        for xp in [
                            ".//a[contains(@ng-click,'open') or contains(@ng-click,'view') or contains(@class,'link')]",
                            ".//td[1]//*[self::a or self::button]",
                        ]:
                            try:
                                r.find_element(By.XPATH, xp)
                                click_xpath = xp
                                break
                            except Exception:
                                continue
                    out.append({"title": title, "href": href, "click_xpath": click_xpath})
                except Exception as e:
                    log_msg(log, f"[ROW-WARN] row parse error: {e}")
                    continue
            return out

        def _open_click_and_capture_pdf_hardened(session, mrn_dir, title, row, click_xpath):
            try:
                if not click_xpath:
                    return False
                try:
                    el = row.find_element(By.XPATH, click_xpath)
                except Exception:
                    return False
                base_handles = driver.window_handles[:]
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                try:
                    el.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", el)
                    except Exception as e:
                        log_msg(log, f"[CLICK-FAIL] {title}: {e}")
                        return False
                time.sleep(1.2)
                new_handles = driver.window_handles[:]
                target = None
                if len(new_handles) > len(base_handles):
                    target = list(set(new_handles) - set(base_handles))[0]
                if target:
                    driver.switch_to.window(target)
                href = ""
                try:
                    href = driver.current_url or ""
                except Exception:
                    href = ""
                ok = False
                if ".pdf" in href.lower():
                    filename = href.split("/")[-1].split("?")[0] or "document.pdf"
                    try:
                        r = session.get(href, timeout=60)
                        if r.ok:
                            final = safe_join(mrn_dir, filename)
                            with open(final, "wb") as f: f.write(r.content)
                            ok = True
                        else:
                            log_msg(log, f"[PDF-HTTP] {title}: {r.status_code}")
                    except Exception as e:
                        log_msg(log, f"[PDF-GET-ERR] {title}: {e}")
                # cleanup
                if target:
                    try:
                        driver.close()
                    except Exception:
                        pass
                    try:
                        driver.switch_to.window(base_handles[0])
                    except Exception:
                        pass
                _close_excess_handles()
                return ok
            except Exception as e:
                log_msg(log, f"[CLICK-FALLBACK-EXC] {title}: {e}")
                _close_excess_handles()
                return False

        def extract_operatives_all_pages_hardened(mrn):
            try:
                cookies = driver.get_cookies()
            except Exception as e:
                log_msg(log, f"[COOKIES-ERR] {e}")
                cookies = []
            session = requests.Session()
            for c in cookies:
                try: session.cookies.set(c['name'], c['value'], domain=c.get('domain'), path=c.get('path','/'))
                except Exception: 
                    try: session.cookies.set(c['name'], c['value'])
                    except Exception: pass

            mrn_dir = os.path.join(BASE_DIR, mrn); os.makedirs(mrn_dir, exist_ok=True)
            saved = 0

            try:
                open_attachments_tab()
            except Exception as e:
                log_msg(log, f"[ATTACHMENTS-OPEN-ERR] {e}")
                return saved

            try:
                _ = set_per_page_to_100()
            except Exception as e:
                log_msg(log, f"[PERPAGE-WARN] {e}")

            page = 1
            while True:
                try:
                    rows = collect_attachment_rows_hardened()
                    log_msg(log, f"[{mrn}] PAGE {page} rows={len(rows)}")
                    dom_rows = _safe_wait_rows()
                    for idx, row_info in enumerate(rows, start=1):
                        title, href, click_xpath = row_info["title"], row_info["href"], row_info["click_xpath"]
                        is_op = is_operative(title) or is_operative(href)
                        if not is_op:
                            continue
                        ok = False
                        if href and ".pdf" in href.lower():
                            filename = href.split("/")[-1].split("?")[0]
                            try:
                                r = session.get(href, timeout=60)
                                if r.ok:
                                    final = safe_join(mrn_dir, filename)
                                    with open(final, "wb") as f: f.write(r.content)
                                    saved += 1
                                    ok = True
                                else:
                                    log_msg(log, f"[{mrn}] Failed {filename} ({r.status_code})")
                            except Exception as e:
                                log_msg(log, f"[{mrn}] ERROR {filename}: {e}")
                        if not ok and click_xpath:
                            try:
                                row_el = dom_rows[idx-1] if idx-1 < len(dom_rows) else None
                                if row_el:
                                    got = _open_click_and_capture_pdf_hardened(session, mrn_dir, title, row_el, click_xpath)
                                    if got:
                                        saved += 1
                                    else:
                                        log_msg(log, f"[{mrn}] CLICK-FALLBACK failed for title='{title}'")
                            except Exception as e:
                                log_msg(log, f"[{mrn}] CLICK-FALLBACK error for title='{title}': {e}")
                except Exception as e:
                    log_msg(log, f"[PAGE-LOOP-ERR] page={page}: {e}")
                try:
                    if not click_next_page():
                        break
                except Exception as e:
                    log_msg(log, f"[PAGINATION-ERR] {e}")
                    break
                page += 1
            return saved
# ========= MODULAR END =========
        # ======= FFCR_MODULAR_SECTION_END =======

        # ========= Run =========
        login()
        summary_rows = []
        for mrn in mrns:
            log_msg(log, f"Processing MRN: {mrn}")
            try:
                open_patient(mrn)
            except Exception as e:
                # One retry after nuking any backdrops
                try:
                    driver.execute_script("document.querySelectorAll('bs-modal-backdrop,.modal-backdrop,modal-container[role=\"dialog\"]').forEach(el=>el.remove())")
                except Exception:
                    pass
                try:
                    open_patient(mrn)
                except Exception as e2:
                    log_msg(log, f"[{mrn}] Could not open patient after retries: {e2}")
                    continue
            cnt = extract_operatives_all_pages(mrn)
            log_msg(log, f"[{mrn}] Saved {cnt} operative PDFs.")
            summary_rows.append({"mrn": mrn, "operative_pdfs": cnt, "ts": datetime.now().isoformat(timespec="seconds")})

        # Write a lightweight summary CSV
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = os.path.join(BASE_DIR, f"run_summary_operatives_{ts}.csv")
        pd.DataFrame(summary_rows).to_csv(summary_path, index=False)

        # ===== Checksums (frozen/modular only) =====
        try:
            with open(__file__, "r", encoding="utf-8") as sf:
                src = sf.read()
            def _sha(txt): return hashlib.sha256(txt.encode("utf-8")).hexdigest()
            mf = re.search(r"# ========= FROZEN START =========(.*?)# ========= FROZEN END =========", src, re.S)
            mm = re.search(r"# ========= MODULAR START =========(.*?)# ========= MODULAR END =========", src, re.S)
            frozen_part = mf.group(1) if mf else ""
            modular_part = mm.group(1) if mm else ""
            log_msg(log, f"[CHECKSUM] Frozen SHA256:  {_sha(frozen_part)}")
            log_msg(log, f"[CHECKSUM] Modular SHA256: {_sha(modular_part)}")
        except Exception as e:
            log_msg(log, f"[CHECKSUM ERROR] {e}")

        driver.quit()
        log_msg(log, "===== FFCR ModMed OperativeOnly+Pagination (Patched) Finished =====")

    except Exception as e:
        log_msg(log, f"[FATAL ERROR] {e}")
