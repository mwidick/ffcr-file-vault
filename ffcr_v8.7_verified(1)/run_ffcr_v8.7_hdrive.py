# BASELINE: Widick v8.6d
# HASH: 6804ccf018053265b445555bba8ebb31c33c997747e69c6033aa282134df1e81

# FFCR v8.5c-hdrive VERIFIED FULL SCRIPT
# ✅ Includes vault backup + raw_hits_audit.txt logging
# ✅ Built on top of working v8.4c logic

import os
import pytesseract
import fitz
from PIL import Image
import csv
import re
import shutil
from datetime import datetime

INCOMING_DIR = 'H:/Shared drives/FFCR/Incoming Cases'
VAULT_DIR = 'H:/Shared drives/FFCR/VAULT'
RESULTS_DIR = 'H:/Shared drives/FFCR/Processed Results'
ARCHIVE_ROOT = 'H:/Shared drives/FFCR/Processed Archive'
SPREADSHEET = os.path.join(RESULTS_DIR, 'FFCR_master_spreadsheet.csv')
LOG_FILE = os.path.join(RESULTS_DIR, 'ffcr_processing_log.txt')
AUDIT_LOG = os.path.join(RESULTS_DIR, 'raw_hits_audit.txt')

FIELDS = [
    'MRN', 'DOB', 'Procedure Date', 'Side', 'Pre-op Diagnosis', 'Post-op Diagnosis',
    'Audiometry Pre', 'Audiometry Post', 'Perforation Size', 'Foam Mention', 'Images Present'
]

def log(msg):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def backup_to_vault(folder_name, folder_path):
    vault_path = os.path.join(VAULT_DIR, folder_name)
    if not os.path.exists(vault_path):
        shutil.copytree(folder_path, vault_path)

def already_processed(folder):
    archive_date = datetime.today().strftime('%Y-%m-%d')
    archive_path = os.path.join(ARCHIVE_ROOT, archive_date, folder)
    return os.path.exists(archive_path)

def ocr_pdf(path):
    text = ''
    doc = fitz.open(path)
    for page_num in range(len(doc)):
        pix = doc.load_page(page_num).get_pixmap(dpi=300)
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        text += pytesseract.image_to_string(img) + '\n'
    return text

def extract_fields(text, image_files, folder_name):
    lines = text.splitlines()
    values = {}
    matched_lines = []

    def find(pattern, label, flags=0):
        for line in lines:
            if re.search(pattern, line, flags):
                match = re.search(pattern, line, flags)
                if match:
                    matched_lines.append(f"{label}: {line.strip()}")
                    return match.group(1).strip()
        matched_lines.append(f"{label}: NOT FOUND")
        return ''

    values['MRN'] = find(r'MRN[:\s]*?(\d{6,})', 'MRN')
    values['DOB'] = find(r'DOB[:\s]*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'DOB')
    values['Procedure Date'] = find(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'Procedure Date')
    values['Side'] = find(r'\b(left|right|bilateral)\b', 'Side', re.IGNORECASE)
    values['Pre-op Diagnosis'] = find(r'Pre[- ]?op(?:erative)? Diagnosis[:\s]*([^\n]+)', 'Pre-op Diagnosis', re.IGNORECASE)
    values['Post-op Diagnosis'] = find(r'Post[- ]?op(?:erative)? Diagnosis[:\s]*([^\n]+)', 'Post-op Diagnosis', re.IGNORECASE)
    values['Perforation Size'] = find(r'\b(small|medium|large)\b(?=.*perforation)', 'Perforation Size', re.IGNORECASE)

    foam = ''
    for line in lines:
        if 'fibrin' in line.lower() or 'foam' in line.lower():
            foam = line.strip()
            matched_lines.append(f"Foam Mention: {foam}")
            break
    values['Foam Mention'] = foam

    pre_audio = ''
    post_audio = ''
    for line in lines:
        if '500' in line and 'dB' in line:
            if not pre_audio:
                pre_audio = line.strip()
                matched_lines.append(f"Audiometry Pre: {pre_audio}")
            elif not post_audio:
                post_audio = line.strip()
                matched_lines.append(f"Audiometry Post: {post_audio}")
    values['Audiometry Pre'] = pre_audio
    values['Audiometry Post'] = post_audio

    values['Images Present'] = 'Yes' if image_files else 'No'
    
    with open(AUDIT_LOG, 'a', encoding='utf-8') as f:
        f.write(f"--- {folder_name} ---\n")
        for line in matched_lines:
            f.write(f"{line}\n")
        f.write("\n")

    return values

def process_case_folder(folder_path):
    folder_name = os.path.basename(folder_path)
    if already_processed(folder_name):
        log(f"Skipping already archived case: {folder_name}")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_ROOT, exist_ok=True)

    backup_to_vault(folder_name, folder_path)

    full_text = ''
    image_files = []
    for file in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file)
        if file.lower().endswith('.pdf'):
            full_text += f"\n--- {file} ---\n" + ocr_pdf(full_path)
        elif file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(file)

    fields = extract_fields(full_text, image_files, folder_name)

    with open(os.path.join(folder_path, 'case_summary.txt'), 'w', encoding='utf-8') as f:
        for k, v in fields.items():
            f.write(f"{k}: {v}\n")

    if not os.path.exists(SPREADSHEET):
        with open(SPREADSHEET, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

    with open(SPREADSHEET, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(fields)

    today = datetime.today().strftime('%Y-%m-%d')
    archive_path = os.path.join(ARCHIVE_ROOT, today)
    os.makedirs(archive_path, exist_ok=True)
    shutil.move(folder_path, os.path.join(archive_path, folder_name))
    log(f"Processed and archived case: {folder_name}")

if __name__ == '__main__':
    log("FFCR v8.5c started")
    for folder in os.listdir(INCOMING_DIR):
        folder_path = os.path.join(INCOMING_DIR, folder)
        if os.path.isdir(folder_path):
            process_case_folder(folder_path)
    log("FFCR v8.5c completed")

# --- FFCR v8.6d Enhancements: Logging + Print ---
try:
    log_path = r"H:\Shared drives\FFCR\Processed Results\ffcr_processing_log.txt"
    with open(log_path, 'a') as log:
        log.write("[INFO] Log path active.\n")
    print(f"[LOG] Written to: {log_path}")
except Exception as e:
    fallback_path = r"C:\FFCR_Fallback\ffcr_processing_log.txt"
    os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
    with open(fallback_path, 'a') as log:
        log.write(f"[FALLBACK LOG] {str(e)}\n")
    print(f"[FALLBACK] Log written to: {fallback_path}")
