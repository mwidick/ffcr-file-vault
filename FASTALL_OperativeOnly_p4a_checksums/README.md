# ModMed Operative-Only Extractor

This repository contains the working FASTALL p4a script configured for extracting Operative Reports from ModMed Attachments.

## Files
- Python script (`FASTALL_v1-p4a_ActivityPDFOutput_NODEDUP_verified.py`) — main extractor
- Batch file (`run_FASTALL_verified.bat`) — launches the script
- Example spreadsheets — placeholder patient list and credentials

## Usage
1. Place real patient list and credentials in the Excel files.
2. Run the `.bat` file.
3. Extracted PDFs will be saved in the configured output folder.

*This version contains frozen logic from the gold-standard extractor and modular changes for Operative-Only filtering.*
