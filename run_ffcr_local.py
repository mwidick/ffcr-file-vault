import os
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import csv
import re

INCOMING_DIR = 'H:/Shared drives/FFCR/Incoming Cases'
RESULTS_DIR = 'H:/Shared drives/FFCR/Processed Results'
SPREADSHEET = os.path.join(RESULTS_DIR, 'FFCR_master_spreadsheet.csv')

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

    return {
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
    }, audit_log

def process_case_folder(folder_path):
    summary_path = os.path.join(folder_path, 'case_summary.txt')
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

    fields, audit = extract_fields(all_text, image_files)

    with open(summary_path, 'w', encoding='utf-8') as f:
        for k, v in fields.items():
            f.write(f"{k}: {v}\n")

    with open(audit_path, 'w', encoding='utf-8') as f:
        for k, v in audit.items():
            f.write(f"{k}: {v}\n")

    if not os.path.exists(SPREADSHEET):
        with open(SPREADSHEET, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields.keys())
            writer.writeheader()

    with open(SPREADSHEET, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields.keys())
        writer.writerow(fields)

if __name__ == '__main__':
    for folder in os.listdir(INCOMING_DIR):
        case_path = os.path.join(INCOMING_DIR, folder)
        if os.path.isdir(case_path):
            print(f"Processing {folder}...")
            process_case_folder(case_path)
