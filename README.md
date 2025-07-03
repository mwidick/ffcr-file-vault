
# FFCR Legacy Parser v1

This is the original data parsing module used in FFCR to analyze operative reports extracted from ModMed.

## Features

- Uses OCR (Tesseract via PyMuPDF) to read PDF content
- Extracts:
  - Medical Record Number (MRN)
  - Date of Birth (DOB)
  - Date of Procedure
  - Operative Side
  - Diagnoses
  - Fibrin/Foam technique mentions
  - Audiometric results (pre/post)
- Generates:
  - case_summary.txt
  - raw_hits_audit.txt
  - full_text.txt
  - FFCR_master_spreadsheet.csv (accumulative)

## Launch Instructions

Double-click `launch_ffcr.bat` or run `run_ffcr_local.py` in a Python 3.11+ environment with Tesseract and PyMuPDF installed.

## Purpose

Used for retrospective analysis of tympanoplasty surgical outcomes and audiological improvement in FFCR cases.

---
Dr. Mark Widick
FFCR Project
