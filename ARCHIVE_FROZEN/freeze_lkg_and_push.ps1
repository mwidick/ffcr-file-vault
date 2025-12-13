# freeze_lkg_and_push.ps1
# Creates a timestamped LKG freeze record and optionally commits/pushes to GitHub.

$ErrorActionPreference = "Stop"

# --- Paths (locked to your environment) ---
$MRN_ROOT   = "C:\FFCR_Project\Counselear Project\MRN_Refresher"
$FROZEN_DIR = Join-Path $MRN_ROOT "ARCHIVE_FROZEN"

$WRAPPER = Join-Path $MRN_ROOT "counselear_visit_refresher_TEST_v1d.py"
$CORE    = Join-Path $MRN_ROOT "counselear_visit_refresher_core_v2_GoldCore.py"

# --- Ensure folders/files exist ---
if (!(Test-Path $FROZEN_DIR)) { New-Item -ItemType Directory -Path $FROZEN_DIR | Out-Null }
if (!(Test-Path $WRAPPER)) { throw "Missing wrapper file: $WRAPPER" }
if (!(Test-Path $CORE))    { throw "Missing core file:    $CORE" }

# --- Compute hashes ---
$hWrapper = (Get-FileHash $WRAPPER -Algorithm SHA256).Hash
$hCore    = (Get-FileHash $CORE    -Algorithm SHA256).Hash

# --- Create freeze record ---
$ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$outFile = Join-Path $FROZEN_DIR "FFCR_LKG_FREEZE_$ts.txt"

@"
FFCR CounselEar LKG Freeze Record (BWMoC-CounselEar-Laws-V1)
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

LKG WRAPPER
  File:  $WRAPPER
  SHA256: $hWrapper

LKG CORE (GoldCore)
  File:  $CORE
  SHA256: $hCore

Locked behavior summary:
- Wrapper: Patient Search -> SearchResults RadGrid row double-click -> Patient chart -> Visits tab -> Save(id ctl01_btnSubmit) -> Back(id ctl01_btnCancel)
- Core:    Appts/Visits -> open visit -> Save -> Back -> repeat (VISIT-UPDATE when webhook config is correct)

Frozen selectors:
- Save id: ctl01_btnSubmit | XPath: //input[@type='submit' and @value='Save']
- Back id: ctl01_btnCancel | XPath: //input[@type='button' and contains(@value, 'Back - Patient Administration')]
- Visits header: //td[normalize-space()='Visits']
- Visits rows:   ./ancestor::table[1]/following-sibling::table[1]

Environment (do not change):
- Chrome:      C:\FFCR_Project\Pair E\chrome-win64\chrome.exe
- ChromeDriver:C:\FFCR_Project\Pair E\chromedriver-win64\chromedriver.exe
"@ | Set-Content -Path $outFile -Encoding UTF8

Write-Host "`n[OK] Freeze record saved:" -ForegroundColor Green
Write-Host "     $outFile`n"

# --- Optional GitHub push ---
# This will only work if the freeze file is inside a Git repo and you already have a configured remote + auth.
# If not, it will print a warning and exit cleanly.
try {
    Push-Location $FROZEN_DIR

    $isRepo = Test-Path (Join-Path (git rev-parse --show-toplevel 2>$null) ".git") 2>$null
    if (-not $isRepo) {
        Write-Host "[WARN] No git repo detected for this folder. Skipping git commit/push." -ForegroundColor Yellow
        Pop-Location
        exit 0
    }

    $top = (git rev-parse --show-toplevel).Trim()
    Pop-Location
    Push-Location $top

    # Add ONLY the new freeze record
    git add -- "$outFile"

    $msg = "Freeze LKG CounselEar core+wrapper ($ts)"
    git commit -m "$msg" | Out-Null

    Write-Host "[OK] Committed freeze record. Attempting push..." -ForegroundColor Green
    git push

    Write-Host "[OK] Pushed to remote." -ForegroundColor Green
    Pop-Location
}
catch {
    try { Pop-Location } catch {}
    Write-Host "`n[WARN] Git commit/push step did not complete." -ForegroundColor Yellow
    Write-Host "       Error: $($_.Exception.Message)"
    Write-Host "       The freeze record is still saved locally at:"
    Write-Host "       $outFile`n"
}
