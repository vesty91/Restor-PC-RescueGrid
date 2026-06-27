\
Write-Host "Verification avant push GitHub..." -ForegroundColor Cyan

$bad = @()
$patterns = @(".env", "backend\.env", "*.db", "*.sqlite", "storage", "backend\storage", "Intervention_*")

foreach ($p in $patterns) {
    $found = Get-ChildItem . -Recurse -Force -ErrorAction SilentlyContinue -Include $p
    foreach ($item in $found) {
        if ($item.FullName -notmatch "\.env\.example$" -and $item.FullName -notmatch "\.git") {
            $bad += $item.FullName
        }
    }
}

if ($bad.Count -gt 0) {
    Write-Host "Elements sensibles detectes :" -ForegroundColor Red
    $bad | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    exit 1
}

Write-Host "OK : aucun fichier sensible evident detecte." -ForegroundColor Green
