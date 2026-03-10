$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-PortOwner {
    param([int]$Port)
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        if (-not $connection) {
            return $null
        }
        $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        if ($process) {
            return "$($process.ProcessName) (PID $($process.Id))"
        }
        return "PID $($connection.OwningProcess)"
    } catch {
        return $null
    }
}

$backendOwner = Get-PortOwner -Port 8010
$frontendOwner = Get-PortOwner -Port 5173

if ($backendOwner -or $frontendOwner) {
    Write-Host "Cannot start GymBuddy because required ports are already in use:" -ForegroundColor Red
    if ($backendOwner) {
        Write-Host "  - 8010: $backendOwner"
    }
    if ($frontendOwner) {
        Write-Host "  - 5173: $frontendOwner"
    }
    Write-Host "Stop those processes, then run .\\run_project.ps1 again." -ForegroundColor Yellow
    exit 1
}

$backendCommand = "Set-Location '$root'; if (Test-Path '.\.venv\Scripts\Activate.ps1') { . .\.venv\Scripts\Activate.ps1 }; python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010"
$frontendCommand = "Set-Location '$root\frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand | Out-Null
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand | Out-Null

Write-Host "Started GymBuddy services:"
Write-Host "  Backend:  http://127.0.0.1:8010"
Write-Host "  Frontend: http://127.0.0.1:5173"
