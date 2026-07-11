Write-Host "=== Reset Database ===" -ForegroundColor Yellow
if (Test-Path "data/bot.db") {
    Remove-Item "data/bot.db" -Force
    Write-Host "Database deleted: data/bot.db" -ForegroundColor Green
} else {
    Write-Host "No database found." -ForegroundColor Gray
}

if (Test-Path "data") {
    $files = Get-ChildItem "data" -Recurse -File
    if ($files.Count -eq 0) {
        Write-Host "Data directory is clean." -ForegroundColor Green
    }
}
