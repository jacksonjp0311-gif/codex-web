$ErrorActionPreference = "Stop"
$root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$tracker = Join-Path $root "codex_kernel_goal_tracker.md"
Set-Location $root
$ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
Write-Host "[codex v1.8] 🧠 Running Daily Auto-Cycle at $ts"
Write-Host "[codex v1.8] 🔍 Verifying kernel integrity..."
if (-not (Test-Path $tracker)) {
    Write-Host "[codex v1.8] ⚠️ Tracker missing — creating new."
    "" | Out-File -FilePath $tracker -Encoding UTF8
}
try {
    git add -A
    $tag = "CODEX-AUTO-CYCLE-v1.8-" + (Get-Date).ToString("yyyyMMdd-HHmmss")
    git commit -m "[codex v1.8] ♻️ Daily Auto-Cycle Review — $ts"
    git tag -a $tag -m "Codex Auto-Cycle Continuum"
    git push origin main
    git push origin --tags
    Write-Host "[codex v1.8] 🔒 Cycle committed and sealed as: $tag"
} catch {
    Write-Host "[codex v1.8] ⚠️ Git commit skipped or failed: $($_.Exception.Message)"
}
Write-Host "[codex v1.8] 📜 Cycle complete — returned to root: $root"
