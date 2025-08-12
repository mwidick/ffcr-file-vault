@echo off
setlocal
cd /d "%~dp0"
set "PY_CMD=python"
where %PY_CMD% >nul 2>&1 || set "PY_CMD=py -3"
echo Using %PY_CMD%
%PY_CMD% -X dev -u "FASTALL_OperativeOnly_Pagination_MARKED_patched_v2d.py"
echo ExitCode=%ERRORLEVEL%
pause
endlocal
