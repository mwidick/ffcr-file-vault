
import os
import zipfile
import pytesseract
import fitz
from PIL import Image
from datetime import datetime
import csv
import re

KEYWORDS = ["fibrin", "foam", "fibrin foam", "thrombin", "perforation", "graft", "cholesteatoma", "healed", "closure", "cartilage"]

def detect_drive_letter():
    for letter in ["H:", "G:"]:
        if os.path.exists(os.path.join(letter, "Shared drives", "FFCR")):
            return letter
    return None

def extract_text_from_pdf(path):
    try:
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        return f"[PDF parse failed: {e}]"

def extract_text_from_image(path):
    try:
        return pytesseract.image_to_string(Image.open(path))
    except Exception as e:
        return f"[OCR failed: {e}]"

def find_keywords(text):
    hits = []
    for kw in KEYWORDS:
        if kw.lower() in text.lower():
            lines = [line.strip() for line in text.splitlines() if kw.lower() in line.lower()]
            hits.extend(lines)
    return hits if hits else ["None found"]

def extract_fields(text):
    mrn = re.search(r'MRN[:\s]+(\w+)', text)
    dob = re.search(r'DOB[:\s]+(\d{2}/\d{2}/\d{4})', text)
    name = re.search(r'Patient Name[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
    pta_right = re.search(r'PTA.*?Right.*?(\d+\.?\d*)', text)
    pta_left = re.search(r'PTA.*?Left.*?(\d+\.?\d*)', text)
    return {
        "MRN": mrn.group(1) if mrn else "Not found",
        "DOB": dob.group(1) if dob else "Not found",
        "Name": name.group(1) if name else "Not found",
        "PTA Right": pta_right.group(1) if pta_right else "Not found",
        "PTA Left": pta_left.group(1) if pta_left else "Not found"
    }

def process_case(case_path, output_path, backup_base, csv_writer):
    log = []
    full_text = ""
    log.append(f"📁 Processing case: {os.path.basename(case_path)}")

    for root, _, files in os.walk(case_path):
        for f in files:
            path = os.path.join(root, f)
            if f.lower().endswith(".pdf"):
                log.append(f"🔍 OCR PDF: {f}")
                text = extract_text_from_pdf(path)
                full_text += "\n" + text
            elif f.lower().endswith((".png", ".jpg", ".jpeg")):
                log.append(f"🔍 OCR Image: {f}")
                text = extract_text_from_image(path)
                full_text += "\n" + text
            else:
                log.append(f"⏩ Skipped (not PDF/image): {f}")

    os.makedirs(output_path, exist_ok=True)
    backup_path = os.path.join(backup_base, os.path.basename(case_path))
    os.makedirs(backup_path, exist_ok=True)

    with open(os.path.join(output_path, "full_text.txt"), "w", encoding="utf-8") as ft:
        ft.write(full_text)
    with open(os.path.join(backup_path, "full_text.txt"), "w", encoding="utf-8") as bft:
        bft.write(full_text)

    keywords = find_keywords(full_text)
    with open(os.path.join(output_path, "case_summary.txt"), "w", encoding="utf-8") as cs:
        cs.write(f"Case: {os.path.basename(case_path)}\nReviewed: {datetime.now()}\n")
        cs.write("\n--- Keyword Hits ---\n" + "\n".join(keywords))
    with open(os.path.join(backup_path, "case_summary.txt"), "w", encoding="utf-8") as bcs:
        bcs.write(f"Case: {os.path.basename(case_path)}\nReviewed: {datetime.now()}\n")
        bcs.write("\n--- Keyword Hits ---\n" + "\n".join(keywords))

    fields = extract_fields(full_text)
    csv_writer.writerow({"Case": os.path.basename(case_path), **fields})

    with open(os.path.join(output_path, "log.txt"), "w", encoding="utf-8") as logf:
        logf.write("\n".join(log))
    with open(os.path.join(backup_path, "log.txt"), "w", encoding="utf-8") as blogf:
        blogf.write("\n".join(log))

def run():
    print("🩺 Fibrin Foam Chart Review Tool v8.3")
    drive = detect_drive_letter()
    if not drive:
        print("❌ Shared drive FFCR not found.")
        return

    incoming = os.path.join(drive, "Shared drives", "FFCR", "Incoming Cases")
    results = os.path.join(drive, "Shared drives", "FFCR", "Processed Results")
    backups = os.path.join(drive, "Shared drives", "FFCR", "Backups", "Processed Results")
    spreadsheet = os.path.join(results, "fibrin_case_summary.csv")

    print(f"✅ FFCR detected at {drive}")
    print(f"🔍 Scanning: {incoming}")

    fieldnames = ["Case", "MRN", "DOB", "Name", "PTA Right", "PTA Left"]
    with open(spreadsheet, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:
            writer.writeheader()
        for case in os.listdir(incoming):
            cpath = os.path.join(incoming, case)
            if os.path.isdir(cpath):
                outpath = os.path.join(results, case)
                print(f"🚀 Processing: {case}")
                process_case(cpath, outpath, backups, writer)

    print("✅ v8.3 complete.")

if __name__ == "__main__":
    run()
