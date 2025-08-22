
Fibrin Chart Review Tool v8.2

Instructions:
1. Extract to: C:\Fibrin Tool 8.2
2. Double-click run_fibrin_review_v8_2.bat
   or run from terminal with:
   cd "C:\Fibrin Tool 8.2"
   python fibrin_review_chunked_v8_2.py

What It Does:
- Scans H:/ or G:/Shared drives/FFCR/Incoming Cases
- Unzips .zip folders
- OCRs all PDFs and images
- Extracts keywords and fields (MRN, DOB, etc.)
- Generates per-case log.txt, case_summary.txt, full_text.txt
- Updates fibrin_case_summary.csv
- Backs up each case to FFCR/Backups/Processed Results
