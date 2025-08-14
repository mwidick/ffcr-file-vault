# FFCR ModMed Operative Report Downloader (Baseline)

**Purpose**  
Automate retrieval of *Operative Report* PDFs from ModMed (ENT & Allergy Associates of FL) for a list of MRNs.  
Pagination is set to 100 rows; if the standard HTTP download path saves 0 files, a **hard‑click fallback** clicks the `/fileattachment/*.pdf` links and forces Chrome to save **silently** into the correct MRN folder.

---

## What’s in this folder

- `FASTALL_OperativeOnly_Pagination_MARKED_patched(4)_MARKED_HC.py`  
  Baseline working script (marker present; hard‑click fallback included).

- `FASTALL_OperativeOnly_Pagination_MARKED_patched(4)_MARKED_HC_DLAUTO_FIXED.py`  
  Same baseline with **DevTools download enforcement** (`Page.setDownloadBehavior`) so fallback saves **without** a Save As dialog into:
  `C:\FFCR_Project\Attachments_Multiple\Activity_PDF_Output\<MRN>`.

- `Run_FFCR_MARKED_HC_DLAUTO_FIXED.bat`  
  Double‑click runner that keeps the window open (`pause`).

- `generate_run_bat.py`  
  Writes a checksum‑enforced launcher for a given script (optional).

- `ffcr_modmed_patcher.py`  
  Minimal patcher that appends the fallback block and preserves the frozen‑section checksum (optional).

- `modmed_patch4_run_log.txt` (optional)  
  Sample run log showing `[DL] Downloads allowed to: ...` and `OP-SAVED via hardclick:` entries.

- `.gitignore`  
  Prevents committing credentials, MRN lists, output PDFs, and temp files.

---

## Quick Start (Recommended DLAUTO build)

1. Put these beside the Excel files in `C:\FFCR_Project\Attachments_Multiple\`:
   - `FASTALL_OperativeOnly_Pagination_MARKED_patched(4)_MARKED_HC_DLAUTO_FIXED.py`
   - `Run_FFCR_MARKED_HC_DLAUTO_FIXED.bat`
   - `counselear_credentials.xlsx` *(NOT in GitHub)*
   - `counselear_patients.xlsx` *(NOT in GitHub)*

2. Open `counselear_patients.xlsx` → one MRN per line.

3. Double‑click `Run_FFCR_MARKED_HC_DLAUTO_FIXED.bat`.

**What to expect in the log**  
```
[VIEWBY] Current setting: 100
[DL] Downloads allowed to: C:\FFCR_Project\Attachments_Multiple\Activity_PDF_Output\<MRN>
[FFCR-DBG3] Hardclick candidates: N
[FFCR-DBG3] OP-SAVED via hardclick: EMA_..._Operative_Report[_SCAN].pdf
[MM0000xxxxx] Saved <N> operative PDFs.
```

---

## Output
Per‑MRN subfolders under:
```
C:\FFCR_Project\Attachments_Multiple\Activity_PDF_Output\<MRN>\*.pdf
```

---

## Notes & Safety Rails
- The **frozen block** is unchanged; patcher preserves its checksum for auditing.
- Chrome DevTools `Page.setDownloadBehavior` is used to force silent downloads for the fallback path.
- If UI clicks open a new tab, the script closes it and returns to the base tab.
- To re‑apply the fallback into a new “GoldCore”, keep the `# FFCR_POSTPASS_HOOK` marker in your base and run the patcher.

---

## Troubleshooting
- **Save As dialog appears** → ensure you’re running the **DLAUTO** build; confirm `[DL] Downloads allowed to: ...` appears per MRN.
- **Candidates found but 0 saved** → increase fallback wait (e.g., 90s) or widen tokens (`operative`, `op_report`, `surgical_report`, `procedure`, `opnote`, `op note`).  
- **Files landing in wrong folder** → verify the log path printed by `[DL] Downloads allowed to:` matches the MRN folder.

---

© 2025 FFCR. Internal automation script for data retrieval.
