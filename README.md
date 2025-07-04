# FFCR Legacy Parser v1

This script processes folders of scanned surgical reports using OCR to extract structured data related to tympanoplasty and fibrin foam usage.

## 🧩 Components

- `run_ffcr_local.py` – Main script for parsing PDF files using OCR and regex.
- `README.md` – Project overview and usage instructions.
- `requirements.txt` – Dependencies for running the script.

## 📂 Input Folder Structure

Expected input folder:
```
H:/Shared drives/FFCR/Incoming Cases/
    ├── Case1/
    │     ├── file1.pdf
    │     ├── image1.jpg
    ├── Case2/
          ├── ...
```

Each folder contains case-specific documents and images.

## 📤 Output

- `full_text.txt`: Entire OCR output.
- `case_summary.txt`: Key fields extracted.
- `raw_hits_audit.txt`: Regex match audit log.
- `FFCR_master_spreadsheet.csv`: Appended results for all cases.

## 🧪 Requirements

- Python 3.10+
- Tesseract OCR
- PyMuPDF
- Pillow
- pytesseract

Install dependencies with:
```bash
pip install -r requirements.txt
```

Tesseract must be installed and in your system path:
https://github.com/tesseract-ocr/tesseract

## 🚀 Run

```bash
python run_ffcr_local.py
```

Ensure that `INCOMING_DIR` and `RESULTS_DIR` are configured properly inside the script.