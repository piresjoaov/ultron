$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$releaseExe = Join-Path $frontendRoot "src-tauri\target\release\ultron.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$appFolder = Join-Path $desktop "Ultron"
$buildStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$desktopExe = Join-Path $appFolder "Ultron-$buildStamp.exe"
$launcher = Join-Path $appFolder "Start-Ultron.ps1"
$shortcut = Join-Path $desktop "Ultron.lnk"

Write-Host "Building the production desktop application..."
Push-Location $frontendRoot
try {
    npm run tauri:build
    if ($LASTEXITCODE -ne 0) {
        throw "Tauri production build failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

if (-not (Test-Path $releaseExe)) {
    throw "Tauri release executable was not found at $releaseExe"
}

New-Item -ItemType Directory -Path $appFolder -Force | Out-Null
Copy-Item $releaseExe $desktopExe -Force

@"
`$ErrorActionPreference = "Stop"
`$repoRoot = '$repoRoot'
`$python = Join-Path `$repoRoot 'backend\.venv\Scripts\python.exe'
`$api = Join-Path `$repoRoot 'backend\src'
`$exe = Join-Path `$PSScriptRoot 'Ultron-$buildStamp.exe'

if (-not (Test-Path `$python)) {
    [System.Windows.Forms.MessageBox]::Show('Backend Python environment not found. Run backend setup first.', 'Ultron') | Out-Null
    exit 1
}

`$health = `$false
try {
    Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 1 -UseBasicParsing | Out-Null
    `$health = `$true
} catch { }

if (-not `$health) {
    Start-Process -FilePath `$python -WorkingDirectory `$repoRoot -ArgumentList @('-m', 'uvicorn', 'api:app', '--app-dir', `$api, '--port', '8000') -WindowStyle Hidden
}
Start-Process -FilePath `$exe -WorkingDirectory `$PSScriptRoot
"@ | Set-Content -Path $launcher -Encoding UTF8

$ws = New-Object -ComObject WScript.Shell
$link = $ws.CreateShortcut($shortcut)
$link.TargetPath = "powershell.exe"
$link.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcher`""
$link.WorkingDirectory = $appFolder
$link.Description = "Ultron local STEM tutor"
$link.IconLocation = "$desktopExe,0"
$link.Save()

Write-Host "Production app copied to $appFolder"
Write-Host "Desktop shortcut created at $shortcut"
