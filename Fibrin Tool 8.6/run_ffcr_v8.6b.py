__version__ = "8.6b"

import os
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import csv
import re
import shutil
from datetime import datetime

INCOMING_DIR = 'H:/Shared drives/FFCR/Incoming Cases'
RESULTS_DIR = 'H:/Shared drives/FFCR/Processed Results'
ARCHIVE_ROOT = 'H:/Shared drives/FFCR/Processed Archive'
SPREADSHEET = os.path.join(RESULTS_DIR, 'FFCR_master_spreadsheet.csv')
MISSING_REPORT = os.path.join(RESULTS_DIR, 'FFCR_missing_fields.csv')
LOG_FILE = os.path.join(RESULTS_DIR, 'ffcr_processing_log.txt')

FIELDS = [
    'MRN', 'DOB', 'Procedure Date', 'Side', 'Pre-op Diagnosis', 'Post-op Diagnosis',
    'Audiometry Pre', 'Audiometry Post', 'Perforation Size', 'Foam Mention', 'Images Present'
]

def log(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

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

def extract_fields(text, image_files):
    lines = text.splitlines()
    audit_log = {}
    def find(pattern, label, flags=0):
        for line in lines:
            if re.search(pattern, line, flags):
                audit_log[label] = line.strip()
                match = re.search(pattern, line, flags)
                return match.group(1).strip() if match else ''
        audit_log[label] = ''
        return ''

    mrn = find(r'MRN[:\s]*?(\d{6,})', 'MRN')
    dob = find(r'DOB[:\s]*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'DOB')
    procedure_date = find(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'Procedure Date')
    side = find(r'\b(left|right|bilateral)\b', 'Side', re.IGNORECASE)
    pre_dx = find(r'Pre[- ]?op(?:erative)? Diagnosis[:\s]*([^\n]+)', 'Pre-op Diagnosis', re.IGNORECASE)
    post_dx = find(r'Post[- ]?op(?:erative)? Diagnosis[:\s]*([^\n]+)', 'Post-op Diagnosis', re.IGNORECASE)
    perforation_size = find(r'\b(small|medium|large)\b(?=.*perforation)', 'Perforation Size', re.IGNORECASE)

    foam_line = ''
    for line in lines:
        if 'fibrin' in line.lower() or 'foam' in line.lower():
            foam_line = line.strip()
            audit_log['Foam Mention'] = foam_line
            break
    if not foam_line:
        audit_log['Foam Mention'] = ''

    pre_audio = ''
    post_audio = ''
    for line in lines:
        if '500' in line and 'dB' in line:
            if not pre_audio:
                pre_audio = line.strip()
            elif not post_audio:
                post_audio = line.strip()
    audit_log['Audiometry Pre'] = pre_audio
    audit_log['Audiometry Post'] = post_audio

    image_presence = 'Yes' if image_files else 'No'
    audit_log['Images Present'] = ', '.join(image_files) if image_files else ''

    values = {
        'MRN': mrn,
        'DOB': dob,
        'Procedure Date': procedure_date,
        'Side': side,
        'Pre-op Diagnosis': pre_dx,
        'Post-op Diagnosis': post_dx,
        'Audiometry Pre': pre_audio,
        'Audiometry Post': post_audio,
        'Perforation Size': perforation_size,
        'Foam Mention': foam_line,
        'Images Present': image_presence
    }

    missing_fields = [k for k, v in values.items() if not v.strip()]
    return values, audit_log, missing_fields

def write_html_summary(fields, missing, path):
    html = "<html><head><style>"
    html += "body { font-family: Arial; } h2 { color: #2c3e50; } table { border-collapse: collapse; width: 100%; margin-top: 10px; } td, th { border: 1px solid #ddd; padding: 8px; } th { background-color: #f2f2f2; } .missing { background-color: #ffe6e6; }"
    html += "</style></head><body><h2>Case Summary</h2><table>"
    for k, v in fields.items():
        missing_class = " class='missing'" if k in missing else ""
        html += f"<tr><th>{k}</th><td{missing_class}>{v if v else '[Missing]'}</td></tr>"
    html += f"<tr><td colspan='2'><strong>Missing Fields:</strong> {', '.join(missing) if missing else 'None'}</td></tr>"
    html += "</table></body></html>"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

def process_case_folder(folder_path):
    folder_name = os.path.basename(folder_path)
    if already_processed(folder_name):
        log(f"Skipping already archived case: {folder_name}")
        return

    summary_path = os.path.join(folder_path, 'case_summary.txt')
    html_path = os.path.join(folder_path, 'case_summary.html')
    fulltext_path = os.path.join(folder_path, 'full_text.txt')
    audit_path = os.path.join(folder_path, 'raw_hits_audit.txt')
    all_text = ''
    image_files = []

    for file in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file)
        if file.lower().endswith('.pdf'):
            text = ocr_pdf(full_path)
            all_text += f"\n--- {file} ---\n" + text
        elif file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(file)

    with open(fulltext_path, 'w', encoding='utf-8') as f:
        f.write(all_text)

    fields, audit, missing = extract_fields(all_text, image_files)

    with open(summary_path, 'w', encoding='utf-8') as f:
        for k, v in fields.items():
            f.write(f"{k}: {v}\n")
        f.write(f"\n[Missing Fields]: {', '.join(missing) if missing else 'None'}\n")

    write_html_summary(fields, missing, html_path)

    with open(audit_path, 'w', encoding='utf-8') as f:
        for k, v in audit.items():
            f.write(f"{k}: {v}\n")

    if not os.path.exists(SPREADSHEET):
        with open(SPREADSHEET, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

    with open(SPREADSHEET, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(fields)

    if not os.path.exists(MISSING_REPORT):
        with open(MISSING_REPORT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Case Folder', 'Missing Fields'])

    with open(MISSING_REPORT, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([folder_name, ', '.join(missing)])

    today = datetime.today().strftime('%Y-%m-%d')
    archive_path = os.path.join(ARCHIVE_ROOT, today)
    os.makedirs(archive_path, exist_ok=True)
    shutil.move(folder_path, os.path.join(archive_path, folder_name))
    log(f"Processed and archived case: {folder_name}")

if __name__ == '__main__':
    log("FFCR v8.6b started")
    for folder in os.listdir(INCOMING_DIR):
        folder_path = os.path.join(INCOMING_DIR, folder)
        if os.path.isdir(folder_path):
            process_case_folder(folder_path)
    log("FFCR v8.6b completed")
