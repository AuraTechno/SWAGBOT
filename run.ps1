param(
    [switch]$ResetDB
)

$ErrorActionPreference = "Stop"
Write-Host "=== SWAG VPN Bot ===" -ForegroundColor Cyan

if ($ResetDB) {
    Write-Host "Resetting database..." -ForegroundColor Yellow
    if (Test-Path "data/bot.db") {
        Remove-Item "data/bot.db" -Force
        Write-Host "Database deleted." -ForegroundColor Green
    }
}

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

$venvActivate = Join-Path (Get-Location) "venv\Scripts\Activate.ps1"
& $venvActivate

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Starting bot..." -ForegroundColor Green
python -m bot.main
