@echo off
setlocal EnableExtensions EnableDelayedExpansion

set PY=python
where python >nul 2>&1 || set PY=py -3

set SCRIPT="FASTALL_OperativeOnly_Pagination_MARKED_patched(4)_MARKED_HC_UNCHANGED.py"

echo [RUN] Launching %SCRIPT% ...
%PY% %SCRIPT%
