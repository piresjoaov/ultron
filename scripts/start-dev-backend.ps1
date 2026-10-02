$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
$api = Join-Path $repoRoot "backend\src"

$owners = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
foreach ($owner in $owners) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($owner.OwningProcess)"
    $command = [string]$process.CommandLine
    if ($command -like "*$repoRoot*backend*uvicorn*api:app*") {
        Write-Host "Stopping the existing Ultron backend on port 8000..."
        Stop-Process -Id $owner.OwningProcess -Force
    } else {
        throw "Port 8000 is already used by another process (PID $($owner.OwningProcess)). Stop it or set up a different API port before starting Ultron."
    }
}

& $python -m uvicorn api:app --app-dir $api --reload --port 8000
exit $LASTEXITCODE
