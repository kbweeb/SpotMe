$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendCommand = "Set-Location '$root'; if (Test-Path '.\.venv\Scripts\Activate.ps1') { . .\.venv\Scripts\Activate.ps1 }; python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010"
$frontendCommand = "Set-Location '$root\frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand | Out-Null
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand | Out-Null

Write-Host "Started GymBuddy services:"
Write-Host "  Backend:  http://127.0.0.1:8010"
Write-Host "  Frontend: http://127.0.0.1:5173"
