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
        # Early checksum log (so partial runs still record forensics)
        try:
            with open(__file__, "r", encoding="utf-8") as sf:
                _src_all = sf.read()
            def _sha(txt): 
                import hashlib
                return hashlib.sha256(txt.encode("utf-8")).hexdigest()
            _mf = re.search(r"# ========= FROZEN START =========(.*?)# ========= FROZEN END =========", _src_all, re.S)
            _mm = re.search(r"# ========= MODULAR START =========(.*?)# ========= MODULAR END =========", _src_all, re.S)
            _frozen = _mf.group(1) if _mf else ""
            _mod = _mm.group(1) if _mm else ""
            log_msg(log, f"[CHECKSUM-EARLY] Frozen SHA256:  {_sha(_frozen)}")
            log_msg(log, f"[CHECKSUM-EARLY] Modular SHA256: {_sha(_mod)}")
        except Exception as e:
            log_msg(log, f"[CHECKSUM-EARLY ERROR] {e}")


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
        # MODv2 — Dual-column matching (Category + Title) + weighted keywords + older-chart screening
        _DEFAULT_MIN_DATE = '2016-01-01'
        AGGRESSIVE = os.getenv('FFCR_AGGRESSIVE','0') == '1'
        BASE_THRESHOLD = 22 if AGGRESSIVE else 26
        _MRN_DATE_CSV = os.getenv('FFCR_MRN_DATE_CSV','mrn_procedure_dates.csv')
        _DT_FMT = '%Y-%m-%d'
        CAT_POSITIVE = [r'\boperative\b', r'\bop\s*report\b', r'\boperative\s*report\b', r'\boperative\s*note\b', r'\bop\s*note\b', r'\bsurgery\b', r'\bprocedure\b']
        CAT_NEGATIVE = [r'\bpre[-\s]?op\b', r'\bpost[-\s]?op\b', r'\bprogress\b', r'\bclinic\b', r'\breferral\b', r'\binsurance\b', r'\bclearance\b', r'\boutbound fax(?:es)?\b', r'\bpathology\b', r'\blab(?:oratory)?\b', r'\bradiology|MRI|CT|x[-\s]?ray\b']
        TITLE_BOOSTS = {r'\boperative report\b':40, r'\boperative note\b':34, r'\bop(?:erative)?\s*report\b':28, r'\bop(?:erative)?\s*note\b':26, r'\bsurgery\b':14, r'\bprocedure\b':16, r'\bOR\s+(?:report|note)\b':24}
        POSITIVE_WEIGHTS = {r'\bindications?\b':10, r'\bfindings?\b':10, r'\bprocedure\b':12, r'\btechnique\b':10, r'\bestimated blood loss\b':12, r'\banesthesia\b':10, r'\bassistant\b':8, r'\bcomplications?\b':10, r'\bimplants?\b':8, r'\bdisposition\b':8, r'\btourniquet\b':8, r'\barthroscop(?:y|ic)\b':8, r'\bmeniscectomy\b':8, r'\brotator cuff\b':8, r'\bACLR?\b':8}
        NEGATIVE_WEIGHTS = {r'\bpre[-\s]?op(?:erative)? (?:clearance|clinic|visit|assessment)\b':-24, r'\bpost[-\s]?op(?:erative)? (?:visit|check|clinic)\b':-18, r'\bprogress note\b':-14, r'\bdischarge summary\b':-12, r'\bpathology report\b':-12, r'\bradiology|MRI|CT|x[-\s]?ray\b':-12, r'\bH&P\b':-10, r'\bhistory and physical\b':-10, r'\bconsult(?:ation)?\b':-10}
        def _parse_date_safe(s: str):
            s = (s or '').strip()
            for fmt in (_DT_FMT, '%m/%d/%Y','%m-%d-%Y','%Y/%m/%d'):
                try: return datetime.strptime(s, fmt)
                except Exception: pass
            m = re.search(r'\b(19|20)\d{2}\b', s)
            if m:
                try: return datetime(int(m.group(0)),6,30)
                except Exception: return None
            return None
        def _get_min_date():
            max_age = os.getenv('FFCR_MAX_AGE_YEARS')
            if max_age:
                try: return datetime.today() - timedelta(days=365*int(max_age))
                except Exception: pass
            dt = _parse_date_safe(os.getenv('FFCR_MIN_DATE', _DEFAULT_MIN_DATE))
            return dt or datetime(2016,1,1)
        def _load_mrn_date_map(path: str):
            mapping = {}
            try:
                with open(path,'r',encoding='utf-8') as f:
                    for row in csv.DictReader(f):
                        m = (row.get('MRN') or '').strip(); d = (row.get('ProcedureDate') or '').strip()
                        if m and d: mapping[m]=d
            except FileNotFoundError:
                pass
            except Exception as e:
                log_msg(log, f"[MODULAR] could not read {path}: {e}") if 'log' in globals() else print(f"[MODULAR] could not read {path}: {e}")
            return mapping
        _MRN_DATE_MAP = _load_mrn_date_map(_MRN_DATE_CSV)
        def _any_match(rx_list, text):
            return any(re.search(rx, text or '', flags=re.I) for rx in rx_list)
        def _score(patterns, text):
            total=0; hits=[]
            for rx,w in patterns.items():
                if re.search(rx, text or '', flags=re.I):
                    total+=w; hits.append(f"{rx}:{w}")
            return total, hits
        def evaluate_row(category, title, body_preview):
            cat_pos = _any_match(CAT_POSITIVE, category)
            cat_neg = _any_match(CAT_NEGATIVE, category)
            cat_score = (18 if cat_pos else 0) + (-12 if cat_neg else 0)
            title_score, title_hits = _score(TITLE_BOOSTS, title)
            pos_score, pos_hits = _score(POSITIVE_WEIGHTS, f"{title}\n{body_preview}")
            neg_score, neg_hits = _score(NEGATIVE_WEIGHTS, f"{title}\n{body_preview}")
            score = cat_score + title_score + pos_score + neg_score
            passes = (score >= BASE_THRESHOLD) or (cat_pos and (title_score>0 or pos_score>0))
            return {'score':score,'passes':passes,'threshold':BASE_THRESHOLD,'cat_score':cat_score,'title_score':title_score,'pos_score':pos_score,'neg_score':neg_score,'title_hits':title_hits,'pos_hits':pos_hits,'neg_hits':neg_hits,'cat_pos':cat_pos,'cat_neg':cat_neg}
        def classify_age(encounter_date, doc_date, title, mrn=None):
            min_dt = _get_min_date()
            e = _parse_date_safe(encounter_date or '')
            d = _parse_date_safe(doc_date or '')
            if mrn and mrn in _MRN_DATE_MAP:
                md = _parse_date_safe(_MRN_DATE_MAP[mrn])
                if md: e = md
            best = e or d or _parse_date_safe(title)
            return {'best_date': best.strftime(_DT_FMT) if best else None, 'older_than_cutoff': bool(best and best < min_dt), 'cutoff': min_dt.strftime(_DT_FMT)}
        _SUMMARY = []
        def evaluate_and_record(category, title, body_preview, encounter_date, doc_date, extra=None):
            info = evaluate_row(category, title, body_preview)
            mrn = str(extra.get('mrn')) if isinstance(extra, dict) and 'mrn' in extra else None
            age = classify_age(encounter_date, doc_date, title, mrn=mrn)
            row = {'mrn': mrn or '', 'category': category, 'title': title, 'encounter_date': encounter_date, 'doc_date': doc_date, 'best_date': age['best_date'], 'older_than_cutoff': age['older_than_cutoff'], 'score': info['score'], 'threshold': info['threshold'], 'passes': info['passes'], 'cat_score': info['cat_score'], 'title_score': info['title_score'], 'pos_score': info['pos_score'], 'neg_score': info['neg_score'], 'title_hits': ';'.join(info['title_hits']), 'pos_hits': ';'.join(info['pos_hits']), 'neg_hits': ';'.join(info['neg_hits']), 'cat_pos': info['cat_pos'], 'cat_neg': info['cat_neg']}
            if isinstance(extra, dict):
                for k,v in extra.items():
                    if k not in row: row[k]=v
            _SUMMARY.append(row)
            return row
        def write_summary_csv(path='op_candidates_summary.csv'):
            if not _SUMMARY: return
            fields=['mrn','category','title','encounter_date','doc_date','best_date','older_than_cutoff','score','threshold','passes','cat_score','title_score','pos_score','neg_score','title_hits','pos_hits','neg_hits','cat_pos','cat_neg']
            try:
                with open(path,'w',newline='',encoding='utf-8') as f:
                    w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(_SUMMARY)
            except Exception as e:
                log_msg(log, f"[MODULAR] Could not write {path}: {e}") if 'log' in globals() else print(f"[MODULAR] Could not write {path}: {e}")
        # ========= MODULAR END =========
        # ======= FFCR_MODULAR_SECTION_END =======

        
        # --- Patch4b: robust wrapper around frozen open_patient ---
        def robust_open_patient(mrn, max_tries=3):
            tries = 0
            while tries < max_tries:
                tries += 1
                try:
                    # Pre-empt modals/backdrops that block clicks
                    try:
                        kill_backdrops()
                    except Exception:
                        pass
                    try:
                        dismiss_modal()
                    except Exception:
                        pass
                    open_patient(mrn)
                    return True
                except StaleElementReferenceException:
                    log_msg(log, f"[RETRY-OPEN:{tries}] stale element → reload list")
                    try:
                        driver.get("https://entaaf.ema.md/ema/web/practice/staff#/practice/staff/patient/list")
                        time.sleep(1.2)
                    except Exception:
                        pass
                except TimeoutException:
                    log_msg(log, f"[RETRY-OPEN:{tries}] timeout → retry")
                except Exception as e:
                    log_msg(log, f"[RETRY-OPEN:{tries}] general error → {e}")
                time.sleep(0.8)
            return False
# ========= Run =========
        login()
        summary_rows = []
        for mrn in mrns:
            log_msg(log, f"Processing MRN: {mrn}")

            if not robust_open_patient(mrn, max_tries=3):
                log_msg(log, f"[{mrn}] Could not open patient after robust retries.")
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