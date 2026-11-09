@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo =============================================================
echo   VINAMR Field - Khởi Động Bản Streamlit (Cổng 8501)
echo =============================================================
set PYTHON_EXE=C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe

start "" http://localhost:8501

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m streamlit run app.py --server.port 8501
) else (
    python -m streamlit run app.py --server.port 8501
)
pause
