@echo off
echo ==========================================
echo      FFCR MODMED MASTER SCRIPT LAUNCHER
echo ==========================================
echo.
echo Choose the version to run:
echo [A] Attachments-first (v22.0i_a)
echo [B] Patient Activity-first (v22.0i_b)
echo [G] GoldCore baseline (v22.0i_goldcore)
echo.

set /p choice="Enter your choice (A/B/G): "
if /i "%choice%"=="A" (
    python run_ffcr_modmed_v22_0i_a.py
) else if /i "%choice%"=="B" (
    python run_ffcr_modmed_v22_0i_b.py
) else if /i "%choice%"=="G" (
    python run_ffcr_modmed_v22_0i_goldcore.py
) else (
    echo Invalid choice.
)
pause