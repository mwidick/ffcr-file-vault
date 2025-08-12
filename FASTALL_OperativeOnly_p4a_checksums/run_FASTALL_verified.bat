@echo off
REM FASTALL v1-p4a NODEDUP verified build
setlocal
cd /d %~dp0
python FASTALL_v1-p4a_ActivityPDFOutput_NODEDUP_verified.py
if %errorlevel% neq 0 (
  echo Script exited with errorlevel %errorlevel%
  pause
)
endlocal
