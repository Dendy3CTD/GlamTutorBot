# UTF-8 in console
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
chcp 65001 | Out-Null

Write-Host "Zapusk GlamTutorBot..." -ForegroundColor Cyan
Write-Host ""

$pythonExe = $null

# 1) Try py, python3, python in PATH (real Python, not Store stub)
foreach ($cmd in @('py', 'python3', 'python')) {
    try {
        $exe = Get-Command $cmd -ErrorAction Stop
        $ver = & $cmd --version 2>&1
        if ($ver -match 'Python (\d+\.\d+)') {
            $pythonExe = $cmd
            Write-Host "OK: $cmd $ver"
            break
        }
    } catch { }
}

# 2) Search standard install paths
if (-not $pythonExe) {
    $paths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
        "C:\Program Files\Python*\python.exe",
        "C:\Python*\python.exe"
    )
    foreach ($pattern in $paths) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($found -and (Test-Path $found.FullName)) {
            $pythonExe = $found.FullName
            Write-Host "OK: $pythonExe"
            break
        }
    }
}

if ($pythonExe) {
    if ($pythonExe -match '\.exe$') {
        & $pythonExe main.py
    } else {
        & $pythonExe main.py
    }
    exit $LASTEXITCODE
}

# Python not found
Write-Host ""
Write-Host "Python ne ustanovlen." -ForegroundColor Red
Write-Host ""
Write-Host "Instrukciya: sm. fail USTANOVKA_PYTHON.md" -ForegroundColor Yellow
Write-Host "  https://www.python.org/downloads/" -ForegroundColor Gray
Write-Host "  Pri ustanovke vklyuchite: Add python.exe to PATH" -ForegroundColor Gray
Write-Host ""
$open = Read-Host "Otkryt stranicu zagruzki? (y/n)"
if ($open -eq 'y' -or $open -eq 'Y') {
    Start-Process "https://www.python.org/downloads/"
}
Read-Host "Enter - vyhod"
