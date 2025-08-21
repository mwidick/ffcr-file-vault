@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "C:\FFCR_Project\Attachments_Multiple\"
set "PY=python"
where python >nul 2>nul || set "PY=py -3"
set "SCRIPT=FASTALL_OperativeOnly_Pagination_PATCH4c_HARDGET_FIX4_MODv2.py"
set "LOG=modmed_patch4_run_log.txt"
rem Optional: set FFCR_MIN_DATE=2016-01-01
rem Optional: set FFCR_MAX_AGE_YEARS=9
rem Optional: set FFCR_AGGRESSIVE=1
rem Optional: set FFCR_MRN_DATE_CSV=mrn_procedure_dates.csv
echo === FFCR FIX4 MODv2 (Dual-column matching) ===
echo Using: %SCRIPT%
"%PY%" "%SCRIPT%" 1>>"%LOG%" 2>&1
set "EC=%ERRORLEVEL%"
echo [DONE] Exit code: %EC%
pause
exit /b %EC%