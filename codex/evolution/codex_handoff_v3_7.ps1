# ============================================================
# Codex v3.7 — Handoff Synchronization Point (HSP)
# Author: James Paul Jackson — Codex Project
# ============================================================

$root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Set-Location $root
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Write-Host "`n🔷 Initiating Codex v3.7 — Handoff Synchronization Point (HSP)`n" -ForegroundColor Cyan

# --- Paths ---
$handoffDir = "$root\codex\handoff"
$logsDir = "$root\codex\logs"
$evoDir = "$root\codex\evolution"
$coreDir = "$root\codex\core"
$outputFile = "$handoffDir\handoff_state_v3_7_$timestamp.json"
New-Item -ItemType Directory -Force -Path $handoffDir | Out-Null

# --- Collect data safely ---
$collect = @{}

function Safe-LoadJson($path) {
    if (Test-Path $path) {
        try { return (Get-Content $path -Raw | ConvertFrom-Json) }
        catch { return @{"error"="parse_failed";"file"=$path} }
    } else { return @{"error"="missing";"file"=$path} }
}

Write-Host "📥 Loading Codex state snapshots..."
$collect.registry  = Safe-LoadJson "$coreDir\registry.json"
$collect.harmonics = Safe-LoadJson "$coreDir\harmonics.json"

$collect.latest_logs = Get-ChildItem "$logsDir" -Recurse -Include *.json |
    Sort-Object LastWriteTime -Descending | Select-Object -First 10 |
    ForEach-Object { @{name=$_.Name; path=$_.FullName; modified=$_.LastWriteTimeUtc} }

$collect.latest_evolution = Get-ChildItem "$evoDir" -Include *.json |
    Sort-Object LastWriteTime -Descending | Select-Object -First 5 |
    ForEach-Object { @{name=$_.Name; path=$_.FullName; modified=$_.LastWriteTimeUtc} }

$collect.meta = @{
    version = "v3.7"
    codex_phase = "Handoff Synchronization Point"
    author = "James Paul Jackson"
    origin = $root
    timestamp = $timestamp
}

# --- Write unified JSON ---
$collect | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 $outputFile
Write-Host "📦 Handoff payload packaged:" -ForegroundColor Yellow
Write-Host "   $outputFile"

# --- Git Commit and Push ---
try {
    git add -A
    $commitMsg = "🪶 Codex v3.7 — Handoff Synchronization Point (HSP) | $timestamp"
    git commit -m $commitMsg 2>$null
    git push origin main 2>$null
    Write-Host "🌐 Handoff committed and pushed to GitHub main." -ForegroundColor Green
} catch {
    Write-Host "⚠️ Git operation failed: $_" -ForegroundColor Red
}

# --- Completion ---
Write-Host "`n✅ Codex v3.7 HSP complete." -ForegroundColor Cyan
Write-Host "   Manifest: $outputFile"
Write-Host "   Phase: HSP — ready for next AI continuity handoff."
Write-Host "`n🏁 Returned to Codex root: $root" -ForegroundColor Cyan

Set-Location $root
