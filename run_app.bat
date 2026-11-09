@echo off
cd /d "%~dp0"

echo =============================================================
echo   VINAMR AUTOFIELD - HE THONG QUAN LY QUOTA O TO
echo =============================================================
echo May chu web dang chay tai:
echo   --> http://localhost:8000
echo   --> http://127.0.0.1:8000
echo =============================================================

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://127.0.0.1:8000"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "http://127.0.0.1:8000"
)

"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" server.py

pause
