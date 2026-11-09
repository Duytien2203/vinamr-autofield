Set-Location $PSScriptRoot

Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "  VINAMR AUTOFIELD - HE THONG QUAN LY QUOTA O TO" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "Dang mo trinh duyet tai http://localhost:8000..." -ForegroundColor Yellow

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$pythonPath = "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"

if (Test-Path $chromePath) {
    Start-Process $chromePath "http://127.0.0.1:8000"
} elseif (Test-Path $edgePath) {
    Start-Process $edgePath "http://127.0.0.1:8000"
}

if (Test-Path $pythonPath) {
    & $pythonPath server.py
} else {
    python server.py
}
