# FFCR Legacy Parser Tool (run_ffcr_local.py)

## 📌 Project Overview

The **FFCR Legacy Parser** is a standalone post-processing script designed to read local FFCR visit activity logs and extract structured information for analysis. This tool is a key component of the legacy FFCR pipeline and works independently of the ModMed extraction modules. Its primary function is to ingest patient visit data from already-downloaded PDFs or log files and output a clean, analyzable report.

---

## ⚙️ How It Works

- The script reads patient-specific data from a designated local input directory.
- Parses key-value pairs from structured text/PDF output (from Patient Activity or Attachments downloads).
- Compiles visit metadata, such as:
  - MRN
  - Visit Date
  - Provider Name
  - Visit Type or Note Presence
- Outputs results as an Excel or CSV file for downstream integration.

---

## 📁 File Structure

```
FFCR tool local/
├── run_ffcr_local.py         # Legacy parser script
├── requirements.txt          # Python dependencies
└── README.md                 # You’re reading it!
```

---

## 🚀 Quickstart

1. Clone the GitHub folder or download the ZIP.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Place the FFCR log files or parsed visit text files into the `input/` directory.
4. Run the parser:
   ```bash
   python run_ffcr_local.py
   ```
5. Output will be generated under `output/ffcr_summary.xlsx` by default.

---

## 📦 Output Format

The final Excel or CSV output includes columns like:
- `MRN`
- `Date`
- `Visit Type`
- `Visit Status`
- `Provider`

All extracted from structured data based on filename matching and embedded text parsing logic.

---

## 🛡️ Warnings & Caveats

- This tool assumes that the log or PDF data is well-structured and properly downloaded.
- Not compatible with placeholder or failed PDF captures.
- Null bytes or malformed encodings will halt parsing unless explicitly handled.
- Works best with text-based PDFs or pre-processed text logs extracted using `PyMuPDF`, `pdfminer`, or equivalent.

---

## 📌 Version Notes

- Current version: `v1.0`
- Last updated: July 2025
- Python version: 3.10+
- Tested on Windows 10+ with FFCR standard directory layout

---

## 🌱 Planned Enhancements

- Add support for multi-visit comparison summaries
- Detect duplicate entries
- Expand parsing to include audiometric data
- Integration with CouncilEar

---

## 🧠 FFCR Philosophy

This tool adheres to the Widick Commandments: no placeholder corruption, no silent failures, and no unlogged results. Every patient log deserves its own meaningful cell in Excel history.

---

For questions or improvements, contact: **Dr. Mark Widick** | mwidick@mac.com
